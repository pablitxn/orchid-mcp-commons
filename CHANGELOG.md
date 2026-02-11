# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-11

### Added
- Initial release of `orchid-skills-commons`
- Configuration system with Pydantic models and environment variable loading
- Database providers: PostgreSQL, SQLite, MongoDB, Redis, RabbitMQ, Qdrant
- Blob storage: S3-compatible (MinIO), Cloudflare R2, multi-bucket router
- Observability: structured logging, Prometheus metrics, OpenTelemetry tracing, Langfuse integration
- HTTP middleware for FastAPI and aiohttp (correlation, error handling)
- Resource lifecycle management with `ResourceManager`
- Health check aggregation
- Vector store contract and pgvector support
- Domain error hierarchies for Redis (`CacheError`, `CacheAuthError`, `CacheTransientError`, `CacheOperationError`) and RabbitMQ (`BrokerError`, `BrokerAuthError`, `BrokerTransientError`, `BrokerOperationError`)
- Error translation in MongoDB, Redis, and RabbitMQ providers matching existing patterns in Postgres/SQLite/Qdrant
- Thread-safety locks for global singletons (`_DEFAULT_LANGFUSE_CLIENT`, `_DEFAULT_RECORDER`, `_OBSERVABILITY_HANDLE`, `_RESOURCE_FACTORIES`)
- Debug-level logging for previously silenced exceptions in `langfuse.py` and `http.py`
- `http` optional extra with `starlette` and `aiohttp` dependencies
- `postgres` optional extra as alias for `sql`
- `pip-audit` to dev dependencies for security scanning
- Integration tests for Redis, MongoDB, and RabbitMQ using testcontainers
- Python 3.12/3.13 matrix testing in CI
- `mypy` type checking step in CI pipeline
- Security audit job in CI pipeline
- Automated CI triggers on push/PR to `main`

### Changed
- `ObservableMixin._resource_name` is now `ClassVar[str]` for correct dataclass compatibility
- `S3BlobStorage` uses `_resource_name_override` for per-instance metric resource names

### Fixed
- 21 mypy errors: `SecretStr` wrapping in `from_env()`, `ObservableMixin._resource_name` ClassVar conflict, starlette stub resolution
- 8 ruff lint errors (import ordering, `__all__` sorting, `zip()` strict parameter)
