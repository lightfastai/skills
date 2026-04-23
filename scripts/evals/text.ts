export function normalizeLine(line) {
  return line.trim().replace(/\s+/g, " ");
}

export function normalizeHeading(line) {
  return normalizeLine(line)
    .replace(/^#+\s*/, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function stripLeadingSectionNumber(heading) {
  return heading.replace(/^\d+(?:\.\d+)*\.?\s+/, "").trim();
}

export function hasPronounDrift(document) {
  return /\b(we|our|ours|us|you|your|yours)\b/i.test(document);
}

export function hasUppercaseObligationKeyword(document) {
  return /\b(MUST|SHOULD|MAY)\b/.test(document);
}

export function extractNonEmptyNormalizedLines(text) {
  return text
    .split(/\r?\n/)
    .map((line) => normalizeLine(line))
    .filter((line) => line.length > 0);
}

export function linesAppearInOrder(needleLines, haystackLines) {
  let needleIndex = 0;

  for (const line of haystackLines) {
    if (needleIndex >= needleLines.length) {
      break;
    }
    if (line === needleLines[needleIndex]) {
      needleIndex += 1;
    }
  }

  return needleIndex === needleLines.length;
}
