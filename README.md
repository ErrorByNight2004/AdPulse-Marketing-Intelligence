# AdPulse — Marketing Intelligence & Attribution Analytics

**Transforming advertising interaction data into marketing intelligence through campaign analytics, customer journey analysis and multi-touch attribution modelling.**

AdPulse is a marketing analytics project designed to analyse digital advertising performance, understand customer conversion journeys and compare different attribution models.

The project processes large-scale advertising interaction data using Python, DuckDB and SQL, prepares analytical datasets in Parquet format, and presents insights through interactive Power BI dashboards.

---

## 1. Project Overview

Digital advertising campaigns generate millions of impressions, clicks and conversion interactions. Understanding how users interact with campaigns before converting is essential for evaluating marketing performance.

AdPulse explores these interactions through campaign-level analysis, customer journey analysis and attribution modelling.

The project transforms large-scale advertising data into structured insights that support marketing performance evaluation and data-driven business decisions.

## 2. Project Objectives

- Analyse advertising impressions, clicks and conversions.
- Evaluate campaign-level performance.
- Understand customer interaction and conversion journeys.
- Measure customer touchpoints before conversion.
- Compare First Touch, Last Touch, Linear and Time Decay attribution models.
- Identify high-performing campaigns and important patterns.
- Communicate analytical findings through interactive Power BI dashboards.

## 3. Dataset Description

**Dataset:** Criteo Attribution Modeling Dataset

The dataset contains advertising interaction records, including:

- User identifiers
- Campaign identifiers
- Timestamps
- Impression and click indicators
- Conversion information
- Attribution indicators
- Cost-related fields
- Anonymised categorical variables

### Dataset Scale

| Metric | Value |
|---|---:|
| Total impression records | 16,468,027 |
| Distinct users | 6,142,256 |
| Campaigns | 675 |
| Click events | 5,947,563 |
| Conversion-associated impression records | 806,196 |
| Distinct conversion IDs | 435,810 |
| User-conversion journeys | 438,730 |
| Multi-touchpoint journeys | 139,762 |

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and analytical workflows |
| DuckDB | Large-scale analytical data processing |
| SQL | Data transformation and aggregation |
| Parquet | Efficient analytical data storage |
| Power BI | Interactive dashboards and reporting |
| DAX | Dashboard measures and calculations |

## 5. Project Architecture

The project follows a structured data analytics workflow:

```text
Raw Criteo Dataset
        |
        v
Python + DuckDB
        |
        v
Data Processing
        |
        v
SQL Transformations
        |
        v
Processed Parquet Files
        |
        v
Campaign & Journey Analysis
        |
        v
Attribution Modelling
        |
        v
Power BI Dashboards
        |
        v
Marketing Insights
```

### Workflow

1. **Data Ingestion:** Loaded the large raw advertising dataset.
2. **Data Processing:** Used Python and DuckDB to process the data efficiently.
3. **Data Transformation:** Applied SQL transformations and prepared analytical tables.
4. **Data Storage:** Exported processed datasets into Parquet format.
5. **Journey Analysis:** Examined user interactions and conversion touchpoints.
6. **Attribution Modelling:** Implemented four attribution approaches.
7. **Visualization:** Developed interactive Power BI dashboards.

## 6. Attribution Modelling

AdPulse compares four attribution approaches:

- **First Touch:** Assigns conversion credit to the earliest interaction.
- **Last Touch:** Assigns conversion credit to the latest interaction.
- **Linear:** Distributes credit equally across all touchpoints.
- **Time Decay:** Gives greater credit to interactions closer to conversion, using a project-defined seven-day half-life.

Each attribution model distributes approximately 438,730 units of journey credit.

## 7. Power BI Dashboard

The Power BI reporting solution contains four analytical pages:

| Dashboard Page | Description |
|---|---|
| Marketing Performance Overview | High-level advertising performance indicators |
| Campaign Performance Analysis | Campaign-level comparisons and performance patterns |
| Customer Journey Analysis | Customer touchpoints and conversion journey behaviour |
| Attribution Model Analysis | Comparison of four attribution approaches |

## 8. Key Findings

- The dataset contains more than 16.4 million impression records across 675 campaigns.
- Approximately 5.95 million click events were recorded.
- The overall click-through rate is approximately 36.12%.
- The average conversion journey contains approximately 1.84 touchpoints.
- The longest observed journey contains 164 touchpoints.
- There are 139,762 multi-touchpoint journeys.
- Campaign **10341182** received the highest attribution credit, with 21,877 units, representing approximately 4.99% of total journey credit.
- Campaign-level rankings remained consistent across the four attribution models because each conversion-associated journey contains interactions from only one distinct campaign.

## 9. Business Relevance

AdPulse demonstrates how advertising interaction data can be used to:

- Evaluate campaign performance.
- Understand customer conversion behaviour.
- Examine customer touchpoints.
- Compare alternative attribution approaches.
- Identify campaigns receiving higher conversion credit.
- Present analytical findings through business intelligence dashboards.

## 10. Analytical Limitations

- Attribution credit represents an analytical allocation, not proof of causality.
- The dataset does not provide verified revenue figures; therefore, ROI and ROAS are not calculated.
- Cost-related fields are treated as dataset-provided measures, not independently verified advertising expenditure.
- The categorical fields cat1–cat9 are anonymised and are not assigned unsupported business meanings.
- Each conversion-associated journey contains interactions from only one distinct campaign, limiting cross-campaign attribution analysis.
- Time Decay uses a project-defined seven-day half-life.

## 11. Project Deliverables

Explore the complete AdPulse project outputs below.

| Deliverable | Description |
|---|---|
| **Power BI Dashboard** | Interactive marketing intelligence and attribution dashboard |
| **Project Presentation** | Project overview, methodology, analysis and key findings |
| **Project Documentation** | Detailed project methodology, dataset information and analytical findings |

**Files are available in the `AdPulse_Deliverables` folder within this repository.**

- [Open Power BI Dashboard](AdPulse_Deliverables/AdPulse_Marketing_Intelligence.pbix)
- [View Project Presentation](AdPulse_Deliverables/AdPulse_Project_Presentation.pptx)
- [Read Project Documentation](AdPulse_Deliverables/AdPulse_Project_Documentation.docx)

## 12. Repository Structure

```text
AdPulse/
│
├── README.md
├── notebooks/
├── src/
├── data/
│   ├── raw/
│   └── processed/
├── requirements.txt
│
└── AdPulse_Deliverables/
    ├── AdPulse_Marketing_Intelligence.pbix
    ├── AdPulse_Project_Presentation.pptx
    └── AdPulse_Project_Documentation.docx
```

*This is the intended structure. Adjust it to match the actual files and folders in your repository.*

## 13. Running the Project

### Prerequisites

- Python
- DuckDB
- Required Python dependencies
- Criteo Attribution Modeling Dataset
- Power BI Desktop

### Getting Started

1. Clone or download the repository.
2. Open the project folder in Visual Studio Code.
3. Install the required dependencies using the requirements file.
4. Place the source dataset in the appropriate local data directory.
5. Explore the notebooks and source scripts.
6. Open the Power BI dashboard separately using Power BI Desktop.

**Note:** The original raw dataset and large intermediate files are not included in the GitHub repository.

## 14. Conclusion

AdPulse demonstrates how large-scale advertising interaction data can be transformed into structured marketing intelligence through data processing, SQL analysis, customer journey analysis, attribution modelling and business intelligence visualization.

By combining analytical workflows with interactive dashboards, the project provides a structured approach to understanding advertising campaign performance and customer conversion behaviour.

---

## Connect

**Nishanth S Reddy**
- GitHub: https://github.com/ErrorByNight2004

---

**Project:** AdPulse — Marketing Intelligence & Attribution Analytics