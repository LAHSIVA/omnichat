# ADR-001: Application Architecture

## Status

Accepted

## Context

OmniChat needs to provide two major capabilities:

1. AI-powered conversational chat with conversation history.
2. Document-based question answering using Retrieval-Augmented Generation (RAG).

The application must be maintainable, testable, secure, and suitable for deployment while remaining appropriately simple for the scope of the assignment.

## Decision

We will implement OmniChat as a modular monolithic application.

The application will contain separate Django modules for:

- Accounts
- Chat
- Documents
- RAG
- AI integration

React will provide the frontend and Django REST Framework will provide the backend API.

## Alternatives Considered

### Microservices

Rejected initially because the project does not currently require independent deployment, independent scaling, or separate service ownership.

### Single large Django application module

Rejected because mixing authentication, chat, document processing, RAG, and AI provider logic would make the code harder to maintain and test.

### Modular Monolith

Selected because it provides clear domain boundaries while avoiding unnecessary distributed-system complexity.

## Consequences

### Positive

- Simple deployment model
- Clear separation of responsibilities
- Easier local development
- Easier testing
- Easier future extraction of individual components if required

### Negative

- All modules initially share the same application deployment
- Some scaling decisions may eventually require extracting components into separate services

## Review Criteria

We will reconsider this decision if the application develops requirements for independent scaling, independent deployment, or strong service boundaries.