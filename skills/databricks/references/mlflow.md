# MLflow Reference

## Experiment Tracking

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier

# Set experiment (creates if not exists)
mlflow.set_experiment("/my-project/experiments/churn-model")

# Auto-logging (recommended)
mlflow.sklearn.autolog()

with mlflow.start_run(run_name="rf-baseline"):
    # Log params
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 5)

    # Train
    model = RandomForestClassifier(n_estimators=100, max_depth=5)
    model.fit(X_train, y_train)

    # Log metrics
    mlflow.log_metric("accuracy", 0.92)
    mlflow.log_metric("f1", 0.89)
    mlflow.log_metric("auc", 0.95)

    # Log multiple metrics over time
    for epoch, loss in enumerate(losses):
        mlflow.log_metric("train_loss", loss, step=epoch)

    # Log artifacts
    mlflow.log_artifact("feature_importance.png")
    mlflow.log_dict({"config": {"lr": 0.01}}, "config.json")

    # Log model
    mlflow.sklearn.log_model(model, "model",
                              input_example=X_train[:5],
                              registered_model_name="churn-classifier")
```

## Model Registry

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Register model
result = mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="churn-classifier"
)

# Add description and tags
client.update_registered_model(
    name="churn-classifier",
    description="XGBoost churn prediction model"
)

client.set_model_version_tag(
    name="churn-classifier",
    version=result.version,
    key="validated",
    value="true"
)

# Transition to alias (new API)
client.set_registered_model_alias(
    name="churn-classifier",
    alias="champion",
    version=result.version
)

# Load by alias
model = mlflow.sklearn.load_model("models:/churn-classifier@champion")

# Legacy stage transition (deprecated but still used)
client.transition_model_version_stage(
    name="churn-classifier",
    version=1,
    stage="Production"  # Staging, Production, Archived
)
```

## Model Serving (Databricks)

```python
# Deploy model endpoint via SDK
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedModelInput

w = WorkspaceClient()

endpoint = w.serving_endpoints.create(
    name="churn-classifier-endpoint",
    config=EndpointCoreConfigInput(
        served_models=[
            ServedModelInput(
                model_name="churn-classifier",
                model_version="1",
                workload_size="Small",  # Small, Medium, Large
                scale_to_zero_enabled=True
            )
        ]
    )
)

# Query endpoint
import requests
response = requests.post(
    f"{workspace_url}/serving-endpoints/churn-classifier-endpoint/invocations",
    headers={"Authorization": f"Bearer {token}"},
    json={"dataframe_records": [{"feature1": 1.0, "feature2": "value"}]}
)
```

## Feature Engineering with Databricks

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Create feature table
fe.create_table(
    name="my_catalog.features.customer_features",
    primary_keys=["customer_id"],
    timestamp_keys=["updated_at"],
    df=features_df,
    description="Customer behavioral features"
)

# Write features
fe.write_table(
    name="my_catalog.features.customer_features",
    df=new_features_df,
    mode="merge"
)

# Log model with feature lookups
from databricks.feature_engineering import FeatureLookup

fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=fe.create_training_set(
        df=training_df,
        feature_lookups=[
            FeatureLookup(
                table_name="my_catalog.features.customer_features",
                feature_names=["avg_purchase", "days_since_last_order"],
                lookup_key="customer_id"
            )
        ],
        label="churned"
    )
)
```

## MLflow + Spark (PySpark)

```python
# Log Spark model
mlflow.spark.log_model(spark_model, "spark-model")

# Distributed hyperparameter tuning with Hyperopt
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
from pyspark.ml.tuning import CrossValidator

def objective(params):
    with mlflow.start_run(nested=True):
        mlflow.log_params(params)
        # train and evaluate
        score = evaluate_model(params)
        mlflow.log_metric("score", score)
        return {"loss": -score, "status": STATUS_OK}

best = fmin(
    fn=objective,
    space={"lr": hp.loguniform("lr", -5, 0),
           "depth": hp.choice("depth", [3, 5, 7])},
    algo=tpe.suggest,
    max_evals=20,
    trials=SparkTrials(parallelism=4)
)
```

## Querying MLflow via SQL

```sql
-- List experiments
SELECT * FROM mlflow.experiments;

-- List runs
SELECT run_id, experiment_id, status, start_time, metrics.accuracy
FROM mlflow.runs
WHERE experiment_id = 'your-experiment-id'
ORDER BY metrics.accuracy DESC
LIMIT 10;
```
