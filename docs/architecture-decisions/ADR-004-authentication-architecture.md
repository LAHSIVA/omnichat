# ADR-004: Authentication Architecture

## Status

Accepted

## Context

OmniChat is a React single-page application communicating with a
Django REST API.

The application must authenticate users and ensure that protected
resources such as conversations and documents are associated with the
correct authenticated user.

## Options Considered

### Django Session Authentication

Django session authentication is mature and well integrated with
Django. It is particularly suitable for traditional server-rendered
Django applications.

It was not selected as the primary authentication mechanism because
OmniChat uses React as a separate frontend application communicating
with Django through a REST API.

### JWT Authentication

JSON Web Tokens allow the API to authenticate requests using bearer
tokens without maintaining server-side session state for each access
request.

JWT is appropriate for the React + Django REST architecture, provided
token lifetime, refresh behavior, storage, and revocation are handled
carefully.

## Decision

OmniChat will use JSON Web Token authentication through
Django REST Framework Simple JWT.

The system will use:

- Short-lived access tokens
- Longer-lived refresh tokens
- Bearer authentication for protected API requests
- Refresh-token rotation
- Refresh-token blacklisting

The frontend token-storage strategy will be designed separately,
with the goal of avoiding persistent storage of long-lived
credentials in browser JavaScript-accessible storage.

## Initial Authentication Endpoints

POST /api/auth/register/
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/auth/me/

## Consequences

### Positive

- Appropriate separation between React and Django
- Stateless access-token verification
- Short-lived access tokens reduce exposure if stolen
- Refresh-token rotation improves security
- Blacklisting provides a mechanism for refresh-token revocation

### Negative

- JWT introduces additional security considerations compared with
  Django sessions
- Token refresh and logout require deliberate implementation
- Browser storage and CSRF considerations must be handled carefully

## Future Considerations

Authentication will be reviewed before production deployment,
including HTTPS, secure cookie configuration where applicable,
CORS policy, refresh-token rotation, token revocation, rate limiting,
and brute-force protection.