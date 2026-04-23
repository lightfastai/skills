import path from "node:path";
import { fail, loadText } from "../runtime.ts";
import {
  validateFoundationDocument,
  validateFoundationUpdateDocument,
} from "./foundation.ts";
import {
  validateSpecDocument,
  validateSpecUpdateDocument,
} from "./spec.ts";

export async function runDeterministicChecks(
  skillRoot,
  validationContract,
  candidateDocument,
  packet = null,
) {
  if (!validationContract || validationContract.type !== "reference_document_checks") {
    return {
      enabled: false,
      overall_pass: true,
      checks: [],
    };
  }

  const templatePath = validationContract.template_file
    ? path.join(skillRoot, validationContract.template_file)
    : null;
  const languagePath = validationContract.language_file
    ? path.join(skillRoot, validationContract.language_file)
    : null;
  const existingSpecPath = validationContract.existing_spec_file
    ? path.join(skillRoot, validationContract.existing_spec_file)
    : null;
  const existingFoundationPath = validationContract.existing_foundation_file
    ? path.join(skillRoot, validationContract.existing_foundation_file)
    : null;
  const [templateText, languageText, existingSpecText, existingFoundationText] = await Promise.all([
    validationContract.template_file ? loadText(templatePath) : Promise.resolve(""),
    languagePath ? loadText(languagePath) : Promise.resolve(""),
    existingSpecPath ? loadText(existingSpecPath) : Promise.resolve(""),
    existingFoundationPath ? loadText(existingFoundationPath) : Promise.resolve(""),
  ]);

  let checks;
  switch (validationContract.validator) {
    case "foundation-v1":
      checks = validateFoundationDocument(candidateDocument, templateText, languageText, packet);
      break;
    case "foundation-update-v1":
      checks = validateFoundationUpdateDocument(
        candidateDocument,
        existingFoundationText,
        templateText,
        validationContract,
        packet,
      );
      break;
    case "spec-v1":
      checks = validateSpecDocument(candidateDocument, templateText, languageText);
      break;
    case "spec-update-v1":
      checks = validateSpecUpdateDocument(candidateDocument, existingSpecText, validationContract);
      break;
    default:
      fail(`Unknown validation contract '${validationContract.validator}'.`);
  }

  return {
    enabled: true,
    validator: validationContract.validator,
    overall_pass: checks.every((check) => check.passed),
    checks,
  };
}
