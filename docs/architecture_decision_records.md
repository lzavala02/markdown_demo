# Architecture Decision Records (ADR)

This document records the key architectural decisions made for the **Campus Event Hub** system, following a consistent ADR format.

---

## ADR 001 — System Roles & Communication

**Title:** Client–Server Architecture

**Status:** Accepted

### Context

The system supports students browsing events, student organizations submitting events, and administrators reviewing and approving events. All interactions are web-based and follow a request/response pattern, with no real-time communication requirements.

### Decision

Adopt a **Client–Server architecture**, where a web client communicates with a centralized backend server responsible for business logic and data persistence.

### Alternatives Considered

* **Event-Driven Architecture** — introduces asynchronous messaging and additional infrastructure not required for the current use cases.

### Consequences

**Positive**

* Simple and well-understood architecture
* Easy to implement and maintain with a small team
* Fits synchronous workflows such as submission, approval, and browsing

**Negative**

* Less flexible for future real-time or highly decoupled workflows
* Backend may become more complex as features grow

---

## ADR 002 — Deployment & Evolution Strategy

**Title:** Monolithic Application Deployment

**Status:** Accepted

### Context

The system has low to moderate usage, limited operational resources, and is maintained by a small engineering team. Ease of deployment and maintenance is a priority.

### Decision

Deploy the system as a **Monolithic application**, packaged and deployed as a single unit.

### Alternatives Considered

* **Microservices Architecture** — offers independent scaling and deployment but significantly increases operational complexity.

### Consequences

**Positive**

* Simple deployment and testing
* Lower infrastructure and operational costs
* Easier debugging and monitoring

**Negative**

* Scaling individual components independently is not possible
* Large codebase may become harder to manage if not well structured

---

## ADR 003 — Code Organization & Dependency Direction

**Title:** Layered Architecture

**Status:** Accepted

### Context

The application includes distinct concerns such as request handling, business rules, and data persistence. Maintainability and clarity are important for future development.

### Decision

Organize the codebase using a **Layered Architecture** (presentation, business logic, and data access layers).

### Alternatives Considered

* **Feature-Based Architecture** — groups code by feature but can blur boundaries between concerns in smaller teams.

### Consequences

**Positive**

* Clear separation of concerns
* Easier onboarding for new developers
* Changes in one layer have limited impact on others

**Negative**

* Some features may require changes across multiple layers
* Risk of overly rigid boundaries if not applied pragmatically

---

## ADR 004 — Data & State Ownership

**Title:** Single Shared Database

**Status:** Accepted

### Context

All core functionality centers around event data and its lifecycle. Strong consistency and simple querying are required for browsing and administration.

### Decision

Use a **Single shared database** for all application data.

### Alternatives Considered

* **Database per Service** — assumes a microservices architecture and introduces data duplication and synchronization challenges.

### Consequences

**Positive**

* Strong consistency for event status updates
* Simpler querying and reporting
* Reduced infrastructure complexity

**Negative**

* Database schema changes can impact multiple parts of the system
* Less flexibility if the system is later split into services

---

## ADR 005 — Interaction Model

**Title:** Synchronous Interaction Model

**Status:** Accepted

### Context

Users expect immediate feedback when submitting events, browsing listings, or approving events. There are no long-running or background-heavy tasks.

### Decision

Use a **Synchronous interaction model** based on standard HTTP request/response communication.

### Alternatives Considered

* **Asynchronous Interaction Model** — useful for long-running or background tasks but unnecessary for current requirements.

### Consequences

**Positive**

* Immediate user feedback
* Simple control flow and easier debugging
* Meets all functional and performance requirements

**Negative**

* Backend operations must remain responsive
* Less suitable for future long-running processes without refactoring
