# Payments Analytics Engineering

An analytics engineering portfolio project inspired by real-world payment analytics challenges.

The project focuses on designing a scalable and reliable data architecture for analyzing payment requests, transactions, and different payment flows.

All data is synthetic, and the project is being developed incrementally.

## Tech Stack

- **Python** — Synthetic data generation
- **Google BigQuery** — Cloud data warehouse
- **dbt Platform** — Data transformations, modeling, and testing
- **SQL** — Data transformation and business logic
- **Git & GitHub** — Version control and development workflow

## Planned Data Architecture

1. **Raw Layer** — Synthetic operational data loaded into BigQuery.
2. **Staging Layer** — Data standardization, type casting, and consistent naming conventions.
3. **Intermediate Layer** — Business logic, relationships, and payment lifecycle transformations.
4. **Marts Layer** — Analytics-ready models for payment requests, transactions, and payment-flow usage.

## Key Modeling Challenges

- Modeling multiple payment flows, including invoices and POS.
- Defining consistent grains across payment requests, payments, and related entities.
- Supporting partial payments and payment status changes.
- Preventing double counting across related payment flows.
- Managing data dependencies and downstream transformations.
- Implementing data quality tests and incremental processing.

## Development Status

**In progress**

The repository currently contains the project specification, initial dbt project structure, and development setup.

Synthetic data generation, transformation models, and automated tests are planned for the next development stages.

## Future Enhancements

- Advanced incremental processing and lifecycle handling
- FX conversion, taxes, and tips
- Additional payment scenarios and edge cases
- Extended data quality and reconciliation tests

## Data Privacy

All datasets are fully synthetic. No proprietary company data or production code is used.