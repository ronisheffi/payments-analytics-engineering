# Payments Analytics Engineering — Project Specification

**Status:** Implementation specification v0.8  
**Scope:** End-to-end dbt Core + DuckDB analytics project using fully synthetic data, inspired by real-world payment workflows.

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
2. **Invoice aggregation with retained requests:** only unpaid source requests can be included; the original payment-request rows **remain physically present** but their status changes to `replaced`. A new invoice payment request is created; `order_items.type='i'` stores constituent lines. Preserve invoice request ID and invoice ID on resolved lines. Resolve the underlying entity from invoice items, not from the invoice container. Avoid counting replaced constituent requests as additional active payable demand. Do not assume the invoice items contain original constituent request IDs unless an explicit link exists.
3. **POS sale, persisted only upon payment:** preparing a POS basket in the UI creates **no persisted sale/cart request** and does not alter existing payment requests. The prepared POS basket cannot be saved and resumed later. **Only when a payment is executed** are the sale cart (`is_sale=1`), its new payment request, `order_items.type='s'` lines and payment persisted; any relevant pre-existing source payment requests are **logically deleted via `delete_at`** in this synthetic system; raw ingestion retains the tombstone. Resolve the underlying entities from POS lines. Detect `delete_at` updates via incremental ingestion and propagate them into incremental models; exclude logically deleted requests from active payable demand. A persisted POS sale has at least one payment, but may be partially paid. Behavior after payment cancellation/reversal is unknown and must not be invented.
4. **Legacy client cart:** initiated **only by the client in the Client Portal**. The client selects **existing payment requests only** and pays them together; new catalog products, services or free-form items without an existing request cannot be added. A new request references a non-sale cart (`is_sale=0`) linking the selected requests. Constituent source requests remain, while the payment is recorded against the cart request. Resolve underlying entities via the linked requests, preserve cart and constituent lineage, and avoid duplicating paid amounts. Do not assert an unverified persistence lifecycle for an unpaid/abandoned client cart.
5. **Historical ad-hoc payment:** a payment without a request must map to a virtual analytical request; its actor unambiguously determines client/business legacy ad-hoc flow.

At the detailed fact grain, distinguish `canonical_payment_request_id` (the actual/virtual payable request), `source_constituent_request_id` when available, `source_container_type`, `invoice_id`/`cart_id` where applicable, `item_id`, `underlying_entity_type`, and `underlying_entity_id`. An invoice or cart must not be the sole analytical entity when it has constituent lines. For invoice requests, retained original rows may be available for audit but their linkage to invoice items is not guaranteed. For POS source requests, do not invent a source-request-to-sale-item FK; derive sale details from POS items. Ensure item-level requested amounts and allocated paid amounts reconcile to the payable request and do not multiply due to one-to-many joins.

## Source timestamps and deletion convention
Every synthetic operational raw table must include `create_at`, `update_at`, and `delete_at` (nullable). Preserve these names through staging. In **this independent synthetic design**, deletions are logical: an upstream row is retained with `delete_at` populated and `update_at` advanced. The incremental ingestion feed captures this change. No snapshot comparison or POS replacement log is required. A soft-deleted row remains available for lineage/audit, but must not count as active payable demand. `WHERE delete_at IS NULL` is valid in a full rebuild, **but not sufficient by itself in a persisted incremental mart**: changed/deleted keys must trigger a merge/tombstone or explicit removal of previously materialized active rows. Prefer retaining an `is_deleted`/`is_active_payable` marker in the incremental canonical layer, with filtered active consumption marts/views. Changes to constituents, payments and items must invalidate/recompute all affected canonical request and item allocations.

## Data pipeline and incremental strategy
- Operational source → simulated Stitch-style **incremental ingestion** (new/updated rows including deletion tombstones) → raw current-state tables → staging → intermediate → marts.
- Do **not** model or claim a full-table overwrite architecture. Use incremental dbt `merge` with stable unique keys and dependency-aware change propagation; full refresh remains a recovery option.
- Demonstrate at least two deterministic ingestion batches: Invoice conversion with retained constituent requests marked `replaced`; POS payment with original direct requests marked `delete_at`; Client Cart paid-on-creation; and updated/new payments including legacy orphans.
- Use test assertions that formerly active requests are not left as stale payable records after `delete_at` or `replaced` transitions. Preserve audit lineage separately.

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

The table list and exact column names are design proposals to be validated during implementation.

## Business rules

### Booking-triggered requests
- Each underlying meeting/event/product/service may have **at most one direct payment request** at a time in the synthetic source. The same entity can also appear inside an invoice, POS sale or client cart; that does not constitute a second direct request.
- A meeting or event does **not** automatically generate a payment request merely by existing.
- A payment request is created when the booking is configured as requiring payment.
- `request_initiator` may be `business`, `client`, or `system`.
- `system` is permitted **only** for automatically booked meetings/events where the configured rule creates a payment request. Enforce this with a data-quality test.

### Invoices
- An invoice may be created only from **unpaid** source requests. A request already paid cannot be rolled into a newly created invoice.
- **Invoice creation does not physically delete constituent source payment requests.** They remain in `payment_requests` and change to `request_status='replaced'`. A **new, distinct payment request** is created with `entity_type='invoice'` and `entity_uid=invoice_id`.
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
- Historical orphan payments are **exclusively ad-hoc payments**. Their workflow is deterministically identifiable from `payment_actor`: `client` means **legacy client-initiated ad-hoc payment**, and `business` means **legacy business-initiated ad-hoc payment**. These are exhaustive cases for payments lacking a source payment request; do not classify them as unknown or infer any other flow.
- Set `entity_type = 'ad_hoc'` on the virtual analytical request, and expose a derived legacy workflow classification based on the two cases above. Preserve `payment_actor` on the payment fact. Since no actual request-creation event occurred, keep `request_initiator` NULL on the virtual request rather than copying `payment_actor` into it; the derived historical flow is still known unambiguously.
- Test that every historical orphan payment has a valid `payment_actor` (`client` or `business`) and resolves to exactly one of these two ad-hoc classifications. Keep this derivation separate from any optional labels for newer flows.
- Use a stable item identifier for virtual requests (for example a payment-derived line) when a source entity/line item is absent, and avoid multiplying amounts in item-level marts.
- Test uniqueness of canonical request IDs, one-to-one mapping for orphan payments, coverage of every payment, no double counting of paid amounts, and stable IDs across incremental reruns.
- Distinguish **real payment-request adoption metrics** from unified payment-activity metrics: virtual requests are an analytical bridge and must not be counted as real user-created requests.

### Payments and allocation
- A request can have multiple payments and be partially paid, whether it originates from an invoice, POS sale, legacy cart, or direct request.
- Compute settlement consistently at canonical payment-request grain: `successful_paid_amount` is the sum of successful positive payments, `remaining_amount = greatest(requested_amount - successful_paid_amount, 0)` (subject to an explicit overpayment policy), `is_fully_paid` when successful paid amount meets the requested amount. `payment_status` is `unpaid`, `partially_paid`, or `fully_paid`. Keep request cancellation in a separate `request_status`.
- Every recorded payment has `payment_actor` of either `business` or `client`; requests without payments have no payment actor yet (NULL at request summary level).
- `payment_key` identifies a processor transaction; `is_online` is relevant to additional business logic. Do not assume a transaction key is globally unique across processors.
- Item-level `allocated_paid_amount` is a **proportional estimate**: successful paid amount × item requested amount / total constituent requested amount. Test reconciliation, handle zero denominators, and retain original payment amounts.
- No partial payment cancellation is assumed for the initial dataset. Refunds, reversals, invoice cancellation and POS reversal are explicitly out of scope.

## Workflow attributes and classification
Prefer independent attributes that identify each stage unambiguously:
- **At request creation:** `request_initiator`, `request_source`, `entity_type`, `entity_uid`, `is_sale` (for cart requests), `requested_amount`, `requires_payment` (for relevant booking source).
- **After request creation:** `payment_link_sent`, request lifecycle status.
- **At payment execution:** `payment_actor`, `is_online`, `payment_method`, `payment_key`, `payment_processor`, payment status and amount.
- **Derived outcomes at payment-request grain:** `successful_paid_amount`, `remaining_amount`, `payment_status` (`unpaid`, `partially_paid`, `fully_paid`), `is_partially_paid`, `is_fully_paid`, `has_paid_invoice`. Keep `request_status` (including cancellation) separate from settlement status.

Avoid forcing requests into a fixed list of seven flows. If a human-readable flow label is useful, derive it from the atomic attributes and permit extensibility. Because one request may have multiple payments, payment actor/channel belongs at **payment grain**; request-level rollups should use flags or explicit mixed-value logic.

## Analytical models and grains
1. `fct_payments`: one row per payment record; transaction context and execution attributes.
2. `fct_payment_requests`: one row per canonical payable request; lifecycle, requested/paid totals, invoice-paid flag, and summary attributes.
3. `fct_payment_request_items`: one row per canonical payable request **plus item/underlying entity**; includes free-form lines and proportional paid allocation. Use stable line-item IDs, not nullable entity IDs alone, as row keys.
4. Monthly/lifetime usage aggregates above detailed facts; explicitly define whether metrics count requests, items, payments, or invoices.

Source constituent requests retained for audit (invoice and client cart) should not inflate canonical payable-request counts. POS source requests remain as soft-deleted raw rows; active sale details are resolved from POS lines, not counted again from deleted direct requests. Invoice items also determine the analytical detail of invoice requests even though original requests remain.

## dbt structure
- `models/staging`: source cleaning, casting, status normalization, key tests.
- `models/intermediate`: historical-payment virtual request mapping, canonical request union, request lineage, invoice/POS/cart item resolution, payment aggregation, business rules.
- `models/marts`: facts and consumption-oriented aggregates.
- `tests`: referential integrity, uniqueness at grain, historical payment coverage, deterministic legacy ad-hoc classification and virtual-request provenance, amount reconciliation, valid actors/initiators, valid `system` booking origin, invoice paid flag, duplicate-count protections.

## Monetary model: tax, tip and FX
- Include tax and tip in the synthetic schema and calculations. Each payable item has `base_amount` and `tax_amount`; a request may have `tip_amount`. Define `requested_amount = sum(item base_amount + item tax_amount) + tip_amount` for multi-item containers. Direct requests use the same reconciliation rule with one analytical line. No discounts, fees or refunds in v1.
- Treat tax and tip as distinct components (not revenue by default); preserve gross paid, tax and tip separately. Allocate request-level tip across items proportionally to pre-tip item gross; label allocations as estimates and assign rounding residual deterministically to the final line. Reconcile all item gross amounts to the canonical request gross.
- Include daily `exchange_rates` with `rate_date`, `from_currency`, `to_currency`, `rate` and uniqueness tests. Use **USD** as reporting currency. Convert payment amounts at `payments.create_at` date and request amounts at `payment_requests.create_at` date. The rate means units of USD per 1 source-currency unit; USD→USD = 1. Use decimal-safe rounding, test missing rates and document that payment/request USD figures may differ due to FX timing.
- `exchange_rates` is a reference feed, not necessarily an operational product table; the three operational timestamps requirement does not force fake source lifecycle fields on this reference feed.

## Payment status and cart/invoice lifecycle
- Synthetic `payments.payment_status='paid'` means successful payment and counts toward `successful_paid_amount`; other values (e.g. `failed`) do not. Request settlement remains `unpaid`, `partially_paid`, `fully_paid` and is **derived** from successful payments, not copied from the transaction status.
- Invoice creation retains original source requests with `request_status='replaced'`, creates a new invoice request and invoice lines, and does not require an item→original-request FK. The replaced requests are not active payable demand; UI visibility is separate from physical row retention.
- Client Cart exists only when the first payment is executed; before that, selections are ephemeral and requests remain independent. POS likewise persists only when a payment is executed. Partial payment is permitted for either.

## Explicit exclusions
Refunds, chargebacks, payment reversals, invoice cancellation, POS restoration, hard-delete detection/snapshot diff, and POS replacement log are not part of v1. This is a standalone synthetic design inspired by generic payment workflows; do not reference or replicate a particular company's confidential implementation.

## Open implementation choices (non-blocking)
- Define sensible synthetic currencies, dates, tax/tip distributions, failed payments, and rounding conventions consistently in generator, SQL and tests.
- No event-attendance table required in v1. Preserve `payment_key`, `is_online` and payment processor without inventing a fixed number of workflow classes.

## Delivery plan
1. Implement the source schemas and deterministic generator with at least two incremental ingestion batches, including tombstones and status transitions, plus exchange-rate reference data.
2. Set up Python, dbt Core, dbt-duckdb and DuckDB. Load and incrementally upsert raw operational rows; retain `delete_at` tombstones.
3. Build staging → intermediate → incremental canonical and item models → active consumption marts, with unique keys and dependency-aware recomputation.
4. Test invoice/POS/cart lifecycle, orphan virtual requests, actor constraints, tax/tip/FX arithmetic, allocation, no double counting, and deletion/status-change propagation across batches.
5. Build monthly/lifetime usage aggregates, dbt docs, reproducible README and Git branch/commit/PR demonstration.
