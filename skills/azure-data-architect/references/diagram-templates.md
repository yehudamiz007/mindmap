# Diagram Templates - Azure Data Pipelines

## How to Render These Diagrams
- **GitHub** - paste in any .md file, renders automatically
- **VS Code** - install "Markdown Preview Mermaid Support" extension
- **Notion** - /mermaid block
- **Mermaid Live** - https://mermaid.live (paste and share)
- **draw.io** - import Mermaid via Extras → Edit Diagram

---

## Template 1: Classic Batch Pipeline (ADF + Databricks)

```mermaid
flowchart LR
    subgraph src["📥 Data Sources"]
        SQL["🗄️ Azure SQL\n/ SQL Server"]
        API["🌐 REST API\n/ SaaS"]
        FILE["📁 SFTP\n/ SharePoint"]
    end

    subgraph ingestion["⚙️ Ingestion Layer"]
        ADF["Azure Data\nFactory"]
    end

    subgraph lake["🏔️ ADLS Gen2 - Data Lake"]
        direction TB
        BRZ["🥉 Bronze\nRaw / Immutable"]
        SLV["🥈 Silver\nClean / Validated"]
        GLD["🥇 Gold\nBusiness-Ready"]
        BRZ --> SLV --> GLD
    end

    subgraph compute["⚡ Compute"]
        DB["Databricks\nSpark + dbt"]
    end

    subgraph serve["📊 Serving"]
        PBI["Power BI"]
        DBSQL["Databricks SQL\n/ Genie"]
    end

    SQL & API & FILE --> ADF
    ADF -->|"Copy Activity"| BRZ
    BRZ -->|"Trigger"| DB
    DB --> SLV & GLD
    GLD --> PBI & DBSQL

    style BRZ fill:#cd7f32,color:#fff
    style SLV fill:#c0c0c0,color:#000
    style GLD fill:#ffd700,color:#000
```

---

## Template 2: Real-Time Streaming Pipeline

```mermaid
flowchart LR
    subgraph sources["📡 Streaming Sources"]
        IOT["IoT Devices"]
        APP["App Events\n(clickstream)"]
        CDC["CDC\n(Debezium)"]
    end

    EH["⚡ Azure Event Hubs\n(Kafka-compatible)"]

    subgraph stream["🌊 Stream Processing"]
        DLT["Databricks\nDelta Live Tables"]
        ASA["Azure Stream\nAnalytics"]
    end

    subgraph outputs["📤 Outputs"]
        DELTA["Delta Lake\n(Silver/Gold)"]
        COSMOS["Cosmos DB\n(low-latency)"]
        PBI_RT["Power BI\nStreaming"]
        ALERT["Azure Monitor\n/ Alerts"]
    end

    IOT & APP & CDC --> EH
    EH --> DLT & ASA
    DLT --> DELTA
    ASA --> COSMOS & PBI_RT & ALERT

    style EH fill:#0078d4,color:#fff
    style DLT fill:#ff6b35,color:#fff
```

---

## Template 3: Lambda Architecture (Batch + Speed)

```mermaid
flowchart TD
    SRC["Data Sources"]

    subgraph batch["🐢 Batch Layer"]
        ADF["ADF\nDaily Ingest"]
        DB_BATCH["Databricks\nBatch Processing"]
    end

    subgraph speed["⚡ Speed Layer"]
        EH["Event Hubs"]
        DLT["DLT Streaming"]
    end

    subgraph serving["📊 Serving Layer"]
        GOLD_B["Gold Delta\n(batch)"]
        GOLD_S["Gold Delta\n(streaming)"]
        PBI["Power BI\n(merged view)"]
    end

    SRC --> ADF
    SRC --> EH
    ADF --> DB_BATCH --> GOLD_B
    EH --> DLT --> GOLD_S
    GOLD_B & GOLD_S --> PBI
```

---

## Template 4: Microsoft Fabric End-to-End

```mermaid
flowchart TD
    subgraph ext["External Sources"]
        SRC1["SaaS APIs"]
        SRC2["On-Prem DB"]
        SRC3["Files / Blobs"]
    end

    subgraph fabric["Microsoft Fabric Workspace"]
        subgraph ingestion["Ingestion"]
            DFG2["Dataflows Gen2\n(low-code ETL)"]
            PIPE["Data Pipelines\n(ADF-like)"]
        end

        OL["☁️ OneLake\nUnified Delta Storage"]

        subgraph processing["Processing"]
            LH["Lakehouse\n(Bronze/Silver)"]
            NB["Notebooks\n(Spark / Python)"]
            WH["Warehouse\n(SQL endpoint)"]
        end

        subgraph analytics["Analytics"]
            SM["Semantic Model\n(Power BI)"]
            PBI["📊 Power BI Reports"]
            GENIE["Copilot / AI Skills"]
        end
    end

    SRC1 & SRC2 & SRC3 --> DFG2 & PIPE
    DFG2 & PIPE --> OL
    OL --> LH --> NB --> OL
    OL --> WH --> SM --> PBI
    SM --> GENIE

    style OL fill:#0078d4,color:#fff
    style fabric fill:#f0f4ff,color:#000
```

---

## Template 5: Multi-Region / HA Architecture

```mermaid
flowchart TB
    subgraph primary["🌍 Primary Region (West Europe)"]
        ADF_P["ADF Primary"]
        DB_P["Databricks\nPrimary"]
        ADLS_P["ADLS Gen2\nPrimary"]
    end

    subgraph secondary["🌎 Secondary Region (North Europe)"]
        DB_S["Databricks\nSecondary"]
        ADLS_S["ADLS Gen2\n(GRS Replica)"]
    end

    subgraph govern["🔐 Global Governance"]
        UC["Unity Catalog"]
        KV["Key Vault"]
        PURVIEW["Microsoft Purview"]
    end

    subgraph serve["📊 Global Serving"]
        PBI["Power BI\n(Premium)"]
        APIM["API Management"]
    end

    ADF_P --> ADLS_P --> DB_P
    ADLS_P -->|"GRS Replication"| ADLS_S
    ADLS_S --> DB_S
    DB_P & DB_S --> UC
    UC --> PBI & APIM
    KV --> DB_P & DB_S
    PURVIEW --> UC
```

---

## Template 6: Data Mesh Architecture

```mermaid
flowchart TB
    subgraph platform["🏗️ Data Platform Team"]
        UC["Unity Catalog\n(Federated Governance)"]
        INFRA["IaC Templates\n(Terraform/Bicep)"]
        PURVIEW["Microsoft Purview"]
    end

    subgraph sales_domain["📦 Sales Domain"]
        SALES_LH["Sales Lakehouse"]
        SALES_GOLD["Sales Data Product\n(orders, revenue)"]
    end

    subgraph marketing_domain["📦 Marketing Domain"]
        MKT_LH["Marketing Lakehouse"]
        MKT_GOLD["Marketing Data Product\n(campaigns, leads)"]
    end

    subgraph finance_domain["📦 Finance Domain"]
        FIN_LH["Finance Lakehouse"]
        FIN_GOLD["Finance Data Product\n(P&L, costs)"]
    end

    subgraph consumers["👥 Consumers"]
        BI["Power BI\nCross-domain"]
        DS["Data Science\nTeam"]
        EXT["External\n(Delta Sharing)"]
    end

    UC --> SALES_LH & MKT_LH & FIN_LH
    SALES_LH --> SALES_GOLD
    MKT_LH --> MKT_GOLD
    FIN_LH --> FIN_GOLD
    SALES_GOLD & MKT_GOLD & FIN_GOLD --> UC
    UC --> BI & DS & EXT
    PURVIEW --> UC
    INFRA --> SALES_LH & MKT_LH & FIN_LH

    style UC fill:#0078d4,color:#fff
    style platform fill:#e8f4fd,color:#000
```

---

## ASCII Fallback (for WhatsApp / plain text)

```
┌─────────────────────────────────────────────────────────────┐
│                    AZURE DATA PIPELINE                       │
├───────────┬──────────────┬───────────────┬──────────────────┤
│  SOURCES  │  INGESTION   │   DATA LAKE   │    SERVING       │
│           │              │               │                  │
│ SQL Server│              │  🥉 BRONZE    │                  │
│ REST APIs ├─► ADF ───────►  Raw Data    │                  │
│ Files     │              │               │  Power BI        │
│           │  Event Hubs  │  🥈 SILVER   │  Databricks SQL  │
│ IoT/Apps  ├─────────────►  Cleaned      │  API Layer       │
│           │              │               │                  │
│           │  Databricks  │  🥇 GOLD     │                  │
│           │  (Spark/dbt) │  Aggregated  │                  │
└───────────┴──────────────┴───────────────┴──────────────────┘
                Unity Catalog (Governance) across all layers
```
