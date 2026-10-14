# Payments Analytics Engineering

An end-to-end Analytics Engineering portfolio project built with **Python, Google BigQuery, dbt, SQL, and Git**.

The project uses synthetic payment data to demonstrate how complex operational payment flows can be transformed into a consistent, tested analytical model.

## Project Overview

Payment requests can originate from different business activities, including meetings, events, products, services, and shopping carts.

Although these flows ultimately represent payment activity, they do not necessarily follow the same operational lifecycle or data structure.

The goal of this project is to create a **unified analytical model** that supports consistent analysis across payment flows while preserving the business context of each transaction.

The project focuses on:

- Modeling different payment request lifecycles.
- Resolving relationships between payment requests and business entities.
- Handling carts containing multiple items.
- Representing legacy payments without an original payment request.
- Preventing double counting when expanding requests into multiple analytical rows.
- Implementing data quality tests that validate both technical integrity and business logic.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Deterministic synthetic data generation |
| Google BigQuery | Data warehouse and SQL execution |
| dbt | Data transformations, modeling, testing, and lineage |
| SQL | Business logic and analytical transformations |
| Git & GitHub | Version control and development workflow |

## Data Architecture

```text
Python Synthetic Data Generator
              |
              v
        CSV Datasets
              |
              v
       BigQuery Raw
              |
              v
        dbt Staging
   Standardization and typing
              |
              v
      dbt Intermediate
   Payment flow business logic
              |
              v
         dbt Marts
   Unified analytical model
              |
              v
     Analytics / Reporting
```

### 1. Raw Layer

The Python generator creates reproducible synthetic data representing businesses, clients, meetings, events, products, services, carts, order items, payment requests, and payments.

The generated CSV files are loaded into BigQuery's `raw` dataset.

### 2. Staging Layer

Staging models provide a standardized interface to the source data.

They handle:

- Data type casting.
- Consistent naming conventions.
- Standardization of status and currency values.
- Basic data quality validation.

The staging layer preserves the original source grain and avoids introducing complex business logic.

### 3. Intermediate Layer

Intermediate models implement the business rules required to interpret the different payment lifecycles.

**Direct payment requests**

Resolves requests associated with meetings, events, products, and services.

The logic accounts for entities absorbed into carts, preventing them from being represented incorrectly as independent direct requests.

**Cart-based requests**

Resolves payment requests associated with carts and expands them into their underlying order items.

This preserves item-level business context while retaining the relationship to the original payment request.

**Legacy payments**

Handles payments that do not reference an existing payment request by creating synthetic analytical request identifiers.

These records remain distinguishable from original payment requests.

### 4. Marts Layer

The main analytical model is:

`fct_payment_request_entities`

Its grain is **one row per payment request and associated business entity or cart item**.

This enables analysis at the entity level while preserving request-level information.

A single payment request may contain multiple items. Therefore, simply summing its requested amount across all rows would result in double counting.

The model includes dedicated measures such as:

- `request_amount_once`
- `request_count_once`
- `item_amount`

These support analysis at different aggregation levels while avoiding inflated request-level metrics.

The model also distinguishes payment flows such as direct requests, POS, and legacy payments.

## Data Quality and Testing

Data quality is an important part of the project.

### Generic dbt Tests

Schema-based tests validate fundamental data integrity, including:

- `unique`
- `not_null`
- `relationships`
- `accepted_values`

### Custom Singular Tests

Custom SQL assertions validate business rules that cannot be fully covered by generic tests.

Examples include:

- Preventing double counting of payment request amounts.
- Validating cart item amounts against request-level amounts.
- Detecting incorrect representation of entities absorbed into carts.
- Checking consistency between source requests and the analytical model.

A singular test passes when its SQL query returns **zero rows**.

These tests help ensure that transformations preserve the intended business meaning, not just technical correctness.

## Project Structure

```text
payments-analytics-engineering/
├── data/                     # Generated synthetic CSV datasets
├── docs/                     # Project specification and documentation
├── src/
│   └── payments_generator/   # Python synthetic data generator
├── models/
│   ├── staging/              # Standardized source models
│   ├── intermediate/         # Payment flow business logic
│   └── marts/                # Final analytical models
├── tests/                    # Python and dbt SQL tests
├── dbt_project.yml
├── pyproject.toml
└── README.md
```

## Running the dbt Project

The dbt models are configured to read source tables from the BigQuery `raw` dataset.

With a compatible dbt environment and BigQuery connection configured, the project can be built using:

```bash
dbt build
```

To build individual layers:

```bash
dbt build --select path:models/staging
dbt build --select path:models/intermediate
dbt build --select path:models/marts
```

To run the custom singular tests:

```bash
dbt test --select test_type:singular
```

The repository also includes the Python source code and sample synthetic CSV datasets used for the project.

## Key Modeling Decisions

**Business grain before implementation**

The analytical grain was defined around payment requests and their associated entities, rather than assuming that one payment request always represents one business item.

**Lifecycle-aware transformations**

Different operational flows require different transformation logic. The model explicitly distinguishes direct requests, cart-based requests, and legacy payments.

**No double counting**

Request-level metrics are handled separately from item-level metrics to support reliable aggregation.

**Reusable transformation layers**

The project separates source standardization, business logic, and analytical consumption into staging, intermediate, and marts layers.

**Testing business assumptions**

Custom data quality tests validate important modeling decisions and help detect regressions in downstream analytics.

## Scope and Future Improvements

This project is a focused portfolio implementation using synthetic data rather than a production payment platform.

Potential future extensions include:

- Incremental models and incremental loads.
- More complex payment status transitions.
- Partial payments and refunds.
- Invoice-specific payment lifecycles.
- FX conversion and multi-currency reporting.
- Automated CI checks for dbt changes.
- Production-style orchestration and monitoring.

These are future improvements and are not presented as completed functionality.

## Project Motivation

This project was developed to apply Analytics Engineering practices in a hands-on environment, combining prior experience in payment-domain data modeling, SQL transformations, and BI engineering with practical dbt development.

The emphasis is on **understanding the business problem, designing reliable data models, managing dependencies, and validating analytical correctness**.