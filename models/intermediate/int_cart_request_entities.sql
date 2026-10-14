-- Cart-based payment requests.
-- Grain: one row per payment request + order item.
--
-- Includes both POS and non-POS carts.
-- Does not filter by request status or cart type.
-- LEFT JOIN preserves cart requests even if
-- their cart or order items are missing.

with cart_requests as (

    select
        pr.payment_request_id,
        pr.business_id,
        pr.client_id,
        pr.entity_id as cart_id,
        pr.requested_amount,
        pr.currency,
        pr.request_status,
        pr.created_at,
        pr.updated_at,
        pr.deleted_at

    from {{ ref('stg_payment_requests') }} pr

    where pr.entity_type = 'cart'

),

cart_items as (

    select
        cr.payment_request_id,
        cr.business_id,
        cr.client_id,
        cr.cart_id,

        c.is_sale,

        oi.order_item_id,
        oi.entity_type,
        oi.entity_id,
        oi.amount as item_amount,

        cr.requested_amount,
        cr.currency,
        cr.request_status,
        cr.created_at,
        cr.updated_at,
        cr.deleted_at

    from cart_requests cr

    left join {{ ref('stg_carts') }} c
        on cr.cart_id = c.cart_id
       and cr.business_id = c.business_id

    left join {{ ref('stg_order_items') }} oi
        on cr.cart_id = oi.cart_id
       and cr.business_id = oi.business_id

)

select
    ci.payment_request_id,
    ci.business_id,
    ci.client_id,
    ci.entity_type,
    ci.entity_id,

    case
        when ci.entity_type = 'meeting' then m.meeting_name
        when ci.entity_type = 'event' then e.event_name
        when ci.entity_type = 'product' then p.product_name
        when ci.entity_type = 'service' then s.service_name
    end as entity_name,

    ci.requested_amount,
    ci.item_amount,
    ci.currency,
    ci.request_status,
    ci.created_at,
    ci.updated_at,
    ci.deleted_at,

    case
        when ci.is_sale = 1 then 'pos'
        when ci.is_sale = 0 then 'non_pos_cart'
        else 'unknown_cart'
    end as payment_flow,

    ci.cart_id,
    ci.order_item_id,
    ci.is_sale,

    cast(null as string) as selected_item_name,
    cast(null as string) as source_payment_id,
    cast(null as timestamp) as paid_at,

    false as is_synthetic_request

from cart_items ci

left join {{ ref('stg_meetings') }} m
    on ci.entity_type = 'meeting'
   and ci.entity_id = m.meeting_id
   and ci.business_id = m.business_id

left join {{ ref('stg_events') }} e
    on ci.entity_type = 'event'
   and ci.entity_id = e.event_id
   and ci.business_id = e.business_id

left join {{ ref('stg_products') }} p
    on ci.entity_type = 'product'
   and ci.entity_id = p.product_id
   and ci.business_id = p.business_id

left join {{ ref('stg_services') }} s
    on ci.entity_type = 'service'
   and ci.entity_id = s.service_id
   and ci.business_id = s.business_id