---
name: convert-2-mindmap-md
description: Convert long-form source text into structured mind-map markdown for XMind/Markdown workflows. Use when user asks to turn notes, OCR text, articles, PDFs, transcripts, or tutorials into mind-map files with clear hierarchy, concise nodes, and actionable branches.
---

# convert-2-mindmap-md

Convert input content into mind-map-friendly Markdown with stable hierarchy and short node text.

## Output Rules

- Use a single H1 as root topic.
- Use nested bullet lists (`-`) for branches/sub-branches.
- Keep each node short (prefer 4-18 Chinese characters, or brief phrases).
- Preserve source meaning; do not invent facts.
- Collapse repetition; merge similar points.
- Keep branch depth typically 3-5 levels.
- End with `- 行动建议` branch when source includes practical advice.

## Workflow

1. Identify document type: 方法论 / 教程 / 复盘 / 访谈 / 规范.
2. Extract top-level trunks (usually 5-9).
3. For each trunk, extract key sub-points and evidence/examples.
4. Refactor into parallel structure (same level = same abstraction).
5. Emit final markdown only.

## Node Design Heuristics

- Prefer nouns for trunks, verbs for actions.
- Keep one idea per node.
- Use sequence labels only when order matters (如“7天/15天/30天”).
- Put formulas, thresholds, and metrics in dedicated child nodes.
- Mark risk/compliance items explicitly as `风险` / `边界`.

## Prompt Template (Expert Mode)

See `references/prompt-templates.md` for reusable prompts.
