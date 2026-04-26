# Databricks AI Dev Kit

## What is the AI Dev Kit?
The Databricks AI Dev Kit is an SDK + CLI toolset for building, testing, and deploying AI/ML applications on Databricks. It enables local development with live workspace connectivity, standardizes AI project structure, and integrates with Databricks Asset Bundles (DABs) for CI/CD.

## Installation

```bash
pip install databricks-ai-devkit
# or with extras
pip install databricks-ai-devkit[langchain,llama-index]
```

## CLI Commands

```bash
# Initialize a new AI project
databricks-ai init my-agent-project
# Creates: src/, tests/, databricks.yml, prompts/, .env.example

# Run locally (connects to live Databricks workspace)
databricks-ai run --profile my_profile

# Run tests
databricks-ai test

# Deploy via DABs
databricks bundle deploy --target dev
databricks bundle deploy --target prod
```

## Project Structure

```
my-agent-project/
├── databricks.yml           # DAB bundle config
├── src/
│   ├── agent.py             # Main agent logic
│   ├── tools.py             # Tool definitions
│   └── config.py            # Config/env vars
├── prompts/
│   ├── system.jinja2        # System prompt template
│   └── user.jinja2          # User prompt template
├── tests/
│   ├── test_agent.py        # Unit tests
│   └── eval_dataset.json    # Evaluation dataset
├── notebooks/
│   └── explore.ipynb        # Dev notebook
└── .env.example
```

## Local Development with Hot-Reload

```python
# src/agent.py
from databricks_ai_devkit import AgentBase, tool, prompt_template
from databricks_ai_devkit.connections import get_spark, get_workspace_client

class SalesAgent(AgentBase):
    @prompt_template("prompts/system.jinja2")
    def system_prompt(self, context: dict) -> str:
        pass

    @tool(description="Query sales data for a given date range")
    def get_sales(self, start_date: str, end_date: str) -> dict:
        spark = get_spark()  # connects to workspace Spark in dev, cluster in prod
        df = spark.sql(f"""
            SELECT date, sum(revenue) as revenue
            FROM catalog.sales.fact_sales
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY date
        """)
        return df.toPandas().to_dict(orient="records")

    def run(self, user_input: str) -> str:
        # Agent logic here
        ...
```

## Prompt Management

```python
# prompts/system.jinja2
You are a sales analytics assistant with access to real-time data.
Today is {{ current_date }}.
Available data ranges: {{ min_date }} to {{ max_date }}.
Always cite the data source in your response.

# Load and version prompts
from databricks_ai_devkit.prompts import PromptRegistry

registry = PromptRegistry(catalog="my_catalog", schema="ai_assets")
registry.register("sales_system_prompt", "prompts/system.jinja2", version="1.0")

# Retrieve specific version
prompt = registry.get("sales_system_prompt", version="1.0")
```

## Testing Framework

```python
# tests/test_agent.py
from databricks_ai_devkit.testing import AgentTestCase
from src.agent import SalesAgent

class TestSalesAgent(AgentTestCase):
    agent_class = SalesAgent

    def test_get_sales_returns_data(self):
        result = self.agent.get_sales("2024-01-01", "2024-01-31")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_handles_empty_date_range(self):
        result = self.agent.get_sales("2099-01-01", "2099-01-31")
        self.assertEqual(result, [])

    def test_end_to_end(self):
        response = self.agent.run("What was total revenue in January 2024?")
        self.assertIn("revenue", response.lower())
```

## Evaluation Dataset Format

```json
// tests/eval_dataset.json
[
  {
    "input": "What was total revenue in January 2024?",
    "expected_output": "Revenue in January 2024 was approximately $1.2M",
    "metadata": {"category": "revenue_query"}
  },
  {
    "input": "Compare Q1 vs Q2 2024 sales",
    "expected_output": "Q1 was $3.5M, Q2 was $4.1M - a 17% increase",
    "metadata": {"category": "comparison"}
  }
]
```

## Databricks Asset Bundles (DABs) Config

```yaml
# databricks.yml
bundle:
  name: sales-agent

variables:
  catalog:
    default: dev_catalog
  model_endpoint:
    default: databricks-meta-llama-3-1-70b-instruct

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: dev_catalog

  prod:
    mode: production
    variables:
      catalog: prod_catalog

resources:
  model_serving_endpoints:
    sales_agent_endpoint:
      config:
        name: sales-agent-${bundle.target}
        served_entities:
          - entity_name: ${var.catalog}.ai_assets.sales_agent
            entity_version: 1
            scale_to_zero_enabled: true

  jobs:
    agent_eval_job:
      name: "Sales Agent Evaluation"
      tasks:
        - task_key: evaluate
          notebook_task:
            notebook_path: notebooks/evaluate_agent.ipynb
      schedule:
        quartz_cron_expression: "0 0 9 * * ?"
        timezone_id: "Asia/Jerusalem"
```

## VS Code Integration

Install the **Databricks extension** for VS Code:
- Run notebooks locally with remote Spark
- Browse Unity Catalog from the sidebar
- Sync files to workspace automatically
- Debug jobs and DLT pipelines

```bash
# Configure workspace connection
databricks configure --profile my_profile
# Enter: host, token
```

## Best Practices
- Use `databricks-ai init` to start every new AI project - standard structure matters for DABs
- Store prompts as files (not hardcoded strings) - enables versioning and A/B testing
- Write unit tests with mock Spark for speed, integration tests against dev workspace
- Use `bundle deploy --target dev` frequently, `prod` only from CI/CD pipeline
- Pin model endpoint versions in `databricks.yml` - never use floating `latest` in prod
- Use `PromptRegistry` for production prompts - enables rollback without code deploy
