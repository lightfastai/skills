import {
  normalizeHeading,
  normalizeLine,
  stripLeadingSectionNumber,
} from "../text.ts";

export function createCheck(id, passed, details) {
  return { id, passed, details };
}

export function compilePatternSpec(patternSpec) {
  if (typeof patternSpec === "string") {
    return new RegExp(patternSpec, "i");
  }

  return new RegExp(patternSpec.pattern, patternSpec.flags ?? "i");
}

export function filterLinesByPatternSpecs(lines, patternSpecs = []) {
  if (patternSpecs.length === 0) {
    return lines;
  }

  return lines.filter((line) =>
    !patternSpecs.some((patternSpec) => compilePatternSpec(patternSpec).test(line)),
  );
}

export function normalizeComparableHeading(value) {
  return stripLeadingSectionNumber(normalizeHeading(value));
}

export function extractMarkdownHeadingEntries(document) {
  const lines = document.split(/\r?\n/);
  const headings = [];

  for (const [index, rawLine] of lines.entries()) {
    const match = rawLine.match(/^\s*(#{1,6})\s+(.+?)\s*$/);
    if (!match) {
      continue;
    }

    headings.push({
      index,
      level: match[1].length,
      title: normalizeLine(match[2]),
      normalizedTitle: normalizeComparableHeading(match[2]),
    });
  }

  return {
    lines,
    headings,
  };
}

export function removeReplaceableSectionContent(document, replaceableSections = []) {
  if (replaceableSections.length === 0) {
    return document;
  }

  const normalizedSpecs = replaceableSections
    .map((sectionSpec) =>
      typeof sectionSpec === "string"
        ? {
            title: sectionSpec,
          }
        : sectionSpec,
    )
    .filter((sectionSpec) => typeof sectionSpec?.title === "string")
    .map((sectionSpec) => ({
      normalizedTitle: normalizeComparableHeading(sectionSpec.title),
      level: Number.isInteger(sectionSpec.level) ? sectionSpec.level : null,
      removeHeading: sectionSpec.remove_heading === true,
    }));

  if (normalizedSpecs.length === 0) {
    return document;
  }

  const { lines, headings } = extractMarkdownHeadingEntries(document);
  const skippedLineIndexes = new Set();

  for (let headingIndex = 0; headingIndex < headings.length; headingIndex += 1) {
    const heading = headings[headingIndex];
    const matchingSpec = normalizedSpecs.find((sectionSpec) => {
      if (sectionSpec.normalizedTitle !== heading.normalizedTitle) {
        return false;
      }

      if (sectionSpec.level !== null && sectionSpec.level !== heading.level) {
        return false;
      }

      return true;
    });

    if (!matchingSpec) {
      continue;
    }

    let end = lines.length;
    for (let nextIndex = headingIndex + 1; nextIndex < headings.length; nextIndex += 1) {
      if (headings[nextIndex].level <= heading.level) {
        end = headings[nextIndex].index;
        break;
      }
    }

    const start = matchingSpec.removeHeading ? heading.index : heading.index + 1;
    for (let lineIndex = start; lineIndex < end; lineIndex += 1) {
      skippedLineIndexes.add(lineIndex);
    }
  }

  return lines.filter((_, index) => !skippedLineIndexes.has(index)).join("\n");
}

export function findSectionBody(sectionMap, targetTitle) {
  const normalizedTarget = stripLeadingSectionNumber(normalizeHeading(targetTitle));

  for (const [title, body] of sectionMap.entries()) {
    if (stripLeadingSectionNumber(normalizeHeading(title)) === normalizedTarget) {
      return body ?? "";
    }
  }

  return null;
}

export function extractMarkdownSectionBodies(candidateDocument) {
  const { lines, headings } = extractMarkdownHeadingEntries(candidateDocument);
  const sections = headings.map((heading) => ({
    title: heading.title,
    index: heading.index,
    level: heading.level,
  }));
  const bodies = new Map();

  for (let index = 0; index < sections.length; index += 1) {
    const current = sections[index];
    let end = lines.length;

    for (let nextIndex = index + 1; nextIndex < sections.length; nextIndex += 1) {
      if (sections[nextIndex].level <= current.level) {
        end = sections[nextIndex].index;
        break;
      }
    }

    const start = current.index + 1;
    bodies.set(current.title, lines.slice(start, end).join("\n").trim());
  }

  return {
    lines,
    sections,
    bodies,
  };
}

export function createPatternChecks(candidateDocument, patternChecks = [], expectedPresence = true) {
  const normalizedCandidate = normalizeLine(candidateDocument);
  const sectionBodies = extractMarkdownSectionBodies(candidateDocument).bodies;

  return patternChecks.map((patternCheck) => {
    const expression = compilePatternSpec(patternCheck);
    const scopedText = patternCheck.section_title
      ? findSectionBody(sectionBodies, patternCheck.section_title)
      : candidateDocument;
    const normalizedScopedText =
      typeof scopedText === "string" ? normalizeLine(scopedText) : "";
    const matched = expression.test(
      patternCheck.section_title ? normalizedScopedText : normalizedCandidate,
    );
    const passed = expectedPresence ? matched : !matched;

    return createCheck(
      patternCheck.id,
      passed,
      passed ? patternCheck.details_pass : patternCheck.details_fail,
    );
  });
}

export function createPreservedSectionChecks(
  existingDocument,
  candidateDocument,
  preservedSections = [],
) {
  if (preservedSections.length === 0) {
    return [];
  }

  const existingSections = extractMarkdownSectionBodies(existingDocument).bodies;
  const candidateSections = extractMarkdownSectionBodies(candidateDocument).bodies;

  return preservedSections.map((sectionCheck) => {
    const existingBody = findSectionBody(existingSections, sectionCheck.title);
    const candidateBody = findSectionBody(candidateSections, sectionCheck.title);
    const passed =
      existingBody !== null &&
      candidateBody !== null &&
      normalizeLine(existingBody) === normalizeLine(candidateBody);

    return createCheck(
      sectionCheck.id,
      passed,
      passed ? sectionCheck.details_pass : sectionCheck.details_fail,
    );
  });
}

export function extractMarkdownBullets(sectionBody) {
  const bullets = [];
  let current = null;

  for (const rawLine of sectionBody.split(/\r?\n/)) {
    if (/^\s*-\s+/.test(rawLine)) {
      if (current) {
        bullets.push(current);
      }
      current = normalizeLine(rawLine.replace(/^\s*-\s+/, ""));
      continue;
    }

    const line = normalizeLine(rawLine);
    if (!current || line.length === 0) {
      continue;
    }

    current = `${current} ${line}`.trim();
  }

  if (current) {
    bullets.push(current);
  }

  return bullets;
}

export function extractNormalizedMarkdownBlocks(text) {
  const blocks = [];
  let current = null;

  function flush() {
    if (current && normalizeLine(current).length > 0) {
      blocks.push(normalizeLine(current));
    }
    current = null;
  }

  for (const rawLine of text.split(/\r?\n/)) {
    const trimmed = rawLine.trim();

    if (trimmed.length === 0) {
      flush();
      continue;
    }

    if (/^\s*#+\s+/.test(rawLine)) {
      flush();
      blocks.push(normalizeLine(rawLine));
      continue;
    }

    if (/^\s*-\s+/.test(rawLine)) {
      flush();
      current = rawLine.replace(/^\s*-\s+/, "- ");
      continue;
    }

    if (current) {
      current = `${current} ${trimmed}`.trim();
      continue;
    }

    current = trimmed;
  }

  flush();
  return blocks;
}
