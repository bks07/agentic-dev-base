# [Application Name] – Constitution

> Replace all placeholder text in square brackets before using this file for a real app.

## Purpose

[Describe the product in 2–4 sentences. Explain who it serves, what problem it solves, and what outcome it enables.]

## Users

- **Primary users**: [who uses the app most]
- **Secondary users**: [other user groups, if any]
- **Administrators / operators**: [who manages the system]

## Assumptions

1. **Trust Model**: [What is assumed about user behavior, permissions, and misuse?]
2. **Scale Profile**: [Expected number of users, teams, requests, or data volume.]
3. **Access Model**: [How roles are granted, who can do what, and default permissions.]
4. **Operational Constraints**: [Availability, compliance, security, device, or geography constraints.]

## Product Principles

- **Primary value proposition**: [What matters most for this app to do well?]
- **User experience standard**: [Fast, simple, accessible, enterprise-grade, mobile-first, etc.]
- **Reliability expectation**: [Internal tool tolerance vs customer-facing strictness.]
- **Data sensitivity**: [Low / medium / high, with a short explanation.]

## Technology Stack

### Backend

- **Language**: [e.g. Rust, Node.js, Python, Go]
- **Runtime**: [e.g. Tokio, Node, JVM, serverless]
- **Web Framework**: [e.g. Axum, Express, FastAPI, Spring]
- **Database**: [e.g. PostgreSQL, MySQL, SQLite, MongoDB]
- **Authentication**: [e.g. JWT, session auth, OAuth]
- **Logging / Observability**: [e.g. tracing, OpenTelemetry, Datadog]
- **Other notable infrastructure**: [queues, caching, search, background jobs]

Key dependencies:
- [dependency name] — [purpose]
- [dependency name] — [purpose]
- [dependency name] — [purpose]

### Frontend

- **Language**: [e.g. TypeScript, JavaScript]
- **Framework**: [e.g. React, Vue, Svelte]
- **Build Tool**: [e.g. Vite, Next.js, Webpack]
- **Routing**: [library or approach]
- **State / Data Fetching**: [e.g. Context, Redux, TanStack Query]
- **HTTP Client**: [e.g. fetch, Axios]
- **Testing**: [e.g. Vitest, Jest, Playwright]
- **Design System / UI Library**: [if applicable]

Key dependencies:
- [dependency name] — [purpose]
- [dependency name] — [purpose]
- [dependency name] — [purpose]

### Architecture

```text
[Client / UI]
      ↓
[API / Application Layer]
      ↓
[Data Store / External Services]
```

Add more detail here if the app has multiple services, background workers, third-party integrations, or event flows.

### Deployment

- **Hosting model**: [e.g. Docker, Kubernetes, serverless, VM]
- **Environments**: [e.g. local, staging, production]
- **Delivery pipeline**: [brief CI/CD notes]
- **Operational dependencies**: [databases, secrets, queues, cloud services]

### Code Quality & Testing

- **Unit Tests**: [tools and expectations]
- **Integration Tests**: [tools and expectations]
- **E2E Tests**: [tools and expectations]
- **Type Safety**: [TypeScript, static typing, schema validation, etc.]
- **Linting / Formatting**: [tools used]
- **Build Verification**: [what must pass before release]

## Domain Rules

- [Important business rule or invariant]
- [Important workflow rule or policy]
- [Important permission or approval rule]

## Non-Goals

- [What this app intentionally does not try to do]
- [Scope boundaries that should remain out of the product]

## Change Guidance

When making architecture or product decisions for this app:

1. Prefer changes that reinforce the stated product principles.
2. Keep implementation aligned with the declared stack unless there is a strong reason to change it.
3. Respect the domain rules and non-goals above.
4. Update this constitution when major assumptions or architecture decisions change.
