import {
  hasPronounDrift,
  linesAppearInOrder,
  normalizeLine,
} from "../text.ts";
import {
  createCheck,
  createPatternChecks,
  extractMarkdownBullets,
  extractMarkdownSectionBodies,
  extractNormalizedMarkdownBlocks,
  filterLinesByPatternSpecs,
  removeReplaceableSectionContent,
} from "./markdown.ts";

function extractFoundationTemplateSections(templateText) {
  const sections = [];
  const lines = templateText.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    if (line === "## Disallowed Sections") {
      break;
    }
    if (line.startsWith("## ")) {
      sections.push(line.slice(3).trim());
    }
  }

  return sections;
}

function extractFoundationDisallowedHeadings(templateText) {
  const disallowed = new Set();
  const lines = templateText.split(/\r?\n/);
  let inDisallowedSection = false;

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    if (line === "## Disallowed Sections") {
      inDisallowedSection = true;
      continue;
    }
    if (!inDisallowedSection) {
      continue;
    }
    const match = line.match(/^- `(.+)`$/);
    if (match) {
      disallowed.add(match[1]);
    }
  }

  return disallowed;
}

function packetAllowsPublicMaterialsLead(packet) {
  if (!packet || typeof packet.raw_notes !== "string") {
    return true;
  }

  return (
    /\bURL:\b/i.test(packet.raw_notes) ||
    /\b##\s+Source\s+\d+/i.test(packet.raw_notes) ||
    /\bofficial\b.*\bsources?\b/i.test(packet.raw_notes) ||
    /\bpress release\b/i.test(packet.raw_notes) ||
    /\bdocs homepage\b/i.test(packet.raw_notes) ||
    /\bLast updated:\b/i.test(packet.raw_notes) ||
    /\bPublished:\b/i.test(packet.raw_notes)
  );
}

function strategicBetUsesApprovedLead(line, { allowPublicMaterialsLead = true } = {}) {
  const publicLeadPattern = allowPublicMaterialsLead
    ? "|Public materials (?:suggest|indicate|emphasize)(?:\\s+a bet on|\\s+that)?"
    : "";

  return new RegExp(
    `^(The notes suggest(?:\\s+a bet on|\\s+that)?|There are visible signals that${publicLeadPattern}|The source material (?:indicates|emphasizes)(?:\\s+a bet on|\\s+that)?)`,
    "i",
  ).test(line);
}

function strategicBetUsesDisallowedLanguage(line) {
  const normalized = normalizeLine(line).toLowerCase();

  return (
    normalized.includes("the company appears to be betting on") ||
    /\bprioriti(?:ze|zes|zed|zing)\b/.test(normalized) ||
    /\binvest(?:s|ed|ing)? in\b/.test(normalized) ||
    /\bship(?:s|ped|ping)?\b/.test(normalized) ||
    /\btreat(?:s|ed|ing)?\b.*\bfirst-class\b/.test(normalized) ||
    normalized.includes("first-class") ||
    normalized.includes("is the wedge") ||
    normalized.includes("is a defensible primitive") ||
    normalized.includes("will remain") ||
    normalized.includes("matters more than")
  );
}

export function validateFoundationDocument(candidateDocument, templateText, _languageText, packet) {
  const requiredSections = extractFoundationTemplateSections(templateText);
  const disallowedHeadings = extractFoundationDisallowedHeadings(templateText);
  const { lines, sections, bodies } = extractMarkdownSectionBodies(candidateDocument);
  const titleLine = lines.find((line) => normalizeLine(line).length > 0) ?? "";
  const hasMarkdownTitle = /^\s*#\s+.+\s+Foundation\s*$/.test(titleLine);
  const lineMap = new Map();

  for (const { title, index } of sections) {
    const line = normalizeLine(title);
    if (!lineMap.has(line)) {
      lineMap.set(line, []);
    }
    lineMap.get(line).push(index);
  }

  const missingSections = [];
  const duplicateSections = [];
  const positions = [];

  for (const section of requiredSections) {
    const matches = lineMap.get(section) ?? [];
    if (matches.length === 0) {
      missingSections.push(section);
      continue;
    }
    if (matches.length > 1) {
      duplicateSections.push(section);
    }
    positions.push({
      section,
      index: matches[0],
    });
  }

  const orderIsCorrect = positions.every((entry, index) => {
    if (index === 0) {
      return true;
    }
    return entry.index > positions[index - 1].index;
  });

  const emptySections = [];
  for (let index = 0; index < positions.length; index += 1) {
    const current = positions[index];
    const sectionBody = bodies.get(current.section) ?? "";
    if (!sectionBody) {
      emptySections.push(current.section);
    }
  }

  const presentDisallowedSections = [...disallowedHeadings].filter((section) =>
    (lineMap.get(section) ?? []).length > 0,
  );
  const strategicBetsBody = bodies.get("Strategic Bets") ?? "";
  const openQuestionsBody = bodies.get("Open Questions") ?? "";
  const openQuestionBullets = extractMarkdownBullets(openQuestionsBody);
  const allowPublicMaterialsLead = packetAllowsPublicMaterialsLead(packet);
  const openQuestionsLookOpen =
    openQuestionBullets.length > 0 &&
    openQuestionBullets.every((line) => line.endsWith("?"));
  const strategicBetLines = extractMarkdownBullets(strategicBetsBody);
  const strategicBetsUseBullets =
    strategicBetsBody.trim().length === 0 || strategicBetLines.length > 0;
  const hedgedStrategicBets =
    strategicBetLines.length > 0 &&
    strategicBetLines.every((line) =>
      strategicBetUsesApprovedLead(line, { allowPublicMaterialsLead }),
    );
  const strategicBetsAvoidPrescriptiveOrCompanyPosture =
    strategicBetLines.length === 0 ||
    strategicBetLines.every((line) => !strategicBetUsesDisallowedLanguage(line));

  return [
    createCheck(
      "title_heading_present",
      hasMarkdownTitle,
      hasMarkdownTitle
        ? "Detected the required markdown title heading."
        : "Missing required title heading like `# <Primitive Name> Foundation`.",
    ),
    createCheck(
      "required_sections_present_once",
      missingSections.length === 0 && duplicateSections.length === 0,
      missingSections.length === 0 && duplicateSections.length === 0
        ? `All required sections from template are present exactly once: ${requiredSections.join(", ")}.`
        : `Missing: ${missingSections.join(", ") || "none"}. Duplicate: ${duplicateSections.join(", ") || "none"}.`,
    ),
    createCheck(
      "required_sections_in_template_order",
      missingSections.length === 0 && orderIsCorrect,
      missingSections.length > 0
        ? "Section order check skipped because one or more required sections are missing."
        : orderIsCorrect
          ? "Required sections follow the template order."
          : "Required sections are present but not in template order.",
    ),
    createCheck(
      "required_sections_nonempty",
      emptySections.length === 0,
      emptySections.length === 0
        ? "Every required section has non-empty content."
        : `Empty sections: ${emptySections.join(", ")}.`,
    ),
    createCheck(
      "no_disallowed_sections",
      presentDisallowedSections.length === 0,
      presentDisallowedSections.length === 0
        ? "No disallowed downstream-planning sections were detected."
        : `Disallowed sections present: ${presentDisallowedSections.join(", ")}.`,
    ),
    createCheck(
      "strategic_bets_use_markdown_bullets",
      strategicBetsUseBullets,
      strategicBetsUseBullets
        ? "Strategic Bets use markdown bullets."
        : "Strategic Bets should be rendered as markdown bullets using `- `, not as paragraph-only prose.",
    ),
    createCheck(
      "strategic_bets_use_directional_language",
      hedgedStrategicBets,
      hedgedStrategicBets
        ? "Strategic Bets use approved source-centered lead phrasing."
        : allowPublicMaterialsLead
          ? "One or more Strategic Bets bullets do not begin with approved source-centered phrasing such as `The notes suggest...`, `There are visible signals that...`, `Public materials suggest...`, `Public materials indicate...`, `The source material indicates...`, or `The source material emphasizes...`."
          : "One or more Strategic Bets bullets use evidence-source phrasing that does not match a notes-only packet. In note-only packets, use `The notes suggest...`, `There are visible signals that...`, `The source material indicates...`, or `The source material emphasizes...`.",
    ),
    createCheck(
      "strategic_bets_avoid_prescriptive_or_company_intent_language",
      strategicBetsAvoidPrescriptiveOrCompanyPosture,
      strategicBetsAvoidPrescriptiveOrCompanyPosture
        ? "Strategic Bets avoid prescriptive verbs and direct company-intent phrasing."
        : "One or more Strategic Bets bullets use prescriptive verbs, categorical phrasing, or direct company-intent language.",
    ),
    createCheck(
      "open_questions_remain_questions",
      openQuestionsLookOpen,
      openQuestionsLookOpen
        ? "Open Questions are written as explicit unanswered questions."
        : "Open Questions should be bullet questions that remain open and usually end with `?`.",
    ),
    createCheck(
      "no_first_or_second_person",
      !hasPronounDrift(candidateDocument),
      !hasPronounDrift(candidateDocument)
        ? "No obvious first-person or second-person pronouns detected."
        : "Detected first-person or second-person pronouns that violate the language guide.",
    ),
  ];
}

export function validateFoundationUpdateDocument(
  candidateDocument,
  existingFoundationText,
  templateText,
  validationContract,
  packet,
) {
  const baseChecks = validateFoundationDocument(candidateDocument, templateText, "", packet);
  const filteredExistingFoundationText = removeReplaceableSectionContent(
    existingFoundationText,
    validationContract.replaceable_sections ?? [],
  );
  const existingBlocks = extractNormalizedMarkdownBlocks(filteredExistingFoundationText);
  const candidateBlocks = extractNormalizedMarkdownBlocks(candidateDocument);
  const preservedExistingBlocks = filterLinesByPatternSpecs(
    existingBlocks,
    validationContract.allowed_removed_patterns ?? [],
  );
  const preservesExistingContent = linesAppearInOrder(preservedExistingBlocks, candidateBlocks);
  const requiredPatternChecks = createPatternChecks(
    candidateDocument,
    validationContract.required_patterns ?? [],
    true,
  );
  const forbiddenPatternChecks = createPatternChecks(
    candidateDocument,
    validationContract.forbidden_patterns ?? [],
    false,
  );

  return [
    ...baseChecks,
    createCheck(
      "existing_content_preserved_in_order",
      preservesExistingContent,
      preservesExistingContent
        ? "All existing markdown blocks appear in order in the candidate, except blocks explicitly marked as replaceable."
        : "One or more existing markdown blocks were removed or reordered outside the explicitly replaceable blocks.",
    ),
    ...requiredPatternChecks,
    ...forbiddenPatternChecks,
  ];
}
