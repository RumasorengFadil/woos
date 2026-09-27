# ORBIT Architecture Blueprint

> **This is not a cloning guide. This is not a fork guide.** This document does not tell you how to copy ORBIT's source code, database, features, or business logic into a new project. It extracts the **proven architecture, structure, conventions, engineering workflow, and documentation patterns** used to build ORBIT, so they can be reused as a starting point for a **completely different, unrelated application**.

```
ORBIT existing implementation
        ↓
extract proven architecture & conventions
        ↓
ORBIT Architecture Blueprint (this document)
        ↓
attached to Claude / Codex / any AI coding assistant
        ↓
AI builds a completely new system
        ↓
same engineering conventions, different business domain
```

## Intended Usage

This document is designed to be attached alongside a Product Requirements Document (PRD) when starting a brand-new project with an AI coding assistant:

```
You:
"Build an inventory management system based on the attached PRD.
Use ORBIT_ARCHITECTURE_BLUEPRINT.md as the architecture and
engineering convention."

Attachments:
- PRD.md
- ARCHITECTURE_BLUEPRINT.md
```

After reading both documents, the AI should understand:

- `PRD.md` defines **WHAT** to build.
- `ARCHITECTURE_BLUEPRINT.md` (this document) defines **HOW** the project should be structured and developed.

```
PRD
↓
business requirements

ORBIT Architecture Blueprint
↓
engineering architecture & conventions

AI implementation
↓
new application
```

---

## Mandatory AI Interpretation

**When this document is provided to an AI coding assistant together with a PRD, treat this document as the engineering architecture and convention specification for the project.**

- Do not clone ORBIT source code.
- Do not copy ORBIT business modules.
- Do not copy ORBIT database tables or schema.
- Do not reproduce ORBIT-specific roles, workflows, naming, or organizational structures unless explicitly required by the current project's PRD.
- Build the new system from a clean repository while following the reusable architecture patterns and engineering conventions defined in this document.
- The current project's PRD defines the business domain. This blueprint defines how the codebase should be structured and maintained.

**Do not do this:**

```
copy ORBIT
↓
rename
↓
delete unused modules
↓
build new application
```

**Do this instead:**

```
create clean repository
↓
initialize architecture
↓
create project structure
↓
configure environment
↓
initialize database
↓
initialize authentication
↓
initialize authorization
↓
create shared foundation
↓
implement business modules from PRD
```

---

## Blueprint vs Product Requirement

`ARCHITECTURE_BLUEPRINT.md` does not define application features. It only defines:

- architecture;
- folder structure;
- naming conventions;
- database conventions;
- migration conventions;
- authentication foundation;
- authorization foundation;
- module organization;
- documentation structure;
- testing conventions;
- development workflow;
- implementation reporting;
- security baseline;
- configuration management.

Whereas `docs/product/PRD.md` (of the **new** project) defines:

- application purpose;
- users;
- roles;
- features;
- workflows;
- business rules;
- domain entities;
- UI requirements;
- integration requirements.

### Conflict Resolution

If there is a conflict between this blueprint and the domain needs expressed in the PRD:

1. Preserve the blueprint's architectural principles as far as reasonably possible.
2. Adapt the implementation to what the PRD actually needs.
3. Never force ORBIT's business rules onto the new project.
4. Document the architectural deviation if one is genuinely required.

---

## Core Architecture

Generalized reusable architecture pattern, extracted from ORBIT's actual implementation.

**Default stack:**

```
Backend/Application:  PHP Native 8.3+
Database:              PostgreSQL 14+
Dependency Management: Composer
Frontend:              Server-rendered HTML, CSS, vanilla JavaScript where required
Authentication:        PHP Session
Architecture:          Modular monolith, domain-oriented modules
Configuration:         .env
Database Evolution:    SQL migrations
Web Server:            Apache + mod_rewrite
```

Do not bring in dependencies that are not needed. The new project should stay as simple as ORBIT, but its structure and conventions should be cleaner from day one.

---

## Architecture Philosophy

```
Simple
Explicit
Traceable
Modular
Domain-oriented
Low dependency
Documentation-driven
AI-friendly
```

The project must be easy to understand for both human developers and AI coding assistants. Avoid unnecessary abstraction. Do not introduce a framework, ORM, microservices, event bus, message broker, or a heavy dependency without a clear need stated in the PRD.

---

## Base Project Structure

```
project/
│
├── config/
│   ├── app.php
│   ├── database.php
│   ├── database.example.php
│   ├── auth.php
│   └── role_access.php
│
├── modules/
│   ├── auth/
│   │   ├── login.php
│   │   ├── login_submit.php
│   │   └── logout.php
│   │
│   └── <domain>/
│       ├── index.php
│       ├── create.php
│       ├── edit.php
│       ├── view.php
│       └── ...
│
├── shared/
│   ├── menu.php
│   ├── header.php
│   ├── footer.php
│   └── components/
│
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── automation/          (optional -- see Starter Classification)
│
├── storage/
│   ├── uploads/
│   └── logs/
│
├── tests/
│
├── tools/
│
├── docs/
│   ├── README.md
│   ├── architecture/
│   │   └── overview.md
│   ├── database/
│   │   ├── schema.md
│   │   └── migrations.md
│   ├── deployment/
│   │   └── installation.md
│   ├── features/
│   │   └── <feature>/
│   │       └── README.md
│   ├── security/
│   │   ├── authentication.md
│   │   └── authorization.md
│   ├── product/
│   │   ├── PRD.md
│   │   └── roadmap.md
│   └── reports/
│       └── YYYY/
│           └── MM/
│               └── DD/
│
├── .env.example
├── .gitignore
├── composer.json
├── AGENTS.md
├── CLAUDE.md
└── README.md
```

This structure is a **baseline**, not a checklist to fill completely. **Do not create empty folders just to look complete.** Optional folders (`automation/`, `storage/`, etc.) are only created when that capability actually starts being used.

---

## Domain-Oriented Modules

Use:

```
modules/<business-domain>/
```

Not:

```
controllers/
models/
views/
```

Example:

```
modules/
├── auth/
├── inventory/
├── procurement/
├── employee/
└── reporting/
```

Each module represents a business capability. Do not create a folder based on a technical type if the logic in question is actually only used by a single domain.

---

## Shared vs Domain Logic

| Location | Purpose |
|---|---|
| `config/` | Configuration and cross-cutting concerns. |
| `shared/` | Reusable presentation/helper code that is genuinely used across multiple modules. |
| `modules/<domain>/` | Business logic and pages owned by one domain. |

Do not move logic into `shared/` just because it *might* be reused. Generalize only when reuse is already real, not anticipated.

---

## Database Convention

The new project always starts with a **new** database. Do not copy ORBIT's database. Do not use the `orbit_syn` schema unless the PRD explicitly asks for it. Use naming that matches the new application.

Migrations live in `database/migrations/`. Every database structure change must have its own migration, e.g.:

```
001_create_users.sql
002_create_roles.sql
003_create_products.sql
004_add_status_to_products.sql
```

(or another consistent convention). Migrations must be:

- explicit;
- versioned;
- reviewable;
- documented;
- idempotent wherever practical.

Do not make manual schema changes without a migration, except for temporary local investigation.

---

## Authentication

Use PHP Session as the baseline authentication mechanism. Authentication must be separated from authorization.

```
modules/auth/
config/auth.php
```

Authentication is responsible for:

- login;
- logout;
- session;
- user identity;
- authentication guard.

Do not put business roles inside authentication logic.

---

## Authorization / RBAC

Use a centralized authorization foundation:

```
config/role_access.php
```

or a more modular structure as the project grows. **Do not copy ORBIT's roles**, such as:

```
SUPER ADMIN
MANAGER
ASMAN
PIC_MUTASI
PIC_REVIEWER
PIC_APPROVAL
```

Roles come from the new application's PRD. The blueprint only defines the pattern:

```
User
↓
Role
↓
Permission
↓
Scope
↓
Authorization Check
```

If the application is simple, the implementation can be simple. If the PRD needs complex RBAC, design a scalable role/permission table accordingly.

---

## Routing

ORBIT's legacy compatibility routing is **not** the default. `route_map.php` and a compatibility router are only used if a project genuinely needs to preserve old URLs (e.g. after restructuring an existing, already-deployed application). For a brand-new project, use simple, consistent routing from the start.

Legacy compatibility routing must be classified as an **OPTIONAL PATTERN**, not core architecture.

---

## Documentation Convention

Use `docs/` as the single source of truth for technical documentation. Every significant change to features, workflow, database, API, architecture, authentication, authorization, or deployment must update the related documentation. Do not create a new document when an existing one should actually be updated.

### Product Source of Truth

```md
## Product source of truth

`docs/product/PRD.md` is the authoritative product requirement document for the current application.

Preserve it unless the user explicitly requests a requirement change.

`docs/product/roadmap.md` tracks implementation scope, increments, milestones, and progress.

Never represent planned functionality as implemented.

This architecture blueprint defines engineering structure and conventions only.

The current project's PRD defines the business domain, features, workflows, roles, data entities, and business rules.

Build incrementally. Complete and verify the current increment before starting the next one.
```

### Documentation Source of Truth

| Document | Defines |
|---|---|
| `PRD` | Product requirements. |
| `roadmap` | Implementation planning. |
| `architecture` | Architecture decisions. |
| `features` | Actual implemented feature behavior. |
| `database` | Schema and migration documentation. |
| `security` | Authentication and authorization. |
| `reports` | Implementation history. |

Do not use the roadmap as evidence that a feature is implemented. `docs/features/` documentation must always reflect the actual current implementation, not a plan.

### Audience-Tailored Reports

Not every reader of `docs/reports/` is an engineer. When a report's actual audience is a non-technical stakeholder (a business/product owner, a functional lead, an auditor), rewrite it for that audience instead of handing over the engineering version:

- Keep the same **structure** (module → menu/section → feature), so both versions stay easy to cross-reference.
- Replace file names, table/column names, query logic, and implementation detail with **purpose, benefit, and usage flow**.
- Give a plain-language, one-line explanation the first time an unavoidable domain term appears, instead of assuming prior technical knowledge.
- Keep both versions when they serve different readers: the engineering version stays the source of truth for developers; the plain-language version is a separate, explicitly labeled artifact (e.g. suffixed `_bpo` or headed "Business Version") — never silently replace one with the other, and never let the simplified version invent a claim the technical version does not support.

This is a documentation-audience pattern, not a new document category — it does not change where reports live (`docs/reports/<year>/<month>/<day>/`) or the Implementation Report format above.

---

## Development Workflow

```
Read PRD
↓
Read Architecture Blueprint
↓
Understand existing repository
↓
Determine current increment
↓
Implement
↓
Test
↓
Manual verification
↓
Update documentation
↓
Write implementation report
↓
Continue next increment
```

Do not implement the entire PRD at once without need — work incrementally.

---

## Architecture Change Rule

If the AI wants to change any of the following, treat it as an **architecture decision**, not a minor implementation change:

- main folder structure;
- database architecture;
- authentication model;
- authorization model;
- a major dependency;
- routing model;
- infrastructure architecture.

Document the reason and the impact. If the change is not required by the PRD, keep the blueprint baseline.

---

## Database Change Rule

If an implementation adds or changes a table, column, index, constraint, view, materialized view, or database function, the AI must:

1. Create a migration.
2. Update the database documentation.
3. Record the change in the implementation report.
4. Name the affected tables.
5. Provide a manual verification step when relevant.

---

## Implementation Report

After a significant change, use this short format:

```md
## Implementation Report

### Changed
- ...

### Files
- ...

### Database
- No database changes.

  (or)

- Added table: ...
- Added column: ...

### Tests
- PASS / FAIL / NOT TESTED / NOT APPLICABLE

### Manual Test
1. ...
2. ...
3. ...

### Documentation
- Updated ...
```

Never report a test as `PASS` if it was not actually run.

---

## AI Coding Assistant Convention

This document must be usable by Claude Code, Codex, ChatGPT coding agents, or any other coding assistant. Avoid instructions that depend on a single AI vendor — use the generic term **"AI coding assistant"** throughout the shared conventions.

Tool-specific instructions may still live in their own files (e.g. `CLAUDE.md` for Claude Code), while cross-agent conventions belong in `AGENTS.md`.

**When writing `AGENTS.md`/`CLAUDE.md` for the new project**: its `## Project` section must always be written fresh for the actual project being built — never copied from this blueprint, and never copied from ORBIT's own `CLAUDE.md`/`AGENTS.md`. That section is what every later decision by the AI is built on; if it is wrong or generic, everything downstream inherits that mistake. Everything else in `AGENTS.md`/`CLAUDE.md` (setup commands, test commands, architecture notes, conventions) can start from this blueprint's patterns, but must describe the **new project's own** implementation once it exists, not ORBIT's.

---

## Starter Classification

Split every pattern in this blueprint into three categories.

### CORE — mandatory baseline for every project

- modular monolith;
- domain-oriented modules;
- PostgreSQL;
- `.env`;
- config separation;
- documentation convention;
- migration convention;
- authentication foundation;
- authorization foundation;
- incremental development.

### OPTIONAL — only used if the PRD requires it

- automation (background jobs / external sync);
- upload storage;
- AI features;
- background processes;
- external synchronization;
- legacy URL compatibility (`route_map.php` + router);
- materialized views;
- complex RBAC.

### DOMAIN SPECIFIC — must never be part of the starter

- FTK (workforce formation);
- Talent;
- Mutasi (employee transfer);
- FNP (Fit and Proper);
- HCBP;
- PLN organizational structure;
- PLN-specific roles;
- ORBIT's approval workflows;
- ORBIT's database tables;
- ORBIT-specific queries.

---

## Technical Debt Filtering

Do not automatically treat every part of ORBIT's implementation as best practice. When extracting a convention from ORBIT, classify it as one of:

```
REUSABLE PATTERN
OPTIONAL PATTERN
LEGACY COMPATIBILITY
TECHNICAL DEBT
DOMAIN SPECIFIC
```

Only `REUSABLE PATTERN` becomes part of the blueprint baseline. Known items from ORBIT's own codebase that fall **outside** `REUSABLE PATTERN`, so they are not silently inherited by new projects:

| Pattern | Classification | Why |
|---|---|---|
| `route_map.php` + compatibility router | LEGACY COMPATIBILITY | Only exists to preserve old URLs after ORBIT's own root-to-`modules/` restructuring. A new project has no old URLs to preserve. |
| No centralized auth guard (every page repeats the session check) | TECHNICAL DEBT | Works, but there is no second layer of protection if a page forgets the boilerplate. New projects should still start from the same explicit-check pattern (it is simple and traceable) but should consider a lightweight shared guard once the page count grows. |
| Menu renders with no RBAC (`shared/menu.php` shows all items regardless of role) | TECHNICAL DEBT | ORBIT enforces access only at the page level; the menu does not hide links a user cannot use. Decide explicitly for the new project whether this is acceptable. |
| PIN reset with no identity verification | TECHNICAL DEBT | A real gap in ORBIT's authentication flow. Do not reuse as-is if the new project handles more sensitive data or is more exposed. |
| Chatbot AI module | DOMAIN SPECIFIC + OPTIONAL PATTERN | Built for PLN's HC/SDM domain with domain-specific prompts and data. The *pattern* of an isolated AI module with its own config is reusable; the content is not. |
| `automation/` sync scripts | OPTIONAL PATTERN | The pattern (external jobs write to a log table the app reads back) is reusable; ORBIT's specific staging-database sync logic is domain specific. |

ORBIT's technical debt must not be inherited by the new application.

---

## Expected AI Behavior

After the AI receives this blueprint together with a PRD, it should be able to make decisions like:

```
PRD asks for an inventory module
→ create modules/inventory/

PRD asks for login
→ use the auth foundation from this blueprint

PRD asks for PostgreSQL
→ create a new application schema

PRD asks for admin and operator roles
→ implement those roles, not ORBIT's roles

PRD asks for file upload
→ enable the optional storage capability

PRD does not ask for AI
→ do not create an AI module

PRD does not need legacy URLs
→ do not create a route compatibility layer
```

---

## Final Objective

> Build a completely new application from scratch using the ORBIT engineering architecture and conventions as the blueprint. Do not clone ORBIT. Do not carry ORBIT business logic. The attached PRD defines the new system's business requirements.

The end goal is that a new project can be started by providing only:

```
1. The new application's PRD
2. ARCHITECTURE_BLUEPRINT.md
```

and Claude Code, Codex, or any other AI coding assistant immediately understands:

```
WHAT to build   → the PRD
HOW to build it → this Architecture Blueprint
```
