# agentic-dev-base

An **agentic operating system** for software delivery—a production-ready framework that orchestrates specialized AI agents through a structured workflow engine, enabling frictionless handoffs between specification, coding, and testing phases.

## Why This Matters

The future of software development is agentic. Teams that replace slow ticket bounce-backs and context-switching with **autonomous agent coordination** ship better software, faster, with fewer handoff failures.

This codebase eliminates Jira workflow chaos by implementing a clear contract-based protocol where:

- **One agent** manages Jira as the single source of truth
- **Specialist agents** own specific domains (specification, coding, unit testing, integration testing, CI, quality gates)
- **Orchestrator agents** coordinate work and enforce process discipline
- **Shared skills** capture procedural knowledge (Jira operations, app resolution, spec lifecycle)
- **Process documents** define the authoritative workflow rules

The result: **deterministic, observable, and recoverable** software delivery. No more "who's doing what?" No more lost context. No more manual status updates.

## Read the Vision

Explore the ideas behind agentic software delivery:

- 📄 [An Agentic Operating System for Software Delivery](https://medium.com/agileinsider/an-agentic-operating-system-for-software-delivery-d2ca49ff70f0) — How structured agents replace ticket chaos
- 📄 [Doing It the Schlein Way: Killing Jira Due to the Rise of the Agentic AI](https://medium.com/agileinsider/doing-it-the-schlein-way-killing-jira-due-to-the-rise-of-the-agentic-ai-0666258299ee) — Why the old workflow bottleneck is gone

## Architecture at a Glance

```
User triggers "." in VS Code
         ↓
     Manager (Orchestrator)
    ↙    ↓    ↓     ↘
Jira  Spec  Code   Test
      ↓      ↓      ↓
   Scribes  Coder  Engineers
           Tester  CI
   Designer  Inspector
```

### Agent Layers

**Top Layer (Orchestration)**
- `Manager` — Decides which phase executes; never edits code
- `Jira Connector` — Only bridge to Jira; owned by Manager

**Phase Orchestrators (Process Gatekeepers)**
- `Specification / Orchestrator` — Intake → spec creation → finalization
- `Coding / Orchestrator` — Planning → coding → unit testing
- `Testing / Orchestrator` — Test planning → execution → merge gate

**Planners (Non-Coding Planning)**
- `Specification / Planner` — Spec task decomposition
- `Coding / Planner` — Implementation task decomposition
- `Testing / Planner` — Test coverage planning

**Specialists (Tool-Wielding Experts)**
- `Specification / Scribe` — Creates and maintains all spec types (unified agent handles bugfix, story, rebrush, technical initiative)
- `Specification / Code Inspector` — Reads code to inform specs (read-only)
- `Specification / Status` — Manages spec lifecycle status
- `Coding / Coder` — Writes production code
- `Coding / Unit Tester` — Writes unit tests alongside code
- `Coding / Designer` — Owns UI/UX and design system
- `Testing / Test Engineer` — Runs coding-phase tests; adds integration tests
- `Testing / UI Tester` — E2E browser journeys
- `Testing / CI Engineer` — CI workflows and artifact handling
- `Testing / Test Quality Reviewer` — Merge gate gatekeeper

### Shared Knowledge (Skills)

Skills encode reusable procedures instead of duplicating them across agents:

- **`jira`** — Fetch, transition, block, comment on work items
- **`app-resolution`** — Map Jira Application field → app folder + constitution
- **`spec-lifecycle`** — File naming, folder structure, templates, status management

### Workflow Phases

1. **Next → Specifying** — Intake specification from Jira; capture WHAT and WHY
2. **Specifying → Coding** — Implementation planning and code delivery
3. **Coding → Testing** — Test planning, execution, coverage gaps, quality gate
4. **Testing → Finalizing** — Promote to develop, finalize specs, close work item
5. **Finalizing → Done** — Complete

## Project Structure

```
.github/
  agents/              # 18 custom agent definitions
  skills/              # 3 shared skill definitions
processes/             # Authoritative workflow rules
templates/             # Spec templates (bug, story, rebrush, tech initiative)
tools/
  init_app.py          # Clone and bootstrap a new app repo under /apps
  jira-connector/      # Jira API scripts + client
  agent-hooks/         # PreToolUse enforcement (app scope isolation)
apps/
  team-availability-matrix/  # Example app under test
  application-mapping.yml    # Jira Application field → app folder
specs/                 # Specification files (bugfix, product-areas, rebrushes, technical-initiatives)
```

## Getting Started

### Prerequisites

- **VS Code** with GitHub Copilot Chat
- **Python 3.8+** for Jira connector scripts
- **Git** for version control
- A **Jira Cloud** instance with API token (set via `JIRA_API_TOKEN` env var)

### Configuration

1. Copy `tools/jira-connector/config.example.yml` to `tools/jira-connector/config.yml`
2. Fill in your Jira instance details (`base_url`, `user_email`, `project.key`)
3. Set `JIRA_API_TOKEN` in your environment:
   ```bash
   export JIRA_API_TOKEN="your_jira_api_token_here"
   ```
4. Configure your app mapping in `apps/application-mapping.yml`:
   ```yaml
   applications:
     - name: "Your App Name"
       app_folder: "your-app-folder-name"
   ```

### Creating a New Application

Before initializing a new app in this workspace:

1. Create a new GitHub repository first.
2. Copy the repository SSH URL from GitHub.
3. Run the init tool from the workspace root and pass the exact Jira Application value:
   ```bash
   python3 tools/init_app.py --name "Your App Name" git@github.com:your-org/your-new-app.git
   ```
4. The tool will:
   - clone the repository into `apps/`
   - stop with an error if that app repo already exists in `apps/`
   - create and switch to the local `develop` branch before adding scaffolded content
   - create `constitution.md` in the cloned repo using `templates/constitution.template.md`
   - create the default folder structure for `specs/` and `docs/architecture/`
   - update `apps/application-mapping.yml` so the passed application name matches the Jira `Application` field value for agent resolution

The generated app scaffold includes these directories:

```text
specs/
  bugfixing/
  product-areas/
  rebrushes/
  technical-initiatives/
docs/
  architecture/
```

### Running the Workflow

In VS Code, with the chat panel open:

1. Type `.` to trigger the Manager
2. Manager fetches the next work item from Jira
3. Agents execute specification → coding → testing → finalization in a loop
4. After testing passes, Manager commits and pushes to `origin/develop` automatically
5. Move the work item to Done

## A Worked Example

See [team-availability-matrix](https://github.com/bks07/team-availability-matrix) — a full-stack React + Rust app built and tested using this agentic system. It demonstrates:

- Specification intake from Jira
- Full-stack implementation (frontend + backend)
- Unit test authorship during coding
- Integration test coverage validation
- CI workflow automation
- Spec finalization and promotion

## Philosophy

### Lean and Precise

- Agents stay focused. Orchestrators delegate with explicit contracts.
- Skills encode shared procedures once; agents reference them.
- No redundant knowledge. No duplication.
- Every agent has a single clear responsibility.

### Deterministic

- Process documents are the source of truth. Agents follow them.
- Workflows are observable via Jira status and agent output.
- Failures are explicit and recoverable (blocked flag, detailed blockers).
- No ambiguity in handoffs — contracts are structured and validated.

### Observable

- Every phase produces a detailed report posted to Jira.
- Agent output includes exact files changed, commands run, test results.
- Risks, blockers, and open questions are surfaced immediately.
- No silent failures.

## Contributing

This framework is designed to evolve. If you:

- Discover redundancies in agent or skill definitions,
- Find workflow bottlenecks,
- Want to add new agent types or specialist roles,
- Have ideas for shared skills,

Consider opening an issue or PR to keep the system lean and precise.

## License

See [LICENSE](LICENSE)
