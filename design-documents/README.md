# Design Documents (`design-documents/`)

This directory stores **all architectural & UI/UX proposals, PDFs, Markdown specifications, diagrams and media (GIF/MP4) related to the LONGIN AI Systems project**.

## 1. Folder Structure Convention

| Sub-folder | Purpose |
|------------|---------|
| `architecture/` | High-level system & component diagrams (Mermaid / SVG) and PDF analyses. |
| `modules/` | Detailed specs of individual modules, connectors, adapters. |
| `agents/` | Prompts, state-machines and flow-charts for core agents (CodingFlowBoss, ContextMaster, …). |
| `ui-ux/` | Wireframes, design guidelines, colour palettes, GIF indicators. |
| `installer/` | Web-installer flows, onboarding steps, screenshots. |

*(If a document belongs to more categories, store a symlink or leave a cross-reference note.)*

## 2. Naming Rules

```
<YYMMDD>-<short-topic>[-vN].md|pdf|gif
```

Examples:
- `250620-system-overview-v1.pdf`
- `250620-garbage-collector-spec.md`
- `250620-thinking-indicator.gif`

Avoid diacritics & spaces to keep cross-platform compatibility.

## 3. GIF Activity Indicators

- Place raw GIFs (e.g. `3LJU_V2.gif`, `supawork-80adee47.gif`) in `ui-ux/indicators/`.
- Reference them in design docs using relative paths:
  ```
  ![Thinking…](../ui-ux/indicators/3LJU_V2.gif)
  ```
- Target usage: front-end components show the GIF while agents are in `thinking` state.

## 4. Contribution Workflow

1. **Create/Update document** in appropriate sub-folder.
2. Add bilingual header *(English first, Czech below)* with:
   - Title
   - Status (`draft`, `review`, `approved`)
   - Related JIRA / GitHub issue
3. Commit with message:
   ```
   docs(design): <topic> – <short note>
   ```
4. Open Pull Request, assign **Architecture** label, request review from `@core-team`.

## 5. Quick Links

| Document | Description |
|----------|-------------|
| [`LONGIN-implementation-plan.md`](../docs/) | Master implementation plan generated from all source specs. |
| [`garbage-collector-spec.md`](architecture/) | Context window GC design (512 token limit). |
| [`ui-guidelines.md`](ui-ux/) | Front-end rules (black bg, green borders, GIF indicators). |

---

_Placeholder README; update when new document types are introduced._  
