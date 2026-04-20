# GenAI Usage Log

## Purpose

This document records how Generative AI is used in the project in a methodical and auditable way. It is intended to support the coursework requirement for a declared AI workflow rather than hide AI involvement inside the codebase.

## Tools Used

- Codex for planning, implementation, debugging, and workflow structuring
- Web research support for checking public dataset availability and comparing upstream sources
- Project-specific prompting for data cleaning and semantic exercise enrichment design

## AI-Supported Activities In Phase 2

### 1. Dataset Discovery And Comparison

AI is used to explore candidate public exercise data sources and compare them against project needs:

- documented public access
- structured exercise fields
- suitability for SQL import
- suitability for a reproducible seed workflow

### 2. Schema Design Support

AI helps propose fields that are useful for a constraint-aware planning API, especially fields not normally present in a generic exercise directory:

- movement pattern
- difficulty
- environment suitability
- impact level
- contraindication tags

### 3. Cleaning Rule Drafting

AI is used to draft deterministic cleaning and enrichment heuristics. These drafts are then checked and narrowed into explicit project rules.

### 4. Import Script Scaffolding

AI helps structure the fetch, clean, and import pipeline into separate scripts and testable functions.

## Human Control Boundary

The project does not treat AI-generated labels as authoritative by default.

The following decisions require manual review:

- difficulty classification
- contraindication tags
- any conservative safety-related assumptions

Other fields may use sampling-based review after the rules stabilise.

## Why This Is Higher-Level AI Use

This workflow uses AI for more than low-level code completion. AI is used to:

- compare alternative public data sources
- shape the schema around the project’s real planning logic
- design a reusable enrichment workflow
- support reproducible data preparation for PostgreSQL import

This aligns with the coursework’s emphasis on creative, methodological, and high-level use of GenAI.

## Submission Reminder

The final submission still needs:

- a declared list of AI tools used
- a summary of what each tool was used for
- exported conversation log excerpts as supplementary material
