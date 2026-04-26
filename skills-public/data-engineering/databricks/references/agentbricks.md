# AgentBricks - Databricks AI Agent Framework

## What is AgentBricks?
AgentBricks is Databricks' native framework for building, evaluating, and deploying production AI agents on the Lakehouse. It unifies MLflow, Mosaic AI, and Unity Catalog into a single agent development lifecycle.

## Key Concepts

### Agent-as-a-Table
Agents are versioned and tracked in Unity Catalog like ML models:
- `catalog.schema.agent_name` - fully qualified agent name
- Version history, lineage, tags - all via UC
- RBAC: control who can invoke/update agents

### Supported Frameworks
- **LangChain** - chains, agents, tools
- **LlamaIndex** - RAG pipelines, query engines
- **Custom Python** - any callable that follows the MLflow pyfunc interface
- **OpenAI-compatible** - agents wrapping external LLMs

## Building an Agent

```python
import mlflow
from langchain.agents import AgentExecutor
from langchain_community.chat_models import ChatDatabricks

llm = ChatDatabricks(endpoint="databricks-meta-llama-3-1-70b-instruct")

# Define tools
from langchain.tools import tool

@tool
def query_sales(date: str) -> str:
    """Query sales data for a given date."""
    df = spark.sql(f"SELECT sum(revenue) FROM catalog.sales.fact_sales WHERE date = '{date}'")
    return str(df.collect()[0][0])

# Build agent
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sales analytics assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, [query_sales], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[query_sales])

# Log with MLflow
mlflow.set_registry_uri("databricks-uc")
with mlflow.start_run():
    mlflow.langchain.log_model(
        agent_executor,
        artifact_path="agent",
        registered_model_name="catalog.schema.sales_agent"
    )
```

## Agent Evaluation

```python
import mlflow

eval_data = [
    {"inputs": {"input": "What was revenue on 2024-01-15?"}, 
     "expected_response": "Revenue was $1.2M"},
]

with mlflow.start_run():
    results = mlflow.evaluate(
        "models:/catalog.schema.sales_agent/1",
        data=eval_data,
        model_type="databricks-agent",  # enables built-in metrics
    )

# Built-in metrics:
# - answer_relevance (0-5)
# - groundedness (0-5)
# - safety (pass/fail)
# - latency (ms)
print(results.metrics)
```

## Deploying an Agent

```python
from databricks.agents import deploy

# Deploy to Model Serving endpoint
deployment = deploy(
    model_name="catalog.schema.sales_agent",
    version=1,
    scale_to_zero=True,      # serverless scaling
    environment_vars={"DATABRICKS_HOST": "{{secrets/scope/host}}"}
)

print(deployment.endpoint_url)
# -> https://<workspace>.databricks.com/serving-endpoints/sales_agent/invocations
```

## Querying a Deployed Agent

```python
import requests

response = requests.post(
    f"{DATABRICKS_HOST}/serving-endpoints/sales_agent/invocations",
    headers={"Authorization": f"Bearer {token}"},
    json={"inputs": [{"input": "What was revenue yesterday?"}]}
)
print(response.json())
```

## AgentBricks + Unity Catalog Tools
Agents can use UC functions as tools natively:

```python
from databricks.agents.tools import UCFunctionToolkit

# UC function becomes a tool automatically
toolkit = UCFunctionToolkit(
    warehouse_id="abc123",
    function_names=["catalog.schema.get_revenue", "catalog.schema.get_top_customers"]
)

agent = create_tool_calling_agent(llm, toolkit.get_tools(), prompt)
```

## Best Practices
- Always log agents via MLflow for traceability
- Use UC-governed tools to keep data access auditable
- Evaluate before deploying - use `mlflow.evaluate` with `databricks-agent` model type
- Enable `scale_to_zero=True` for dev/staging endpoints
- Use Agent Monitoring (via Inference Tables) to track production quality
