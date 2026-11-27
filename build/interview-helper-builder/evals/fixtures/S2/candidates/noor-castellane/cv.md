# Noor Castellane

Data Platform Engineer - Remote (EU)

## Summary

Data engineer with eight years of batch and streaming work, the last four on
a lakehouse platform used by twelve analytics and ML teams.

## Skills

- **Languages:** Python, SQL, Scala
- **Streaming:** Kafka, Flink, Debezium
- **Lakehouse:** Apache Iceberg on S3, Trino, dbt
- **Orchestration:** Airflow, Dagster
- **Infra:** Kubernetes, Terraform, AWS

## Experience

### Data Platform Engineer - Larchmont Freight

04.2021 - present

- Built the shipment-events streaming pipeline (Kafka, Flink) handling about
  40,000 events per second at peak.
- Migrated the warehouse from nightly batch loads to an Iceberg lakehouse;
  owned table layout, partitioning, and compaction.
- Introduced data contracts between producing services and the platform,
  with schema checks in CI.
- Moved orchestration from Airflow to Dagster for 300+ assets.
- Cut monthly compute spend by about 30% through file compaction and query
  tuning in Trino.
- Primary on-call for the platform; wrote the incident runbooks.
- Added column-level lineage from dbt and Flink jobs into the data catalog, so
  consumers can trace a dashboard figure back to its source topic.

### Selected project: late-arriving events

Shipment scans from partner depots arrive up to three days late. Designed the
watermarking and correction flow: Flink emits provisional aggregates, a daily
Iceberg merge job rewrites affected partitions, and downstream dbt models
rebuild only the touched days. Reduced manual finance corrections from weekly
to rare exceptions.

### Data Engineer - Oxbeam Media

09.2017 - 03.2021

- ETL for advertising analytics (Spark, Redshift).
- Built dbt models and tests for the finance reporting layer.
- Replaced hand-written backfill scripts with parameterized Airflow DAGs.

## Education

BSc Software Engineering, 2017
