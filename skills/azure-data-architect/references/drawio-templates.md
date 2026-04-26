# draw.io Templates for Azure Data Pipelines

## How to Use
1. Go to https://app.diagrams.net (or open draw.io desktop)
2. File → New → select "Blank"
3. Extras → Edit Diagram (Ctrl+Shift+X)
4. Paste the XML below → OK
5. Ctrl+Shift+H to fit diagram to screen

Or import directly: File → Import From → Device → paste XML as .xml file

---

## Template 1: Classic Medallion Pipeline (ADF + Databricks)

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Title -->
    <mxCell id="title" value="Azure Data Pipeline - Medallion Architecture" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;fontColor=#0078D4;" vertex="1" parent="1">
      <mxGeometry x="200" y="20" width="760" height="40" as="geometry" />
    </mxCell>

    <!-- SOURCES GROUP -->
    <mxCell id="g_src" value="Data Sources" style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="20" y="80" width="160" height="300" as="geometry" />
    </mxCell>
    <mxCell id="sql" value="🗄️ Azure SQL" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="g_src">
      <mxGeometry x="15" y="50" width="130" height="50" as="geometry" />
    </mxCell>
    <mxCell id="api" value="🌐 REST API" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="g_src">
      <mxGeometry x="15" y="120" width="130" height="50" as="geometry" />
    </mxCell>
    <mxCell id="files" value="📁 Files / SFTP" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="g_src">
      <mxGeometry x="15" y="190" width="130" height="50" as="geometry" />
    </mxCell>

    <!-- ADF -->
    <mxCell id="adf" value="⚙️ Azure Data Factory" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E6F3FF;strokeColor=#0078D4;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="230" y="190" width="160" height="70" as="geometry" />
    </mxCell>

    <!-- BRONZE -->
    <mxCell id="bronze" value="🥉 BRONZE&#xa;Raw / Immutable" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#cd7f32;strokeColor=#8B4513;fontColor=#ffffff;fontStyle=1;fontSize=13;" vertex="1" parent="1">
      <mxGeometry x="460" y="80" width="160" height="80" as="geometry" />
    </mxCell>

    <!-- SILVER -->
    <mxCell id="silver" value="🥈 SILVER&#xa;Cleaned / Validated" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#C0C0C0;strokeColor=#808080;fontColor=#000000;fontStyle=1;fontSize=13;" vertex="1" parent="1">
      <mxGeometry x="460" y="215" width="160" height="80" as="geometry" />
    </mxCell>

    <!-- GOLD -->
    <mxCell id="gold" value="🥇 GOLD&#xa;Business-Ready" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFD700;strokeColor=#DAA520;fontColor=#000000;fontStyle=1;fontSize=13;" vertex="1" parent="1">
      <mxGeometry x="460" y="350" width="160" height="80" as="geometry" />
    </mxCell>

    <!-- DATABRICKS -->
    <mxCell id="db" value="⚡ Databricks&#xa;Spark + dbt" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF6B35;strokeColor=#cc4400;fontColor=#ffffff;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="340" y="215" width="100" height="80" as="geometry" />
    </mxCell>

    <!-- SERVING GROUP -->
    <mxCell id="g_serve" value="Serving Layer" style="swimlane;startSize=30;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="690" y="80" width="160" height="350" as="geometry" />
    </mxCell>
    <mxCell id="pbi" value="📊 Power BI" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F2C811;strokeColor=#D4A800;fontColor=#000000;fontSize=11;" vertex="1" parent="g_serve">
      <mxGeometry x="15" y="50" width="130" height="50" as="geometry" />
    </mxCell>
    <mxCell id="dbsql" value="🔍 Databricks SQL" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF6B35;strokeColor=#cc4400;fontColor=#ffffff;fontSize=11;" vertex="1" parent="g_serve">
      <mxGeometry x="15" y="130" width="130" height="50" as="geometry" />
    </mxCell>
    <mxCell id="api_out" value="🔗 API Layer" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="g_serve">
      <mxGeometry x="15" y="210" width="130" height="50" as="geometry" />
    </mxCell>

    <!-- UNITY CATALOG BANNER -->
    <mxCell id="uc" value="🔐 Unity Catalog — Governance, Lineage, Access Control" style="text;html=1;strokeColor=#0078D4;fillColor=#E6F3FF;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=1;fontSize=11;fontStyle=2;" vertex="1" parent="1">
      <mxGeometry x="230" y="490" width="620" height="35" as="geometry" />
    </mxCell>

    <!-- EDGES -->
    <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="sql" target="adf" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="api" target="adf" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="files" target="adf" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e4" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="adf" target="bronze" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e5" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="bronze" target="db" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e6" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="db" target="silver" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e7" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="silver" target="gold" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e8" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="gold" target="pbi" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e9" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="gold" target="dbsql" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e10" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="gold" target="api_out" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>

    <!-- Watermark -->
    <mxCell id="wm" value="Architecture by Yehuda Mizrahi | Azure Data Architect" style="text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=bottom;whiteSpace=wrap;rounded=0;fontSize=9;fontColor=#999999;" vertex="1" parent="1">
      <mxGeometry x="700" y="540" width="450" height="20" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Template 2: Streaming Pipeline (Event Hubs + DLT)

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <mxCell id="title" value="Azure Real-Time Streaming Pipeline" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;fontColor=#0078D4;" vertex="1" parent="1">
      <mxGeometry x="150" y="20" width="860" height="40" as="geometry" />
    </mxCell>

    <!-- Sources -->
    <mxCell id="iot" value="📡 IoT Devices" style="shape=mxgraph.azure2.iot_hub;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="30" y="100" width="120" height="60" as="geometry" />
    </mxCell>
    <mxCell id="app" value="📱 App Events" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="30" y="200" width="120" height="60" as="geometry" />
    </mxCell>
    <mxCell id="cdc" value="🔄 CDC (Debezium)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="30" y="300" width="120" height="60" as="geometry" />
    </mxCell>

    <!-- Event Hubs -->
    <mxCell id="eh" value="⚡ Azure Event Hubs&#xa;(Kafka-compatible)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontStyle=1;fontSize=13;" vertex="1" parent="1">
      <mxGeometry x="220" y="190" width="160" height="80" as="geometry" />
    </mxCell>

    <!-- DLT -->
    <mxCell id="dlt" value="🔥 Delta Live Tables&#xa;(Databricks)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF6B35;strokeColor=#cc4400;fontColor=#ffffff;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="460" y="130" width="160" height="80" as="geometry" />
    </mxCell>

    <!-- ASA -->
    <mxCell id="asa" value="📊 Stream Analytics&#xa;(SQL on stream)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#5C2D91;strokeColor=#3a1a66;fontColor=#ffffff;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="460" y="260" width="160" height="80" as="geometry" />
    </mxCell>

    <!-- Outputs -->
    <mxCell id="delta_out" value="🥇 Delta Lake&#xa;Silver / Gold" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFD700;strokeColor=#DAA520;fontColor=#000000;fontStyle=1;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="700" y="100" width="150" height="70" as="geometry" />
    </mxCell>
    <mxCell id="cosmos" value="🌐 Cosmos DB&#xa;Low-latency" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078D4;strokeColor=#005a9e;fontColor=#ffffff;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="700" y="220" width="150" height="70" as="geometry" />
    </mxCell>
    <mxCell id="pbi_rt" value="📊 Power BI&#xa;Streaming Dataset" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F2C811;strokeColor=#D4A800;fontColor=#000000;fontSize=12;" vertex="1" parent="1">
      <mxGeometry x="700" y="340" width="150" height="70" as="geometry" />
    </mxCell>

    <!-- Edges -->
    <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="iot" target="eh" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="app" target="eh" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="cdc" target="eh" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e4" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="eh" target="dlt" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e5" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="eh" target="asa" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e6" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="dlt" target="delta_out" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e7" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="asa" target="cosmos" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>
    <mxCell id="e8" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="asa" target="pbi_rt" parent="1"><mxGeometry relative="1" as="geometry" /></mxCell>

    <mxCell id="wm" value="Architecture by Yehuda Mizrahi | Azure Data Architect" style="text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=bottom;whiteSpace=wrap;rounded=0;fontSize=9;fontColor=#999999;" vertex="1" parent="1">
      <mxGeometry x="600" y="460" width="550" height="20" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```

---

## Tips for draw.io Azure Diagrams

### Use Azure Icon Library
1. In draw.io: View → Shapes → Search "Azure"
2. Enable: **Azure**, **Azure 2** shape libraries
3. Icons for ADF, ADLS, Databricks, Event Hubs, Power BI are all available

### Color Palette (Azure Official)
- Azure Blue: `#0078D4`
- Databricks Orange: `#FF6B35`
- Bronze: `#CD7F32`
- Silver: `#C0C0C0`
- Gold: `#FFD700`
- Power BI Yellow: `#F2C811`
- Synapse Purple: `#5C2D91`
- Event Hubs Teal: `#00B4D8`
- Success Green: `#107C10`
- Warning: `#FFB900`

### Swimlane Pattern (for layered architectures)
Use **swimlanes** (Insert → Container → Swimlane) to group:
- Sources | Ingestion | Data Lake (Bronze/Silver/Gold) | Serving

### Export Options
- **PNG/SVG** - for presentations and docs
- **PDF** - for printing
- **XML** - for sharing/version control (commit the .drawio file to git)
- **Confluence** - draw.io is native in Confluence Cloud

### Pro Tips
- Use `Ctrl+Shift+F` to format selected shapes
- Duplicate a template shape with `Ctrl+D`
- Align shapes: Edit → Select All → right-click → Align
- Auto-layout: View → Arrange → Layout → Tree or Flow
