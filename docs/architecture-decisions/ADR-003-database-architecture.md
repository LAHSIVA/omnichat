# ADR-003: Database Architecture

## Status

Accepted

## Context

OmniChat requires persistent storage for users, authentication data,
conversations, messages, documents, and document metadata.

The application also requires a vector store for semantic retrieval
as part of the RAG subsystem.

## Options Considered

### SQLite

SQLite is simple and requires no external database server. It is
appropriate for small prototypes and local experimentation.

It was rejected as the primary database because OmniChat is intended
to be a multi-user application that will eventually run in production.

### MongoDB

MongoDB provides flexible document-oriented storage.

It was not selected because the core application data has strong
relational characteristics:

User → Conversations → Messages

and:

User → Documents

### PostgreSQL

PostgreSQL provides mature relational data management, transactions,
constraints, indexing, and strong Django integration.

## Decision

PostgreSQL will be the primary transactional database for OmniChat.

Django ORM will be used as the application's database abstraction
layer.

A separate vector store will be used for document embeddings and
semantic retrieval rather than storing vector-search data in the
primary relational database.

## Data Responsibilities

PostgreSQL:

- Users
- Authentication-related data
- Conversations
- Messages
- Documents
- Document metadata
- RAG processing metadata

Vector store:

- Document chunks
- Embeddings
- Retrieval metadata required by the RAG pipeline

## Deployment

PostgreSQL will run in a Docker container during local development
and will use persistent storage.

The database will communicate with the Django backend through an
internal network and will not be exposed publicly in production.

## Consequences

### Positive

- Strong relational data model
- Mature transaction support
- Excellent Django integration
- Clear separation between transactional and vector workloads
- Reproducible local development through Docker

### Negative

- Requires database infrastructure unlike SQLite
- Requires separate vector storage for RAG

## Future Considerations

If application scale or workload characteristics change, database
architecture can be revisited. The application should avoid coupling
business logic directly to database-specific behavior where practical.