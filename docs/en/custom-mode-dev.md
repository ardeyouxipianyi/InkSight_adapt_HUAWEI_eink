# Custom Mode Development Guide

InkSight uses pure JSON configuration to define and extend content modes.

## 1. Design Principles

- Decouple content generation from layout rendering
- Configuration-driven, minimizing hardcoding
- New modes should prioritize reusing existing blocks and content types

## 2. Basic Structure

A mode definition typically includes:

- `mode_id` / `display_name` / `icon`
- `content` (generation logic)
- `layout` (rendering structure)
- `cacheable` / `description`

## 3. Common content.type

- `llm`: Text output
- `llm_json`: Structured JSON output
- `computed`: Computed based on local context
- `external_data`: External data source aggregation
- `image_gen`: Image generation
- `composite`: Composing multiple sub-contents

## 4. Suggested Workflow

1. Create a new JSON file under `backend/core/modes/builtin` or `custom`
2. Validate field legality against the schema
3. Verify rendering effect via the preview API
4. Add tests (content generation, rendering, routing)
5. Update README and docs

## 5. Debugging Tips

- First verify if the content layer returns the expected fields
- Then verify if the rendering layer blocks are positioned correctly
- For image modes, prioritize checking external API keys and download pipelines
