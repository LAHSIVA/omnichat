# ADR-002: Backend Framework and API Architecture

## Status

Accepted

## Context

OmniChat requires a backend capable of supporting:

- User authentication
- Chat conversations
- Message persistence
- Document management
- RAG workflows
- AI provider integration
- REST APIs for the React frontend
- Automated testing

The learning curriculum explicitly includes Django, Django REST Framework, authentication, and Django testing.

## Options Considered

### FastAPI

FastAPI provides excellent API development, async support, and automatic OpenAPI documentation.

However, using FastAPI would not align with the Django-focused requirements of the assignment.

### Django with Django REST Framework

Django provides a mature web framework, ORM, authentication system, security middleware, migrations, and a large ecosystem.

Django REST Framework provides the API layer required for communication with the React frontend.

## Decision

OmniChat will use Django as the backend framework and Django REST Framework as the API framework.

The backend will expose RESTful APIs to the React frontend.

The application will use REST for normal request/response operations. Streaming AI responses will be evaluated separately and are expected to use Server-Sent Events (SSE).

## Consequences

### Positive

- Aligns with requirements
- Mature authentication and security ecosystem
- Integrated ORM and migrations
- Clear API boundary between React and Django
- Strong testing support
- Familiarity with Django is directly relevant to the assignment

### Negative

- More framework complexity than a lightweight API framework
- Some API operations require more configuration than FastAPI

## Future Considerations

FastAPI or other services could be introduced later if a specific scalability or workload requirement justifies them. The initial architecture will remain a modular Django monolith.