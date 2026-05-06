# Config & Secrets Management - eToro

## Golden Rules

1. **Zero secrets in code** - no hardcoded tokens, passwords, URLs
2. **Zero secrets in git** - .env files are gitignored always
3. **Databricks Secrets** for all sensitive values in production
4. **Pydantic Settings** for all config, including non-sensitive
5. **Environment-based config** - dev/prod differ by env vars only

## Config Pattern (pydantic-settings)

```python
# src/etoro_trading/config.py
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: str = Field(default="dev", pattern="^(dev|staging|prod)$")

    # Databricks
    databricks_catalog: str = Field(default="dev")
    databricks_host: str

    # eToro API
    etoro_api_base_url: str = Field(default="https://public-api.etoro.com/api/v1")
    etoro_api_key: str  # from Databricks secret

    # Pipeline config (non-sensitive)
    batch_size: int = Field(default=10_000, gt=0)
    max_retry_attempts: int = Field(default=3, ge=1, le=10)
    rate_limit_wait_seconds: float = Field(default=15.0)

# Single instance - import this everywhere
settings = Settings()
```

## .env Example (gitignored)

```bash
# .env.example (commit this)
ENVIRONMENT=dev
DATABRICKS_CATALOG=dev
DATABRICKS_HOST=https://adb-xxx.azuredatabricks.net
ETORO_API_KEY=<get-from-databricks-secrets>
BATCH_SIZE=10000
```

```bash
# .gitignore (always include)
.env
.env.*
!.env.example
```

## Databricks Secrets (Production)

```python
# ✅ Read secrets from Databricks secret scope
def get_secret(scope: str, key: str) -> str:
    """Read from Databricks secret scope."""
    return dbutils.secrets.get(scope=scope, key=key)  # type: ignore[name-defined]

# ✅ In config - load from secrets scope in Databricks environment
class Settings(BaseSettings):
    @classmethod
    def from_databricks_secrets(cls, scope: str = "etoro") -> "Settings":
        return cls(
            etoro_api_key=dbutils.secrets.get(scope, "etoro-api-key"),
            databricks_host=dbutils.secrets.get(scope, "databricks-host"),
        )
```

```bash
# Set secrets via Databricks CLI
databricks secrets create-scope etoro
databricks secrets put-secret etoro etoro-api-key --string-value "your-key"
```

## Config in Databricks Workflows

```yaml
# bundle.yml - pass config as job parameters, not hardcoded
tasks:
  - task_key: ingest
    python_wheel_task:
      parameters:
        - "--env=prod"
        - "--catalog=prod"
    environment_key: etoro_env
environments:
  - environment_key: etoro_env
    spec:
      client: "1"
      dependencies:
        - etoro-trading-pipeline
```

## What Goes Where

| Config Type | Where to store |
|------------|---------------|
| API keys, tokens | Databricks Secrets |
| Passwords | Databricks Secrets |
| DB connection strings | Databricks Secrets |
| Feature flags | Environment variable |
| Table names, catalogs | Environment variable |
| Batch sizes, timeouts | Environment variable with defaults |
| Cluster config | bundle.yml |
| Non-sensitive URLs | Environment variable |

## Config Validation at Startup

```python
# ✅ Validate config at startup - fail fast
def validate_settings(settings: Settings) -> None:
    if settings.environment == "prod" and settings.databricks_catalog == "dev":
        raise ConfigurationError("Production environment cannot use dev catalog")
    if not settings.etoro_api_key:
        raise ConfigurationError("ETORO_API_KEY is required")

# In job entry point
settings = Settings()
validate_settings(settings)
```
