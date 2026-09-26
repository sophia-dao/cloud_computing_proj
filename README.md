# Cloud Computing Project

```mermaid
gantt
    title Cloud Computing Project Timeline
    dateFormat YYYY-MM-DD

    section Deadlines
    Project Proposal — Due Sep 4              :milestone, proposal, 2026-09-04, 0d
    Project Midpoint Evaluation — Due Oct 16  :milestone, midpoint, 2026-10-16, 0d
    Final Documentation & Presentation — Due Nov 13          :milestone, documentation, 2026-11-13, 0d
```

# Recipe Suggestion App

## Overview

The Recipe Suggestion App is a cloud-based web application that helps users decide what to cook based on ingredients they already have.

Users can maintain a personal inventory of available ingredients and receive recipe suggestions that make use of those ingredients. Recommendations can also consider dietary preferences, allergies, cuisine preferences, and other user-defined filters.

The project aims to help users save time and money while reducing unnecessary food waste.

## Target Users

The primary target users are college students and individuals who want convenient and affordable meal ideas without spending significant time deciding what to cook or purchasing additional ingredients.

## Core Features

The application is planned to support:

* User account creation and authentication.
* Personalized user dashboard and logged-in experience.
* User profile, preferences, and allergy management.
* Personal ingredient inventory.
* Recipe recommendations based on available ingredients.
* Recipe search and filtering.
* Recipe display and cooking instructions.
* Manual recipe creation.
* Recipe reviews and ratings.
* Shopping list recommendations based on missing ingredients.
* Dietary, allergy, cuisine, vegan, halal, and similar filters.
* Recipe cost indicators.
* AI-generated recipes.
* AI recipe assistant/chatbot.
* Recipe scanning and ingredient extraction.
* Interface customization.
* Administrative account functionality.
* Contact and customer support functionality.

Some advanced features may be implemented after completion of the project's core functionality.

## High-Level Architecture

The application will use a cloud-based client-server architecture.

```text
User
  │
  ▼
Web Frontend
  │
  ▼
Backend REST API
  │
  ├── Authentication
  ├── User Management
  ├── Recipe Management
  ├── Ingredient Inventory
  ├── Recommendation System
  ├── Reviews
  ├── Shopping Lists
  └── AI Services
          │
          ▼
      Data Storage
```

The application will be deployed using Amazon Web Services (AWS).

## Technology Stack

| Component       | Technology                             |
| --------------- | -------------------------------------- |
| Cloud Platform  | AWS                                    |
| Backend         | Python                                 |
| Backend Design  | Object-Oriented / Layered Architecture |
| API             | REST                                   |
| Database        | Relational Database                    |
| Version Control | Git / GitHub                           |
| Frontend        | TBD                                    |
| Authentication  | TBD                                    |
| AI Integration  | TBD                                    |

Specific frameworks and AWS services will be selected during the system design process.

## Design Principles

The project will follow several core software design principles:

* **Object-Oriented Design:** Backend components will use clear domain objects and service classes.
* **Separation of Concerns:** Presentation, business logic, data access, and infrastructure will remain separated.
* **Modularity:** Major application functionality will be divided into independent modules.
* **Scalability:** Components should be designed so they can be expanded as application requirements grow.
* **Security:** Authentication, authorization, input validation, and secure credential management will be considered throughout development.
* **Cloud-Native Design:** AWS services will be used where appropriate to support deployment, storage, scalability, monitoring, and other application requirements.

## Project Documentation

Detailed technical documentation is maintained separately from this README:

```text
docs/
├── requirements.md
├── system-design.md
├── database-design.md
├── api-design.md
└── aws-architecture.md
```

The main README provides a high-level overview of the project, while the documents under `docs/` contain implementation-level requirements and design decisions.

## Project Structure

The planned repository structure is:

```text
recipe-app/
├── README.md
├── docs/
├── backend/
├── frontend/
├── infrastructure/
└── tests/
```

The structure may evolve as the system architecture and technology stack are finalized.
