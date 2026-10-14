# Payments Analytics Engineering — Project Specification



**Status:** Authoritative implementation specification v1.0 — 2026-10-13 

**Scope:** End-to-end dbt Platform (cloud IDE and execution) + Google BigQuery analytics project using fully synthetic data, inspired by real-world payment workflows. GitHub is the source-control repository; Cursor is an optional local editor and Python generator workspace.




## v1.0 binding business clarifications — authoritative

These rules supersede any conflicting statements elsewhere in this document or in previous Cursor proposals. All data is synthetic; 2025-01-01 is an intentionally chosen simulation cutoff, not a historical claim about any real product.

### Activity classification and human-readable synthetic data

- `businesses` must include `country_code` (ISO 3166-1 alpha-2), `identity_group_code`, and `identity_group_description`. **Identity group means business activity/industry classification, not risk.** Examples: BEAUTY / Beauty & Wellness, FITNESS / Fitness & Sports, EDUCATION / Education & Tutoring, RETAIL / Retail & Shopping, EVENTS / Events & Entertainment, CONSULTING / Professional Services.
- Add stable, creative, plausible synthetic names and useful descriptions for businesses, clients, meetings, events, products, and services. Use no real customer data. Names should allow future text/name-based exploration; the generator must reproduce the same names for the same seed.
- A meeting or event is an independently identifiable booking/occurrence that can exist without payment. A product or service is a **repeatable catalog definition**, not a unique sale occurrence. The same catalog ID may be purchased repeatedly; distinguish sales by payment request or item ID, never deduplicate on product/service ID alone.

### Historical product behavior cutoff: 2025-01-01 UTC

- Before `2025-01-01T00:00:00Z`, generate legacy direct product/service selections as **payments without a source payment request** (`payment_request_id IS NULL`). The user may have selected an item from the catalog UI, but the operational payment record retained **only the selected name/description**, with no structured product_id/service_id FK. Include true ad-hoc legacy payments as well, and preserve `payment_actor`.
- On/after the cutoff, a new direct product/service purchase creates a source payment request with `entity_type='product'` or `'service'` and a real `entity_uid` FK. A request can exist unpaid. Do not retroactively backfill legacy source requests or reconstruct structured catalog FKs from text.
- The generator must include a stable source field such as `selected_item_name`/`payment_description` for legacy name-only selections, plus a source discriminator if needed to distinguish ad-hoc from name-only; the exact name must be documented in the schema. In dbt, virtual request keys for legacy payments remain namespaced, provenance-labeled, and excluded from **real request adoption** counts.

### Invoice containment and canonical request decision tree

- Invoice creation **retains** original direct meeting/event requests in `payment_requests`; they are **not hard-deleted or soft-deleted** merely because they enter an invoice. Their `request_status` and `update_at` may remain unchanged (e.g. `open`). Do not manufacture a guaranteed `replaced` transition.
- A relevant active invoice is represented by a distinct source payment request (`entity_type='invoice'`) and `order_items.type='i'` lines. Invoice line entity_type/entity_id identifies underlying meetings/events or repeatable catalog/free-form items. A meeting/event may have had a prior direct request; invoice items do not require an original request FK.
- Before processing the main request stream, prepare a set of unique meeting/event IDs appearing in `order_items.type='i'` attached to relevant active invoices. While iterating `payment_requests`, **exclude a direct meeting/event request** from the active canonical payable set when its unique meeting/event is already represented by such an invoice. Do not rely on direct request status to do this. When processing the invoice's request, **expand its invoice lines** into request-plus-item/entity rows. Preserve the original direct request in raw/staging and optionally in an audit/lineage model.
- A product/service catalog ID appearing in an invoice does **not** imply that other independent direct purchase requests for the same catalog ID should be excluded. Only unique meeting/event occurrences support that entity-level exclusion rule.
- Non-sale client portal carts (`carts.is_sale=0`) aggregate existing payment requests through `cart_items`. Their constituent requests remain in raw. Build a lookup set of constituent request IDs for valid persisted client carts; exclude those source requests from separate canonical payable counts and expand them under the cart's payment request. Apply containment rules consistently if a constituent has invoice-derived items. Preserve lineage and guard against duplicate container ownership in the generated scenarios.
- POS sale carts (`carts.is_sale=1`) resolve items through `order_items.type='s'`; affected old requests are soft-deleted according to the POS scenario. No fabricated replacement FK is required.
- Use `payment_requests` as the primary source driving the canonical request logic; **legacy payments without a source request** are an explicit additional virtual-request branch. Stage all raw records without prematurely filtering them out. Implement reusable containment/lineage sets in intermediate models; the final request/item fact determines canonical inclusion and expansion. Grain: one row per canonical request in `fct_payment_requests`; one row per canonical request plus stable item ID in `fct_payment_request_items`; one row per payment attempt in `fct_payments`.
- If invoice membership changes without an update to the original direct request, downstream incremental processing must still invalidate/recompute that direct request's active-payable state. The same applies when cart membership or payment records change. Track dependencies, not only `payment_requests.update_at`.

### Operational timestamps and payment attempts

- All operational source tables must have `create_at`, `update_at`, and nullable `delete_at`; `exchange_rates` is a reference-feed exception. `payments` must also have nullable `paid_at`.
- `payments.payment_status='paid'` requires `paid_at IS NOT NULL` and `paid_at >= create_at`; failed attempts have `paid_at IS NULL`. A successful payment may settle after its creation time. Request settlement (`unpaid` / `partially_paid` / `fully_paid`) is derived from successful payments in dbt, not assumed to be reliably synchronized in source request status.
- Direct requests may be unpaid, failed-only, partially paid, or fully paid. **Do not generate mixed failed-plus-paid attempts for the same direct request.** Multiple successful partial payments are allowed. Other flow scenarios retain their defined failed/partial behaviors.

### Deterministic CDC and validation

- Generate reproducible `batch_001` and `batch_002` (at minimum) with fixed seed, IDs, dates, sorted output, and a scenario manifest. Each batch contains newly inserted or modified rows, including tombstones; raw BigQuery tables are updated by PK-based `MERGE`. Do not precompute canonical facts in Python.
- Ensure scenario coverage for: invoice inclusion with unchanged/open direct meeting/event request; multiple independent purchases of the same product/service ID; client-cart containment; POS soft deletion; legacy name-only product/service payment before cutoff; post-cutoff typed direct request; successful payment with `paid_at` later than `create_at`; failed-only direct request; multiple successful partial payments; a new payment affecting an unchanged request; currency/tax/tip reconciliation.
- Test PK/FK integrity, source grain, timestamp order, money reconciliation, stable reruns, and expected source-side lifecycle. **Do not test the inaccurate assumption that invoice constituents always become `replaced`.**

## Platform and execution architecture (v1.0)

- **Analytics warehouse:** Google BigQuery is the only SQL warehouse and persistent data store for this project. Do not create a DuckDB database, DuckDB adapter, or local dbt Core execution path.
- **dbt development and execution:** use dbt Platform (the browser-based dbt environment) connected to BigQuery. Develop, run, test and document dbt models there. Use the BigQuery adapter supported by the dbt Platform connection; do not install or configure `dbt-duckdb`.
- **Version control:** the existing GitHub repository `ronisheffi/payments-analytics-engineering` is the source of truth. Connect it to dbt Platform after confirming access; do not create a second repository. Cursor may be used for generator code and Git commits/pushes. Synchronize/pull changes when switching between Cursor and dbt Platform; avoid concurrent conflicting edits.
- **Data generation:** a deterministic Python generator creates fully synthetic, reproducible batch files (e.g., CSV/JSON) and scenario manifests. Keep Python generator code in Git. No sensitive credentials or service-account keys may be committed.
- **Raw ingestion simulation:** create a BigQuery raw dataset and load each batch to BigQuery staging/batch tables, then apply explicit BigQuery SQL `MERGE` statements into raw current-state tables keyed by source primary key. Preserve `delete_at` tombstones and advance `update_at` for changes. The batch process may use reproducible SQL scripts plus documented BigQuery load steps; an automated Python loader is optional if credentials are configured safely. This is a *simulated* incremental ingestion feed, not a claim of a live Stitch connector.
- **dbt incremental models:** materialize appropriate intermediate/canonical models with BigQuery-compatible dbt incremental `merge`, stable `unique_key`, and dependency-aware reprocessing of impacted request IDs. Active consumption models may be filtered views or otherwise safely refreshed; never leave stale deleted or otherwise superseded records in persisted incremental outputs.
- **Dataset naming:** use separate BigQuery datasets for raw data and dbt development/analytics outputs, with configurable project/dataset names. Never hard-code an unconfirmed Google Cloud project ID, dataset name, credentials, or billing setup.
- **Prerequisites before first warehouse execution:** verify a Google Cloud project with BigQuery enabled, required permissions and billing/sandbox suitability, a working dbt Platform-to-BigQuery connection, and GitHub repository integration. These are setup checks, not assumptions that they are already complete.
- **Cost discipline:** keep synthetic tables small, use limited batch sizes, avoid unnecessary full-table scans, and document any BigQuery costs or sandbox limitations.

## Objective

Analyze the creation, usage, and outcomes of payment requests—not just payment volume. Support reliable comparisons across initiation sources, channels, aggregation mechanisms, and invoice usage without hard-coding a fixed number of payment flows.



## Modeling principles

- Preserve request lifecycle independently of payment execution: requests may exist without payments.

- Describe workflows using **atomic, testable attributes**, not one mandatory seven-value `payment_flow` classification.

- Preserve transaction-level payment facts separately from request-level and request-item-level facts.

- Support historical payments that predate the payment-request feature without altering or fabricating raw source records.

- Avoid double-counting requests or paid amounts when invoice, POS, or non-sale cart aggregates other requests.

- Explicitly distinguish requested amounts from actually paid amounts and estimated item-level allocations.

- All data and examples must be synthetic; no company names, confidential screenshots, or proprietary source data.



## Core modeling problem: inconsistent source representation and lifecycle

This is a central engineering challenge, not a simple denormalization exercise. A raw `payment_requests.entity_type='invoice'` or `'cart'` identifies the container, **not necessarily the underlying business entity being paid for**. The analytical item/entity-grain fact must resolve the actual constituent items and underlying entities, including ad-hoc items without an entity reference, while preserving the canonical payment request through which payment was collected.



Explicitly implement and test these distinct source patterns:

1. **Direct request:** request references a meeting, event, service, product or ad-hoc item; resolve its business context directly.

2. **Invoice aggregation with retained requests:** only unpaid source requests can be included; original direct payment-request rows **remain physically present** and may retain their prior status (including `open`). Do **not** assume a reliable `replaced` status transition. A new invoice payment request is created; `order_items.type='i'` stores constituent lines. Preserve invoice request ID and invoice ID on resolved lines. Resolve the underlying entity from invoice items, not from the invoice container. Avoid counting invoice-contained constituent requests as additional active payable demand. Do not assume the invoice items contain original constituent request IDs unless an explicit link exists.

3. **POS sale, persisted only upon payment:** preparing a POS basket in the UI creates **no persisted sale/cart request** and does not alter existing payment requests. The prepared POS basket cannot be saved and resumed later. **Only when a payment is executed** are the sale cart (`is_sale=1`), its new payment request, `order_items.type='s'` lines and payment persisted; any relevant pre-existing source payment requests are **logically deleted via `delete_at`** in this synthetic system; raw ingestion retains the tombstone. Resolve the underlying entities from POS lines. Detect `delete_at` updates via incremental ingestion and propagate them into incremental models; exclude logically deleted requests from active payable demand. A persisted POS sale has at least one payment, but may be partially paid. Behavior after payment cancellation/reversal is unknown and must not be invented.

4. **Legacy client cart:** initiated **only by the client in the Client Portal**. The client selects **existing payment requests only** and pays them together; new catalog products, services or free-form items without an existing request cannot be added. A new request references a non-sale cart (`is_sale=0`) linking the selected requests. Constituent source requests remain, while the payment is recorded against the cart request. Resolve underlying entities via the linked requests, preserve cart and constituent lineage, and avoid duplicating paid amounts. Do not assert an unverified persistence lifecycle for an unpaid/abandoned client cart.

5. **Historical no-request payment:** a payment without a request must map to a virtual analytical request; its actor unambiguously determines client/business legacy ad-hoc flow.



At the detailed fact grain, distinguish `canonical_payment_request_id` (the actual/virtual payable request), `source_constituent_request_id` when available, `source_container_type`, `invoice_id`/`cart_id` where applicable, `item_id`, `underlying_entity_type`, and `underlying_entity_id`. An invoice or cart must not be the sole analytical entity when it has constituent lines. For invoice requests, retained original rows may be available for audit but their linkage to invoice items is not guaranteed. For POS source requests, do not invent a source-request-to-sale-item FK; derive sale details from POS items. Ensure item-level requested amounts and allocated paid amounts reconcile to the payable request and do not multiply due to one-to-many joins.



## Source timestamps and deletion convention

Every synthetic operational raw table must include `create_at`, `update_at`, and `delete_at` (nullable). Preserve these names through staging. In **this independent synthetic design**, deletions are logical: an upstream row is retained with `delete_at` populated and `update_at` advanced. The incremental ingestion feed captures this change. No snapshot comparison or POS replacement log is required. A soft-deleted row remains available for lineage/audit, but must not count as active payable demand. `WHERE delete_at IS NULL` is valid in a full rebuild, **but not sufficient by itself in a persisted incremental mart**: changed/deleted keys must trigger a merge/tombstone or explicit removal of previously materialized active rows. Prefer retaining an `is_deleted`/`is_active_payable` marker in the incremental canonical layer, with filtered active consumption marts/views. Changes to constituents, payments and items must invalidate/recompute all affected canonical request and item allocations.



## Data pipeline and incremental strategy

- Operational source → simulated Stitch-style **incremental ingestion** (new/updated rows including deletion tombstones) → raw current-state tables → staging → intermediate → marts.

- Do **not** model or claim a full-table overwrite architecture. Use BigQuery-compatible incremental dbt `merge` with stable unique keys and dependency-aware change propagation; full refresh remains a recovery option.

- Demonstrate at least two deterministic ingestion batches: Invoice conversion with retained constituent requests that may remain unchanged/open; POS payment with original direct requests marked `delete_at`; Client Cart paid-on-creation; and updated/new payments including legacy orphans.

- Use test assertions that formerly active requests are not left as stale payable records after `delete_at` or invoice/cart containment changes. Preserve audit lineage separately.



## Source tables (initial design)

| Table | Purpose / important fields |

|---|---|

| `businesses`, `clients` | Parties and ownership: `clients.business_id` is a required FK; each client belongs to **exactly one** business (one business to many clients) |

| `meetings` | Booking status, created_by_side, is_auto_booked, requires_payment, expected_price, client and business |

| `events` | Event metadata, payment-required/automatic-booking context; attendee-level detail may be deferred |

| `products`, `services` | Catalog entities, optionally referenced by a payment request or line item |

| `payment_requests` | Request ID, business/client, `create_at`, `update_at`, `delete_at`, requested amount, currency, status, `entity_type` and `entity_uid`, `request_initiator`, creation side, `payment_link_sent` |

| `payments` | Payment ID, nullable request ID for historical payments, amount, status, method, processor, `payment_key`, `is_online`, `payment_actor` |

| `invoices` | Invoice ID, client/business, total, currency, status and `create_at`, `update_at`, `delete_at` |

| `order_items` | A **single source `type` discriminator**: invoice items (`type='i'`) vs POS sale items (`type='s'`); optional entity linkage, ad-hoc descriptions and line amounts. Design the owner FK(s) without replacing or obscuring this discriminator. |

| `carts` | Cart ID and `is_sale`: 1 for POS, 0 for legacy client-portal aggregation |

| `cart_items` | Links a non-sale cart to constituent payment requests |



The table list and exact column names are design proposals to be validated during implementation, except the required v1.0 fields and business rules explicitly specified above.



## Business rules



### Booking-triggered requests

- Each unique meeting/event may have **at most one direct payment request** at a time in the synthetic source. Product and service IDs are reusable catalog definitions: multiple independent purchase requests may legitimately reference the same product/service ID. A meeting/event can appear inside an invoice or POS sale without making its earlier direct request analytically payable again.

- A meeting or event does **not** automatically generate a payment request merely by existing.

- For meetings/events, a payment request is created when the booking is configured as requiring payment. For post-cutoff direct product/service purchases, a new payment request represents each purchase, not a unique catalog item.

- `request_initiator` may be `business`, `client`, or `system`.

- `system` is permitted **only** for automatically booked meetings/events where the configured rule creates a payment request. Enforce this with a data-quality test.



### Invoices

- An invoice may be created only from **unpaid** source requests. A request already paid cannot be rolled into a newly created invoice.

- **Invoice creation does not physically delete constituent source payment requests.** They remain in `payment_requests` and may retain their original status and timestamps. A **new, distinct payment request** is created with `entity_type='invoice'` and `entity_uid=invoice_id`.

- **Each invoice has exactly one payment request** pointing to it. Existing direct requests are not counted as additional active payable demand after inclusion in the invoice.

- Retained source requests may be audited, but do not assume a reliable direct request-to-invoice-item FK without explicitly modeling one.

- Invoice contents are represented by `order_items` with `type='i'`; items may have no underlying entity.

- **`has_paid_invoice = true` once a positive successful payment has been made toward the invoice, even if the invoice is only partially paid.** This flag identifies invoice-associated paid activity; it does **not** mean fully settled.

- An entirely unpaid invoice request has `entity_type = 'invoice'` and `has_paid_invoice = false`. Do not create a redundant `has_invoice` field when invoice association is already determinable from the canonical request or invoice lineage.

- Use the same request-level settlement metrics for invoices, POS sales, and direct requests; do not create an invoice-specific payment status.

- A payment that started on an invoice remains invoice-associated; it is not split into invoice and non-invoice portions.

- No invoice is issued retroactively for an already-paid request in this simulation.



### POS sale

- `carts.is_sale=1` denotes a POS sale. It has `order_items` with `type='s'`, including free-form items with no entity ID.

- A POS basket can be assembled in the UI but **no persisted sale/cart payment request or sale line records are created until payment execution**. The user cannot save the prepared POS basket and resume it later.

- At payment execution, persist the sale cart, its payment request, its sale order items and at least one payment together. A persisted sale is **not necessarily fully settled**; partial payment is supported at the request grain.

- Relevant earlier source payment requests are **soft-deleted via `delete_at` and retained in raw/staging**. The item fact resolves the sold entities from `order_items.type='s'`, not from deleted request rows.

- Detect deletion events through incremental updates to `delete_at` and `update_at`; exclude those rows from the active payable set while retaining them for audit.

- What happens if a POS payment is later cancelled or reversed, including whether earlier requests are restored, is **unknown**. Do not fabricate restoration rules or cancellation test cases as established behavior.

- For reproducible synthetic data, generator scenarios explicitly choose which existing requests are marked `delete_at` when POS is paid. Do not add an operational POS replacement FK or require a replacement log. Item facts resolve from `order_items.type='s'`.



### Legacy client cart

- `carts.is_sale=0` groups **existing** payment requests via `cart_items`. It is initiated **only by the client via the Client Portal**.

- The client can select multiple existing requests and pay them together. The client **cannot** add new catalog products/services or ad-hoc items without an existing request.

- A new payment request represents the cart, and actual payments link to that cart request, not the constituent requests.

- The selected constituent payment requests **remain in the source**. Avoid counting them as separate paid demand alongside the cart request.

- Unlike POS, do not assume soft deletion of constituent requests. In this synthetic system, selection alone does not persist a cart. Only successful execution of at least one payment creates the cart, its request, its cart_items and its first payment together; partial settlement is allowed.



### Historical payments without payment requests

- Some historical `payments` rows have `payment_request_id IS NULL` because the payment-request feature did not exist for those transactions.

- Preserve these rows as-is in raw/staging; **do not backfill or overwrite the source payment-request ID**.

- In the intermediate layer, derive one **virtual/analytical payment request per historical orphan payment**, using a deterministic, collision-safe namespaced key such as `legacy_payment:<payment_id>`; original requests use `request:<payment_request_id>`.

- Build a canonical request union and a payment-to-canonical-request mapping. Every payment must resolve to exactly one canonical request, whether native or virtual. Do not generate virtual requests for payments that already reference a native request.

- For virtual requests, use the payment amount and payment timestamp as clearly labeled **analytical proxies** for requested amount and request date; these are not known historical request facts. Keep source provenance (`is_virtual_request`, `request_origin='legacy_payment'`) so metrics can exclude or segment virtual requests when appropriate.

- Historical orphan payments are **legacy no-request payments**, including ad-hoc payments and historical name-only product/service selections. Their source `payment_actor` is either `client` or `business`; retain a source text label for historical product/service selections but do not invent a structured catalog FK. The analytical workflow may distinguish legacy ad-hoc versus name-only catalog selection when supported by the source description/type, while preserving actor as an independent dimension. Never infer an actual product/service ID from the name alone.

- For virtual analytical requests, set `entity_type = 'ad_hoc'` for true ad-hoc payments and use a separately documented legacy name-only classification for product/service selections, with no fabricated structured entity ID. Preserve `payment_actor` on the payment fact. Since no actual request-creation event occurred, keep `request_initiator` NULL on the virtual request rather than copying `payment_actor` into it; the derived historical flow is still known unambiguously.

- Test that every historical orphan payment has a valid `payment_actor` (`client` or `business`) and has a valid provenance classification (ad-hoc or name-only selection) and a valid actor. Keep this derivation separate from any optional labels for newer flows.

- Use a stable item identifier for virtual requests (for example a payment-derived line) when a source entity/line item is absent, and avoid multiplying amounts in item-level marts.

- Test uniqueness of canonical request IDs, one-to-one mapping for orphan payments, coverage of every payment, no double counting of paid amounts, and stable IDs across incremental reruns.

- Distinguish **real payment-request adoption metrics** from unified payment-activity metrics: virtual requests are an analytical bridge and must not be counted as real user-created requests.



### Payments and allocation

- A request can have multiple payments and be partially paid, whether it originates from an invoice, POS sale, legacy cart, or direct request.

- Compute settlement consistently at canonical payment-request grain: `successful_paid_amount` is the sum of successful positive payments, `remaining_amount = greatest(requested_amount - successful_paid_amount, 0)` (subject to an explicit overpayment policy), `is_fully_paid` when successful paid amount meets the requested amount. `payment_status` is `unpaid`, `partially_paid`, or `fully_paid`. Keep request lifecycle in a separate `request_status`.

- Every recorded payment has `payment_actor` of either `business` or `client`; requests without payments have no payment actor yet (NULL at request summary level).

- `payment_key` identifies a processor transaction; `is_online` is relevant to additional business logic. Do not assume a transaction key is globally unique across processors.

- Item-level `allocated_paid_amount` is a **proportional estimate**: successful paid amount × item requested amount / total constituent requested amount. Test reconciliation, handle zero denominators, and retain original payment amounts.

- No partial payment cancellation is assumed for the initial dataset. Refunds, reversals, invoice cancellation and POS reversal are explicitly out of scope.



## Workflow attributes and classification

Prefer independent attributes that identify each stage unambiguously:

- **At request creation:** `request_initiator`, `request_source`, `entity_type`, `entity_uid`, `is_sale` (for cart requests), `requested_amount`, `requires_payment` (for relevant booking source).

- **After request creation:** `payment_link_sent`, request lifecycle status.

- **At payment execution:** `payment_actor`, `is_online`, `payment_method`, `payment_key`, `payment_processor`, payment status and amount.

- **Derived outcomes at payment-request grain:** `successful_paid_amount`, `remaining_amount`, `payment_status` (`unpaid`, `partially_paid`, `fully_paid`), `is_partially_paid`, `is_fully_paid`, `has_paid_invoice`. Keep `request_status` (source lifecycle, not settlement) separate from settlement status.



Avoid forcing requests into a fixed list of seven flows. If a human-readable flow label is useful, derive it from the atomic attributes and permit extensibility. Because one request may have multiple payments, payment actor/channel belongs at **payment grain**; request-level rollups should use flags or explicit mixed-value logic.



## Analytical models and grains

1. `fct_payments`: one row per payment record; transaction context and execution attributes.

2. `fct_payment_requests`: one row per canonical payable request; lifecycle, requested/paid totals, invoice-paid flag, and summary attributes.

3. `fct_payment_request_items`: one row per canonical payable request **plus item/underlying entity**; includes free-form lines and proportional paid allocation. Use stable line-item IDs, not nullable entity IDs alone, as row keys.

4. Monthly/lifetime usage aggregates above detailed facts; explicitly define whether metrics count requests, items, payments, or invoices.



Source constituent requests retained for audit (invoice and client cart) should not inflate canonical payable-request counts. POS source requests remain as soft-deleted raw rows; active sale details are resolved from POS lines, not counted again from deleted direct requests. Invoice items also determine the analytical detail of invoice requests even though original requests remain.



## dbt structure (dbt Platform + BigQuery)

- `models/staging`: source cleaning, casting, status normalization, key tests. BigQuery sources must refer to configurable raw project/dataset definitions.

- `models/intermediate`: historical-payment virtual request mapping, canonical request union, request lineage, invoice/POS/cart item resolution, payment aggregation, business rules.

- `models/marts`: facts and consumption-oriented aggregates.

- `tests`: referential integrity, uniqueness at grain, historical payment coverage, deterministic legacy no-request classification and virtual-request provenance, amount reconciliation, valid actors/initiators, valid `system` booking origin, invoice paid flag, duplicate-count protections.



## Monetary model: tax, tip and FX

- Include tax and tip in the synthetic schema and calculations. Each payable item has `base_amount` and `tax_amount`; a request may have `tip_amount`. Define `requested_amount = sum(item base_amount + item tax_amount) + tip_amount` for multi-item containers. Direct requests use the same reconciliation rule with one analytical line. No discounts, fees or refunds in v1.

- Treat tax and tip as distinct components (not revenue by default); preserve gross paid, tax and tip separately. Allocate request-level tip across items proportionally to pre-tip item gross; label allocations as estimates and assign rounding residual deterministically to the final line. Reconcile all item gross amounts to the canonical request gross.

- Include daily `exchange_rates` with `rate_date`, `from_currency`, `to_currency`, `rate` and uniqueness tests. Use **USD** as reporting currency. Convert payment amounts at `payments.create_at` date and request amounts at `payment_requests.create_at` date. The rate means units of USD per 1 source-currency unit; USD→USD = 1. Use decimal-safe rounding, test missing rates and document that payment/request USD figures may differ due to FX timing.

- `exchange_rates` is a reference feed, not necessarily an operational product table; the three operational timestamps requirement does not force fake source lifecycle fields on this reference feed.



## Payment status and cart/invoice lifecycle

- Synthetic `payments.payment_status='paid'` means successful payment and counts toward `successful_paid_amount`; other values (e.g. `failed`) do not. Request settlement remains `unpaid`, `partially_paid`, `fully_paid` and is **derived** from successful payments, not copied from the transaction status.

- Invoice creation retains original source requests without requiring any status update, creates a new invoice request and invoice lines, and does not require an item→original-request FK. The original constituent requests are not separately active payable demand when included in a relevant active invoice; UI visibility is separate from physical row retention.

- Client Cart exists only when the first payment is executed; before that, selections are ephemeral and requests remain independent. POS likewise persists only when a payment is executed. Partial payment is permitted for either.



## Explicit exclusions

Refunds, chargebacks, payment reversals, invoice cancellation, POS restoration, hard-delete detection/snapshot diff, and POS replacement log are not part of v1. This is a standalone synthetic design inspired by generic payment workflows; do not reference or replicate a particular company's confidential implementation.



## Open implementation choices (non-blocking)

- Define sensible synthetic currencies, dates, tax/tip distributions, failed payments, and rounding conventions consistently in generator, SQL and tests.

- No event-attendance table required in v1. Preserve `payment_key`, `is_online` and payment processor without inventing a fixed number of workflow classes.



## Delivery plan

1. Implement the source schemas and deterministic generator with at least two incremental ingestion batches, including tombstones and status transitions, plus exchange-rate reference data.

2. Confirm BigQuery project/datasets, permissions and dbt Platform BigQuery connection; connect the existing GitHub repository. Generate deterministic synthetic files with Python, load batches into BigQuery, and use BigQuery SQL `MERGE` to incrementally upsert raw operational rows while retaining `delete_at` tombstones. Do not set up DuckDB or a separate local dbt Core project.

3. Build staging → intermediate → incremental canonical and item models → active consumption marts, with unique keys and dependency-aware recomputation.

4. Test invoice/POS/cart lifecycle, orphan virtual requests, actor constraints, tax/tip/FX arithmetic, allocation, no double counting, and deletion/status-change propagation across batches.

5. Build monthly/lifetime usage aggregates, dbt Platform documentation/lineage, reproducible README with BigQuery setup and batch instructions, and Git branch/commit/PR demonstration.


## Migration note and v1.0 precedence

This v1.0 document supersedes v0.9 and earlier versions. It retains the BigQuery + dbt Platform architecture and prior monetary/modeling requirements, while explicitly revising invoice status assumptions, repeatable product/service purchases, and legacy pre-2025 name-only purchases. Where older text or code disagrees, the v1.0 rules prevail. Ignore previous Cursor/chat implementation suggestions to install `dbt-duckdb`, run local DuckDB, or use local dbt Core as the primary development workflow. Do not start generating BigQuery-specific code until the actual GCP project, dbt connection, and repository setup have been verified.
