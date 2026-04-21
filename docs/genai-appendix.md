# GenAI Appendix: Evidence, Representative Conversation Excerpts, and AI Workflow Artifacts

## Submission Links

- Public GitHub repository: https://github.com/leedsnoob/fitness-planner-api
- Technical report PDF: https://github.com/leedsnoob/fitness-planner-api/blob/main/docs/technical-report.pdf
- API documentation PDF: https://github.com/leedsnoob/fitness-planner-api/blob/main/docs/api-documentation.pdf
- Presentation slides link: https://github.com/leedsnoob/fitness-planner-api/blob/main/docs/presentation-slides-link.md
- GenAI usage log: https://github.com/leedsnoob/fitness-planner-api/blob/main/docs/genai-usage.md
- Custom skill artifact: https://github.com/leedsnoob/fitness-planner-api/tree/main/skills/exercise-constraint-enricher
- Tagging rules reference: https://github.com/leedsnoob/fitness-planner-api/blob/main/skills/exercise-constraint-enricher/references/tagging-rules.md

## 1. Purpose

This appendix provides explicit evidence of Generative AI use in the project. It is intended to support the GenAI declaration in the technical report and satisfy the coursework requirement to attach examples of exported conversation logs as supplementary material. The appendix focuses on representative, high-value interactions rather than raw full-length transcripts.

The key point is that GenAI was not used only for low-level code completion. It was used to compare design alternatives, shape the data workflow, structure semantic enrichment, evaluate recommendation strategies, and integrate explanations in a controlled, auditable way.

## 2. Tools Used and Human Review Boundary

- **Codex**: planning, implementation support, debugging, architecture review, documentation structuring, deployment guidance.
- **SiliconFlow + Qwen**: runtime explanation generation inside the API.
- **Repository skill artifacts**: the custom skill and tagging rules capture the AI-assisted enrichment workflow in a reusable form.

Human review remained the final decision point for:

- selecting `wger` as the primary dataset;
- defining the enrichment fields used in the schema;
- deciding not to use collaborative filtering or end-to-end LLM planning;
- treating explanations as a non-critical enhancement rather than a transaction dependency;
- finalizing tagging rules for conservative fields such as difficulty and contraindication tags.

## 3. Representative Conversation Excerpts

### Case 1. Dataset Discovery and Source Selection

**Goal**

Identify a public exercise dataset suitable for a reproducible SQL-backed API project.

**Representative prompt excerpt**

```text
Compare public exercise data sources for a fitness planning API. I need something that is structured enough for SQL import, easy to cite, and suitable for a reproducible seed pipeline.
```

**Representative AI contribution**

- surfaced trade-offs between `wger`, `free-exercise-db`, and Kaggle-style sources;
- highlighted provenance and API accessibility as selection criteria rather than only dataset size.

**Human decision**

I selected `wger` as the primary upstream source because it was easier to justify in a technical report and better supported a reproducible fetch-clean-import workflow. I did not adopt the AI suggestion blindly; I used it to narrow the comparison and then made the final selection based on project constraints.

**Result in the repository**

- `data/raw/wger_exercises_snapshot.json`
- `data/seeds/exercises_cleaned.json`
- `scripts/import_exercise_seed.py`
- `docs/dataset-evaluation.md`

### Case 2. Schema and Semantic Enrichment Design

**Goal**

Move beyond a generic exercise directory and support constraint-aware planning and replacement.

**Representative prompt excerpt**

```text
What additional fields would make a public exercise dataset useful for a rule-based training planner that has to consider home vs gym, user discomfort, and exercise replacement?
```

**Representative AI contribution**

- proposed project-specific semantic fields such as `movement_pattern`, `difficulty`, `impact_level`, and `contraindication_tags`;
- helped separate recommendation-facing schema needs from raw upstream fields.

**Human decision**

I kept only fields that could be justified by actual planning or replacement logic. I rejected open-ended or weakly grounded ideas and narrowed the enrichment layer to fields that could be supported by deterministic heuristics and manual review.

**Result in the repository**

- `app/models/exercise.py`
- `docs/data-design.md`
- `skills/exercise-constraint-enricher/SKILL.md`
- `skills/exercise-constraint-enricher/references/tagging-rules.md`

### Case 3. AI Workflow Artifact: Custom Skill and Tagging Rules

**Goal**

Turn AI-assisted enrichment into a reusable and reviewable workflow instead of invisible prompting.

**Representative prompt excerpt**

```text
I do not want enrichment prompting to live only in chat history. Help me turn it into an explicit workflow artifact with input, output, deterministic rules, and manual-review boundaries.
```

**Representative AI contribution**

- helped structure the enrichment process into a custom skill;
- encouraged separating the skill instructions from the narrower tagging rules reference.

**Human decision**

I kept the skill in the repository because it makes the GenAI workflow auditable. This is stronger evidence than simply saying “AI helped with data cleaning.” I also used conservative review boundaries: difficulty and contraindication tags remain manual-review fields.

**Result in the repository**

- `skills/exercise-constraint-enricher/SKILL.md`
- `skills/exercise-constraint-enricher/references/tagging-rules.md`

### Case 4. Planning Architecture Alternatives

**Goal**

Decide what type of recommendation logic is defensible for this coursework.

**Representative prompt excerpt**

```text
Should this project use collaborative filtering, end-to-end LLM planning, or a rule-based planner with context-aware reranking?
```

**Representative AI contribution**

- clarified the trade-offs between data-hungry collaborative filtering, opaque LLM-driven planning, and a rule-based approach;
- highlighted that limited user-history data makes collaborative filtering hard to defend.

**Human decision**

I chose a rule-based planner with context-aware reranking because it is more explainable, more testable, and better aligned with the actual amount of user data available. AI was used to explore alternatives, not to make the final decision.

**Result in the repository**

- `app/services/planner.py`
- `app/services/plan_adjustments.py`
- `app/services/plan_explanations.py`
- `app/services/analytics.py`

### Case 5. Explanation Layer Design and Failure Isolation

**Goal**

Add natural-language explanations without making AI a hard dependency for the core planning transaction.

**Representative prompt excerpt**

```text
Where should an LLM sit in this system? I want explainability, but I do not want plan generation to become untestable or fragile.
```

**Representative AI contribution**

- supported the design of a separate explanation layer for plans and revisions;
- highlighted the value of input snapshots, stored explanation history, timeout handling, and failure isolation.

**Human decision**

I explicitly rejected designs in which the LLM decides the training plan itself. Instead, I used SiliconFlow + Qwen only for explanations. If the provider fails, the system still preserves plans, revisions, logs, and analytics. This is both a technical and coursework-oriented design choice because it is easier to justify under questioning.

**Result in the repository**

- `app/models/plan.py`
- `app/services/plan_explanations.py`
- `app/api/routes/plans.py`

### Case 6. Technical Report and API Documentation Structuring

**Goal**

Turn a large engineering project into submission-ready coursework materials.

**Representative prompt excerpt**

```text
I need the report to satisfy the coursework brief directly. It must justify the stack, explain the data model, cover testing and deployment, and include a GenAI declaration with evidence.
```

**Representative AI contribution**

- helped map project content to rubric categories rather than writing a generic software report;
- helped identify missing formal deliverables such as the API documentation PDF, technical report PDF, and appendix links.

**Human decision**

I used AI for structure and coverage checking, but every substantive claim was anchored back to the codebase, tests, and deployed system. This reduced the risk of writing a report that says things the implementation does not actually support.

**Result in the repository**

- `docs/api-documentation.md`
- `docs/api-documentation.pdf`
- `docs/technical-report.md`
- `docs/technical-report.pdf`
- `README.md`

## 4. Why the Custom Skill Matters

The repository skill is not an unrelated extra. It is evidence that GenAI use in this project became part of the method, not just part of the chat history. The skill:

- defines when the enrichment workflow should be used;
- defines the input and output contracts;
- explains deterministic tagging steps;
- forces explicit manual-review boundaries for high-risk fields;
- links to a tagging-rules reference file that narrows the heuristic space.

This makes the AI-assisted workflow more reproducible and easier to defend in an oral exam.

## 5. Why This Counts as High-Level GenAI Use

The assessment brief distinguishes between low-level AI assistance and higher-level creative exploration. This project fits the higher-level category because GenAI was used to:

- compare alternative data sources instead of simply writing import code;
- shape the database schema around recommendation constraints;
- evaluate architectural alternatives for planning and explanation;
- turn prompting into repository-level workflow artifacts;
- improve explainability without replacing deterministic business logic.

In other words, the AI contribution was methodological and design-oriented, not just syntactic.

## 6. Appendix Summary

The appendix shows that GenAI use in this project is:

- declared;
- evidenced by repository artifacts;
- connected to specific technical outcomes;
- bounded by explicit human review.

This is the strongest way to present GenAI usage for the coursework because it demonstrates both creativity and responsible engineering control.
