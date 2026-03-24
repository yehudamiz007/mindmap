# Databricks Genie Reference

## What is Genie?

Genie is Databricks' AI/BI natural language interface - users ask questions in plain language and Genie generates SQL, runs it, and returns results. Genie Spaces are curated environments with context about specific datasets.

## Genie Spaces

A Genie Space is a configured environment containing:
- One or more SQL Warehouses (required)
- Curated tables/views from Unity Catalog
- Custom instructions (system prompt for the AI)
- Verified answers (example Q&A pairs)
- Sample questions

### Creating a Genie Space

1. Go to **Databricks UI > Genie** (sidebar)
2. Click **New Genie Space**
3. Configure:
   - **Name** - descriptive name for the space
   - **SQL Warehouse** - select a running serverless/pro warehouse
   - **Tables** - add tables from Unity Catalog (catalog.schema.table)
   - **Instructions** - custom context and rules for the AI
   - **Sample questions** - seed questions to guide users

### Instructions Best Practices

```
# Business Context
This space answers questions about e-commerce sales data.
Orders table contains all customer purchases since 2020.

# Terminology
- "Revenue" = sum of (amount * quantity) excluding refunds
- "Active customer" = customer with purchase in last 90 days
- "Conversion rate" = orders / sessions * 100

# Rules
- Always filter deleted_at IS NULL for orders
- Default date range is last 30 days unless specified
- Round monetary values to 2 decimal places
```

### Verified Answers

Pre-written SQL for common questions Genie should always answer correctly:

```
Question: "What was total revenue last month?"
SQL:
SELECT
  date_trunc('month', order_date) as month,
  SUM(amount * quantity) as revenue
FROM my_catalog.sales.orders
WHERE order_date >= dateadd(month, -1, date_trunc('month', current_date()))
  AND order_date < date_trunc('month', current_date())
  AND deleted_at IS NULL
GROUP BY 1
```

## Using Genie via API

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# List Genie spaces
spaces = w.genie.list_spaces()

# Ask a question (async)
conversation = w.genie.start_conversation(
    space_id="your-space-id",
    content="What were the top 10 products by revenue last quarter?"
)

# Get result
result = w.genie.get_message_query_result(
    space_id="your-space-id",
    conversation_id=conversation.conversation_id,
    message_id=conversation.message.id
)
print(result.statement_response.result)
```

## AI/BI Dashboards

Genie powers AI/BI Dashboards - shareable, embeddable dashboards with natural language.

### Creating Dashboards

1. **Databricks UI > Dashboards > Create Dashboard**
2. Add visualizations (bar, line, scatter, table, counter, map)
3. Connect to SQL Warehouse
4. Publish and share

### Dashboard as Code (via Databricks Asset Bundles)

```yaml
# databricks.yml
bundle:
  name: my_dashboards

resources:
  dashboards:
    sales_dashboard:
      display_name: "Sales Overview"
      warehouse_id: "your-warehouse-id"
      file_path: ./dashboards/sales_overview.lvdash.json
```

## Genie Tips

- Genie requires a **SQL Warehouse** (not all-purpose cluster)
- Serverless warehouse = fastest cold start for Genie
- Add **column descriptions** in Unity Catalog - Genie uses them for better SQL generation
- Add **table descriptions** in Unity Catalog schema
- Use **verified answers** for KPIs that must be exact
- Test Genie with adversarial questions before sharing with business users
- Genie supports **follow-up questions** in conversation thread

## Adding Column Descriptions (helps Genie)

```sql
ALTER TABLE my_catalog.sales.orders
ALTER COLUMN customer_id COMMENT 'Unique identifier linking to customers table';

ALTER TABLE my_catalog.sales.orders
ALTER COLUMN amount COMMENT 'Order total in USD, excluding tax and shipping';

-- Table comment
COMMENT ON TABLE my_catalog.sales.orders IS
'Transactional orders table. One row per order. Excludes draft/abandoned carts.';
```
