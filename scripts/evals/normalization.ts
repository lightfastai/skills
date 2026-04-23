function normalizeMatchText(value) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/[`"'’]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

const COMPARABLE_STOP_WORDS = new Set([
  "the",
  "and",
  "for",
  "with",
  "that",
  "this",
  "from",
  "into",
  "through",
  "within",
  "under",
  "over",
  "while",
  "where",
  "when",
  "than",
  "then",
  "only",
  "just",
  "more",
  "less",
  "same",
  "does",
  "doesnt",
  "not",
  "are",
  "is",
  "was",
  "were",
  "be",
  "being",
  "been",
  "can",
  "could",
  "should",
  "would",
  "will",
  "may",
  "might",
  "must",
  "have",
  "has",
  "had",
  "its",
  "their",
  "them",
  "they",
  "there",
  "about",
  "across",
  "around",
  "also",
  "still",
  "rather",
  "than",
  "such",
  "those",
  "these",
  "service",
  "packet",
  "source",
  "record",
  "records",
  "surface",
  "surfaces",
  "entity",
  "entities",
  "concept",
  "concepts",
  "label",
  "labels",
  "term",
  "terms",
  "context",
]);

function extractComparableWords(value) {
  return new Set(
    normalizeMatchText(value)
      .split(" ")
      .map((word) => word.trim())
      .filter((word) => word.length >= 3 && !COMPARABLE_STOP_WORDS.has(word)),
  );
}

function countWordOverlap(leftWords, rightWords) {
  let overlap = 0;
  for (const word of leftWords) {
    if (rightWords.has(word)) {
      overlap += 1;
    }
  }
  return overlap;
}

function normalizeFieldName(value) {
  return normalizeMatchText(value).replace(/\s+/g, "_");
}

const GENERIC_IDENTITY_FIELDS = new Set([
  "id",
  "name",
  "slug",
  "title",
  "key",
  "code",
  "identifier",
  "external_id",
  "display_name",
]);

function entityUsesOnlyGenericIdentityFields(entity) {
  const fields = Array.isArray(entity?.fields) ? entity.fields : [];

  if (fields.length > 2) {
    return false;
  }

  return fields.every((field) => GENERIC_IDENTITY_FIELDS.has(normalizeFieldName(field?.name)));
}

function collectSpecBriefContextTexts(brief, packet) {
  return [
    brief?.purpose,
    ...(brief?.operational_problems ?? []),
    ...(brief?.goals ?? []),
    ...(brief?.non_goals ?? []),
    ...(brief?.important_boundaries ?? []),
    ...(brief?.external_dependencies ?? []),
    ...(brief?.unresolved_questions ?? []),
    packet?.raw_notes,
    packet?.expected_criteria,
  ].filter((value) => typeof value === "string" && value.trim().length > 0);
}

const ENTITY_ALIAS_AMBIGUITY_MARKERS = [
  /\bdoes not resolve\b/i,
  /\bpreferred term\b/i,
  /\bsame underlying concept\b/i,
  /\bsame service surface\b/i,
  /\bdistinct surface\b/i,
  /\bdistinct surfaces\b/i,
  /\bdistinct concept\b/i,
  /\bdistinct concepts\b/i,
  /\bseparate concept\b/i,
  /\bseparate concepts\b/i,
  /\balias\b/i,
  /\bversus\b/i,
  /\bvs\.?\b/i,
  /\bdo not collapse\b/i,
  /\breferring to the same\b/i,
];

function textHasAliasAmbiguityMarker(text) {
  return (
    ENTITY_ALIAS_AMBIGUITY_MARKERS.some((pattern) => pattern.test(text)) ||
    /\bteams?\b.*\bworkspace\b/i.test(text) ||
    /\bworkspace\b.*\bteams?\b/i.test(text)
  );
}

function findAmbiguousAliasEntityDecision(entity, brief, packet) {
  if (!entityUsesOnlyGenericIdentityFields(entity)) {
    return null;
  }

  const entityText = normalizeMatchText(
    [
      entity?.name,
      entity?.description,
      ...(entity?.fields ?? []).flatMap((field) => [field?.name, field?.description]),
    ].join(" "),
  );

  if (!textHasAliasAmbiguityMarker(entityText)) {
    return null;
  }

  const entityWords = extractComparableWords(entityText);
  if (entityWords.size === 0) {
    return null;
  }

  const matchingContext = collectSpecBriefContextTexts(brief, packet).find((contextText) => {
    const normalizedContext = normalizeMatchText(contextText);
    if (!textHasAliasAmbiguityMarker(normalizedContext)) {
      return false;
    }

    return countWordOverlap(entityWords, extractComparableWords(normalizedContext)) >= 2;
  });

  if (!matchingContext) {
    return null;
  }

  return {
    entity_name: entity?.name ?? "Unnamed entity",
    reason:
      "Removed minimal entity because it models an explicitly ambiguous alias surface that the brief and packet keep unresolved.",
    evidence: matchingContext,
  };
}

function cloneEvalBrief(brief) {
  // Generated BAML objects may be class instances that Bun cannot structuredClone.
  // The runner only needs JSON-shaped data for normalization and rendering.
  return JSON.parse(JSON.stringify(brief));
}

export function normalizeCompiledBriefForRender({ skillName, packetType, brief, packet }) {
  if (skillName !== "spec-creator" || packetType !== "SpecEvalPacket") {
    return {
      brief,
      normalization: {
        applied: false,
        removed_entities: [],
      },
    };
  }

  const normalizedBrief = cloneEvalBrief(brief);
  const removedEntities = [];

  normalizedBrief.entities = (normalizedBrief.entities ?? []).filter((entity) => {
    const decision = findAmbiguousAliasEntityDecision(entity, normalizedBrief, packet);
    if (!decision) {
      return true;
    }

    removedEntities.push(decision);
    return false;
  });

  return {
    brief: normalizedBrief,
    normalization: {
      applied: true,
      removed_entities: removedEntities,
    },
  };
}
