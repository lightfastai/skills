# Harbor Care Coordination Service Specification
Status: Draft v1 (language-agnostic)
Purpose: A long-running care-coordination service that turns referrals, intake notes, discharge instructions, documents, and follow-up events into a shared case timeline, coordination task queue, handoff tracker, and cautious benefits-question surface across family caregivers, patients, advocates, providers, pharmacies, and payers.

## 1. Problem Statement

Harbor Care Coordination Service keeps care logistics from dissolving into scattered calls, documents, and callbacks. It gives families, advocates, providers, pharmacies, payers, and other care contacts one visible coordination picture instead of forcing families to assemble the current state on their own.

The service solves 5 operational problems:
- Families often become the default project managers for eldercare and chronic-care logistics.
- Referrals, intake notes, discharge paperwork, pharmacy issues, benefits questions, and follow-up events live in different places.
- There is no shared operating picture of what happened, what is pending, and who owns the next step.
- Handoffs across organizations and settings can stall when responsibility is implicit.
- Conflicting records need to be surfaced without pretending the service can make a clinical conclusion.

Important boundary:
- Human advocates remain central when situations are ambiguous, sensitive, or clinically interpretive.
- The service stays focused on coordination logistics rather than diagnosis, treatment planning, or telehealth.
- The service is not an EHR, insurer claims processor, or marketplace for clinicians or home aides.
- Benefits questions may be tracked, but the service does not adjudicate claims or eligibility.
- The service should not turn into a generic outbound CRM.

## 2. Goals and Non-Goals

### 2.1 Goals
- Normalize referrals, intake notes, and related care inputs into one coordinated case.
- Maintain a shared case timeline showing what happened, what is pending, and what still needs documents or callbacks.
- Keep next-step ownership visible across family caregivers, advocates, providers, pharmacies, payers, and other care contacts.
- Track handoffs so care transitions do not disappear between settings or organizations.
- Keep a cautious surface for benefits or eligibility questions without becoming an adjudication engine.

### 2.2 Non-Goals
- Diagnosis or treatment planning.
- Telehealth.
- An EHR or EHR replacement.
- Insurer claims processing or adjudication.
- A marketplace for clinicians or home aides.
- A generic outbound CRM.

## 3. System Overview

Harbor Care Coordination Service is organized around messy intake, shared coordination state, explicit ownership, and visible handoffs. It keeps the case current without claiming clinical authority.

### 3.1 Main Components
1. `Referral and Intake Normalization`
   - Converts referral forms, intake call notes, discharge paperwork, and related inputs into a consistent care case.
   - Preserves original context while extracting coordination-relevant work.

2. `Shared Case Timeline`
   - Maintains the visible record of what happened, what is pending, and what still needs documents or callbacks.
   - Provides the main shared coordination surface for the care case.

3. `Coordination Task Queue`
   - Tracks next actions that still need attention.
   - Shows who owns the next step when ownership is known.

4. `Handoff Tracker`
   - Tracks transitions such as hospital to home, clinic to rehab, pharmacy to family, and payer to advocate.
   - Makes responsibility transfers explicit instead of implicit.

5. `Benefits Question Surface`
   - Tracks benefits or eligibility questions that need coordination follow-up.
   - Stays short of claims handling or adjudication.

6. `Advocate Escalation Queue`
   - Provides a visible human escalation surface for ambiguous, sensitive, or clinically interpretive follow-up so review work lands with advocates instead of being forced into automated resolution.

### 3.2 Abstraction Levels
1. `Intake and Normalization Layer`
   - Accepts messy source material and turns it into a care case the service can coordinate.

2. `Shared Coordination State Layer`
   - Keeps the current case timeline, pending items, and next-step ownership visible over time.

3. `Handoff and Ownership Layer`
   - Preserves where responsibility moved and what still needs attention.

4. `Human Boundary Layer`
   - Keeps clinically interpretive or sensitive situations with humans rather than pretending the service can resolve them automatically.

### 3.3 External Dependencies
- Referral and intake channels.
- Care documents such as referral forms, intake notes, and discharge paperwork.
- Communication channels with provider offices, pharmacies, payers, and other care contacts.
- Human advocates.

## 4. Core Domain Model

### 4.1 Entities

The core model stays small and centered on the case, the participants involved, the tasks that need ownership, the handoffs that cross settings, and the benefits questions that need cautious follow-up.

#### 4.1.1 Care Case
Fields:
- `case_id` (string)
  - Stable identifier for the care case.

#### 4.1.2 Participant
Fields:
- `participant_id` (string)
  - Stable identifier for a person or organization involved in the case.
- `role` (string)
  - Coordination role such as family caregiver, patient, advocate, provider office, pharmacy, payer, or home-care organization.

#### 4.1.3 Coordination Task
Fields:
- `task_id` (string)
  - Stable identifier for a next action that needs follow-through.
- `description` (string)
  - Summary of what still needs to happen.
- `owner_role` (string or null)
  - Current owner of the next step when known.

#### 4.1.4 Handoff
Fields:
- `handoff_id` (string)
  - Stable identifier for a care transition or responsibility transfer.
- `handoff_from` (string)
  - Source side of the transition.
- `handoff_to` (string)
  - Destination side of the transition.

#### 4.1.5 Benefits Question
Fields:
- `benefits_question_id` (string)
  - Stable identifier for a benefits or eligibility question.
- `question_text` (string)
  - The question being tracked for coordination follow-up.

## 5. Open Questions

- How much outbound follow-up can be automated versus advocate-owned?
- Is the primary access model family direct, employer/payer sponsored, or provider-linked?
- Do reminders belong here or in a separate communication service?
