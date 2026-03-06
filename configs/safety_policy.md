# Safety Policy — Verified Health Content System

## Purpose
This document defines the safety policy governing all content and interactions
within the Verified Health Content system. This system is **educational only**.

## Core Principles

1. **No Medical Advice**: The system MUST NOT provide medical advice, diagnosis,
   treatment recommendations, dosages, medication changes, or clinical decisions.

2. **No Direct Addressing**: Do NOT use language like "you have X" or
   "you should take/do X".

3. **Verified Sources Only**: All content comes from a strict allowlist of
   trusted domains and verified YouTube channels. No open web crawling.

4. **Rule-Based Triage Only**: The "Seek Care Guidance" flow uses deterministic
   rules derived from trusted public health sources. The LLM is never involved
   in urgency decisions.

5. **Specialist Navigation Only**: The system maps topics to specialist categories
   for navigation purposes. It does NOT claim the user has a condition.

## Disclaimer (Displayed on Every Page)

> **Educational content only. Not medical advice. If worried, seek professional care.**

## Banned Phrases

The following phrases (and variants) are banned from all system-generated text:

- "You have", "You likely have", "You probably have"
- "diagnosis", "diagnosed with"
- "take", "start taking", "stop taking"
- "increase", "decrease" (in medication context)
- "dosage", "mg", "dose"
- "treatment plan", "treatment"
- "cure", "miracle cure"
- Any medication names paired with directives

If any banned phrase is detected in LLM output, the summary is replaced with
a safe generic neutral fallback.

## LLM Usage Constraints

- LLM (Ollama phi3:mini) is used ONLY for neutral summarization and topic tagging.
- LLM output must be valid JSON matching the expected schema.
- All LLM output is post-processed through the banned-phrase filter.
- The LLM never answers user medical questions directly.

## Refusal Behavior

If a user submits a query seeking diagnosis or medical advice, the system:
1. Returns a refusal message explaining it cannot provide medical advice
2. Suggests consulting a healthcare professional
3. Shows relevant verified educational content instead
