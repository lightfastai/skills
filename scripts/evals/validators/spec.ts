import {
  hasPronounDrift,
  hasUppercaseObligationKeyword,
  linesAppearInOrder,
  normalizeHeading,
  normalizeLine,
  stripLeadingSectionNumber,
} from "../text.ts";
import {
  createCheck,
  createPatternChecks,
  createPreservedSectionChecks,
  extractNormalizedMarkdownBlocks,
  filterLinesByPatternSpecs,
  removeReplaceableSectionContent,
} from "./markdown.ts";

function extractSpecMajorSections(templateText) {
  const sections = [];
  const lines = templateText.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    const match = line.match(/^## \d+\.\s+(.+)$/);
    if (match) {
      sections.push(match[1]);
    }
  }

  return sections;
}

function extractSpecSubsections(templateText) {
  const sections = [];
  const lines = templateText.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    const match = line.match(/^### \d+\.\d+\s+(.+)$/);
    if (match) {
      sections.push(match[1]);
    }
  }

  return sections;
}

function lineExists(lines, matcher) {
  return lines.some((line) => matcher(normalizeHeading(line)));
}

export function validateSpecDocument(candidateDocument, templateText) {
  const requiredSections = extractSpecMajorSections(templateText);
  const requiredSubsections = extractSpecSubsections(templateText);
  const lines = candidateDocument.split(/\r?\n/);
  const missingSections = requiredSections.filter(
    (section) =>
      !lineExists(
        lines,
        (line) => stripLeadingSectionNumber(line).toLowerCase() === section.toLowerCase(),
      ),
  );
  const missingSubsections = requiredSubsections.filter(
    (section) =>
      !lineExists(
        lines,
        (line) => stripLeadingSectionNumber(line).toLowerCase() === section.toLowerCase(),
      ),
  );

  const hasStatusLine = lines.some((line) => /^\s*Status:\s+\S+/.test(line));
  const hasPurposeLine = lines.some((line) => /^\s*Purpose:\s+\S+/.test(line));
  const hasProblemStatement = lineExists(lines, (line) => line === "1. Problem Statement");
  const hasGoalSubsections =
    lineExists(lines, (line) => line === "2.1 Goals") &&
    lineExists(lines, (line) => line === "2.2 Non-Goals");
  const hasImportantBoundaryBlock =
    /(^|\n)\s*(?:\*\*)?Important boundary:(?:\*\*)?\s*(?:\n|$)/m.test(candidateDocument);
  const hasNumberedComponents = /^\d+\.\s+`[^`]+`/m.test(candidateDocument);
  const hasFieldFormatting = /- `[^`]+` \([^)]+\)/.test(candidateDocument);
  const hasEntityDefinitions = /^####\s+4\.1\.\d+\s+/m.test(candidateDocument);
  const declaresNoDurableEntities =
    !hasEntityDefinitions &&
    /\b(?:does not (?:introduce|define|create)|no)\b[^.\n]*(?:durable|service-owned|service-specific|first-class)[^.\n]*entities\b/i.test(
      candidateDocument,
    );
  const domainModelShapeAcceptable = hasFieldFormatting || declaresNoDurableEntities;
  const fieldLinesAvoidRequirementKeywords =
    !/- `[^`]+` \([^)]*\b(required|optional)\b[^)]*\)/i.test(candidateDocument);

  return [
    createCheck(
      "core_sections_present",
      missingSections.length === 0,
      missingSections.length === 0
        ? `All major template sections are present: ${requiredSections.join(", ")}.`
        : `Missing major sections: ${missingSections.join(", ")}.`,
    ),
    createCheck(
      "required_subsections_present",
      missingSubsections.length === 0,
      missingSubsections.length === 0
        ? `All template subsections are present: ${requiredSubsections.join(", ")}.`
        : `Missing template subsections: ${missingSubsections.join(", ")}.`,
    ),
    createCheck(
      "status_line_present",
      hasStatusLine,
      hasStatusLine
        ? "Status line is present."
        : "Status line is missing or malformed.",
    ),
    createCheck(
      "purpose_line_present",
      hasPurposeLine,
      hasPurposeLine
        ? "Purpose line is present."
        : "Purpose line is missing or malformed.",
    ),
    createCheck(
      "problem_statement_present",
      hasProblemStatement,
      hasProblemStatement
        ? "Problem Statement major section is present."
        : "Problem Statement major section is missing.",
    ),
    createCheck(
      "goals_subsections_present",
      hasGoalSubsections,
      hasGoalSubsections
        ? "Detected `2.1 Goals` and `2.2 Non-Goals` subsections."
        : "Missing one or both of the required goals subsections: `2.1 Goals`, `2.2 Non-Goals`.",
    ),
    createCheck(
      "important_boundary_block_present",
      hasImportantBoundaryBlock,
      hasImportantBoundaryBlock
        ? "Detected an `Important boundary:` block inside the document."
        : "Did not detect the required `Important boundary:` block.",
    ),
    createCheck(
      "component_list_uses_numbering",
      hasNumberedComponents,
      hasNumberedComponents
        ? "Detected numbered component entries in the spec."
        : "Did not detect numbered component entries like `1. `Component Name``.",
    ),
    createCheck(
      "domain_fields_use_template_shape",
      domainModelShapeAcceptable,
      hasFieldFormatting
        ? "Detected domain-field lines using the `` `field_name` (type) `` format."
        : declaresNoDurableEntities
          ? "The spec explicitly declares that the service does not introduce durable service-owned entities."
          : "Did not detect any domain-field lines using the template field format.",
    ),
    createCheck(
      "field_parens_avoid_requirement_keywords",
      fieldLinesAvoidRequirementKeywords,
      fieldLinesAvoidRequirementKeywords
        ? "Field type parentheses avoid `required`/`optional` labels."
        : "Detected `required` or `optional` inside field type parentheses; keep those details in the description bullets instead.",
    ),
    createCheck(
      "no_first_or_second_person",
      !hasPronounDrift(candidateDocument),
      !hasPronounDrift(candidateDocument)
        ? "No obvious first-person or second-person pronouns detected."
        : "Detected first-person or second-person pronouns that violate the language guide.",
    ),
    createCheck(
      "obligation_keywords_lowercase",
      !hasUppercaseObligationKeyword(candidateDocument),
      !hasUppercaseObligationKeyword(candidateDocument)
        ? "No uppercase obligation keywords detected."
        : "Detected uppercase MUST/SHOULD/MAY, which violates the language guide.",
    ),
  ];
}

export function validateSpecUpdateDocument(candidateDocument, existingSpecText, validationContract) {
  const filteredExistingSpecText = removeReplaceableSectionContent(
    existingSpecText,
    validationContract.replaceable_sections ?? [],
  );
  const existingBlocks = extractNormalizedMarkdownBlocks(filteredExistingSpecText);
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
  const preservedSectionChecks = createPreservedSectionChecks(
    existingSpecText,
    candidateDocument,
    validationContract.preserve_sections ?? [],
  );

  return [
    createCheck(
      "existing_content_preserved_in_order",
      preservesExistingContent,
      preservesExistingContent
        ? "All existing markdown blocks appear in order in the candidate, except blocks explicitly marked as replaceable."
        : "One or more existing markdown blocks were removed or reordered outside the explicitly replaceable blocks.",
    ),
    ...requiredPatternChecks,
    ...forbiddenPatternChecks,
    ...preservedSectionChecks,
    createCheck(
      "no_first_or_second_person",
      !hasPronounDrift(candidateDocument),
      !hasPronounDrift(candidateDocument)
        ? "No obvious first-person or second-person pronouns detected."
        : "Detected first-person or second-person pronouns that violate the language guide.",
    ),
    createCheck(
      "obligation_keywords_lowercase",
      !hasUppercaseObligationKeyword(candidateDocument),
      !hasUppercaseObligationKeyword(candidateDocument)
        ? "No uppercase obligation keywords detected."
        : "Detected uppercase MUST/SHOULD/MAY, which violates the language guide.",
    ),
  ];
}
