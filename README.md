# dhruv's obsidian mcp

i'm working on learning ML compilers + some os concepts this summer so i set up an obsidian vault to track my learning

coincidentally i also wanted some more experience working with mcp so im gonna create an mcp server that connects to codex and gives it some pointers on how to evaluate my learning + make sure my projects are on the right track

stay tuned for updates! we're just getting started ☺︎

## Roadmap

This project is a local MCP server for turning an Obsidian vault into a structured compiler-learning interface.

The goal is not just "AI can read my notes."  
The goal is to build a real MCP-native learning system with:

- **tools** for computation and analysis
- **resources** for stable context surfaces
- **prompts** for reusable workflows

---

## Current State

### Phase 1 — Existing MCP integration
- [x] Connect Codex to an existing Obsidian MCP server
- [x] Validate basic vault access and note summarization

### Phase 2 — Custom local MCP server
- [x] Build a custom Python MCP server
- [x] Expose initial tools:
  - [x] `extract_concepts`
  - [x] `get_learning_gaps`
  - [x] `generate_study_session`
  - [x] `compare_notes_to_project`
- [x] Register server in Codex
- [x] Verify with MCP Inspector
- [x] Get working end-to-end local tool calls

---

## Next Up

### Phase 3 — Flesh out the MCP interface
Goal: evolve from "bag of tools" into a real MCP-backed learning interface.

#### 3.1 Resources
Expose stable, inspectable views of the learning system.

Planned resources:
- [x] `vault://compiler/concepts`
- [x] `vault://compiler/gaps`
- [x] `vault://compiler/recent-notes`
- [x] `vault://project/alignment`
- [x] `vault://weekly-review/latest`

Why:
- tools are good for actions
- resources are good for persistent context
- this makes the server feel more like a system and less like one-off functions

#### 3.2 Prompts
Add reusable workflow templates directly through MCP.

Planned prompts:
- [ ] `weekly_learning_review`
- [ ] `generate_study_plan`
- [ ] `notes_vs_project_analysis`
- [ ] `paper_to_implementation_breakdown`

Why:
- removes the need to remember good prompt phrasing
- turns repeated workflows into first-class interfaces

#### 3.3 Better analysis heuristics
Upgrade from raw keyword counting to more meaningful note analysis.

Planned improvements:
- [ ] frontmatter-aware filtering
- [ ] tag-aware concept grouping
- [ ] recency-aware analysis
- [ ] note depth scoring
- [ ] backlinks / note-link graph analysis
- [ ] better "shallow vs deep" detection
- [ ] concept clustering instead of only exact keyword hits

Why:
- current heuristics are useful but primitive
- this is where the actual intelligence of the server improves

---

## Phase 4 — Multi-source learning system
Goal: compare and synthesize across more than just markdown notes.

Planned sources:
- [ ] Obsidian vault
- [ ] local project repo(s)
- [ ] paper notes / reading notes
- [ ] PDFs or exported paper summaries
- [ ] lightweight project tracker / task file

Planned capabilities:
- [ ] compare notes to implementation
- [ ] compare paper concepts to project gaps
- [ ] detect studied-but-not-built topics
- [ ] generate implementation ideas from recent learning

Why:
- this is where MCP starts becoming genuinely high leverage
- the server becomes a bridge between learning, planning, and building

---

## Phase 5 — Codex workflow integration
Goal: make the server easy and natural to use inside daily Codex workflows.

Planned work:
- [ ] improve tool naming and descriptions
- [ ] make outputs more structured and predictable
- [ ] add AGENTS.md guidance for when to use each MCP feature
- [ ] add example prompts for each tool/resource/prompt
- [ ] reduce need for manual tool invocation phrasing

Why:
- a powerful MCP server is useless if the host/client doesn’t use it well
- ergonomics matter just as much as capabilities

---

## Future / Stretch Ideas

### Sampling
Potential future direction:
- [ ] let the server request model-generated synthesis through MCP sampling

Possible use cases:
- [ ] auto-generate weekly reviews
- [ ] synthesize study guides from grouped notes
- [ ] produce concept summaries from note clusters

Note:
This is intentionally not a near-term priority.  
The server should first have strong tools/resources/prompts before adding more agentic behavior.

### Remote / hosted version
Potential future direction:
- [ ] move from local stdio server to remote server
- [ ] support HTTP transport
- [ ] add auth if needed
- [ ] support broader clients beyond local Codex usage

Note:
This is productization, not the immediate learning goal.

---

## Immediate Priorities

### Priority 1
Implement resources:
- [x] concepts
- [x] gaps
- [x] recent notes digest
- [x] notes/project alignment summary

### Priority 2
Implement prompts:
- [ ] weekly review
- [ ] study session
- [ ] notes vs project comparison

### Priority 3
Improve heuristics:
- [ ] frontmatter and tag support
- [ ] recency filters
- [ ] better depth scoring

---

## Guiding Principle

This project should move toward:

> a real MCP interface for a compiler-learning workflow

and away from:

> a pile of loosely related note-analysis functions

If a new feature does not improve one of these, it probably should not be added:
- learning feedback loops
- study planning
- notes-to-project alignment
- reusable Codex workflows
- structured MCP-native interfaces
