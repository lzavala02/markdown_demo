# Technology Stack Decision Records (TDR)

This document records the key **technology stack decisions** made for the **Campus Event Hub** system. Each decision follows a consistent decision record format and aligns with the project’s assumptions, scope, and architectural goals.

---

## TDR 001 — Backend Framework

**Title:** Use a Lightweight Web Framework (e.g., Django / Flask / Express)

**Status:** Accepted

### Context

The backend must support form submission, validation, approval workflows, and event search. The system is maintained by a small team and should be easy to develop, test, and maintain.

### Decision

Use a **lightweight, well-established web framework** to implement the backend API and server-side logic.

### Alternatives Considered

* **Full enterprise frameworks** — provide extensive features but add unnecessary complexity for the system’s scale.

### Consequences

**Positive**

* Faster development and onboarding
* Large ecosystem and community support
* Sufficient structure without excessive overhead

**Negative**

* Fewer built-in features compared to enterprise frameworks
* Some functionality may require third-party libraries

---

## TDR 002 — Frontend Technology

**Title:** Server-Rendered Pages or Simple SPA

**Status:** Accepted

### Context

The system is primarily used through browsers and does not require complex client-side interactions or real-time updates. Development simplicity is a priority.

### Decision

Use **server-rendered HTML** or a **simple single-page application (SPA)** using standard web technologies.

### Alternatives Considered

* **Complex client-side frameworks** — offer rich interactivity but increase development and maintenance effort.

### Consequences

**Positive**

* Simpler frontend architecture
* Lower learning curve for developers
* Easier integration with backend logic

**Negative**

* Less dynamic user experience
* Limited client-side interactivity compared to advanced SPAs

---

## TDR 003 — Database Technology

**Title:** Relational Database (SQL)

**Status:** Accepted

### Context

The system manages structured data such as events, users, and statuses. Strong consistency and reliable querying are required.

### Decision

Use a **relational SQL database** (e.g., PostgreSQL or MySQL) as the primary data store.

### Alternatives Considered

* **NoSQL databases** — offer flexibility but are unnecessary for the structured data and relationships involved.

### Consequences

**Positive**

* Strong consistency and data integrity
* Powerful querying for filtering and searching events
* Mature tooling and operational support

**Negative**

* Schema changes require migrations
* Less flexible for unstructured data

---

## TDR 004 — Authentication & Authorization

**Title:** Simple Role-Based Access Control

**Status:** Accepted

### Context

The system supports a limited set of roles (students, organizers, administrators). Complex permission systems are out of scope.

### Decision

Implement **simple role-based access control** using the chosen backend framework’s built-in authentication features.

### Alternatives Considered

* **Advanced identity and access management systems** — unnecessary complexity for a small internal system.

### Consequences

**Positive**

* Easy to implement and maintain
* Meets all access control requirements
* Minimal configuration overhead

**Negative**

* Limited flexibility for future complex permission needs
* May require refactoring if roles significantly expand

---

## TDR 005 — Deployment & Hosting Platform

**Title:** Cloud-Based Managed Hosting

**Status:** Accepted

### Context

Cloud hosting is available, but operational resources and budget are limited. The system does not require high availability or auto-scaling.

### Decision

Deploy the application using **cloud-based managed hosting** (e.g., a managed VM or platform-as-a-service offering).

### Alternatives Considered

* **On-premise hosting** — requires more maintenance and operational effort.

### Consequences

**Positive**

* Reduced infrastructure management burden
* Easier deployment and updates
* Scales adequately for expected usage

**Negative**

* Ongoing hosting costs
* Some dependence on cloud provider services

---

## Summary

These technology stack decisions prioritize simplicity, maintainability, and cost-effectiveness, while fully supporting the functional and architectural requirements of the Campus Event Hub system.
