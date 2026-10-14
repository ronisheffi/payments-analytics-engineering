-- Legacy payments without a payment request.
-- Grain: one row per legacy payment.
--
-- Creates analytical synthetic request identifiers.
-- Does not invent a real catalog entity relationship.

select
    concat('legacy_payment:', payment_id) as payment_request_id,

    business_id,
    cast(null as string) as client_id,

    'legacy_item' as entity_type,
    concat('legacy_item:', payment_id) as entity_id,

    selected_item_name as entity_name,

    amount as requested_amount,
    amount as item_amount,
    currency,

    case
        when payment_status = 'paid' then 'paid'
        else payment_status
    end as request_status,

    created_at,
    updated_at,
    deleted_at,

    'legacy_payment' as payment_flow,

    cast(null as string) as cart_id,
    cast(null as string) as order_item_id,
    cast(null as int64) as is_sale,

    selected_item_name,
    payment_id as source_payment_id,
    paid_at,

    true as is_synthetic_request

from {{ ref('stg_payments') }}

where payment_request_id is null