# Assumptions & Scope

This document outlines the assumptions and scope for the **Campus Event Hub** project. These constraints guide architectural decisions and help keep the system aligned with institutional needs and available resources.

---

## Assumptions

* The system is an **internal university application**, not a public commercial product.
* **Expected users** include:

  * Hundreds of students browsing and searching for events
  * Dozens of student organization leaders or departments submitting events
  * A small number of staff administrators reviewing and approving events
* **Concurrent usage** is low to moderate.
* There are **no strict real-time or high-availability requirements**.
* The system is developed and maintained by a **small engineering team (2–4 engineers)**.
* **Cloud hosting is available**, but budget and operational resources are limited.

---

## Out of Scope

The following items are explicitly out of scope for the initial version of the system:

* Native mobile applications (iOS or Android)
* Public APIs for external partners or third-party integrations
* Real-time chat, messaging, or live streaming features
* Complex role-based permission systems
* Advanced analytics, personalization, or recommendation engines

---

These assumptions and scope limitations are intended to keep the system focused, maintainable, and appropriate for its intended use within the university environment.
