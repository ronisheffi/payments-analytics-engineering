-- Direct payment requests.
-- Grain: one row per payment request + entity.
--
-- Business rule:
-- Meetings and events absorbed into a cart are no longer
-- treated as standalone payment-request entities.
--
-- Products and services may be sold both directly and
-- inside carts, so they are not excluded on this basis.

with direct_requests as (

    select
        pr.payment_request_id,
        pr.business_id,
        pr.client_id,
        pr.entity_type,
        pr.entity_id,
        pr.requested_amount,
        pr.requested_amount as item_amount,
        pr.currency,
        pr.request_status,
        pr.created_at,
        pr.updated_at,
        pr.deleted_at

    from {{ ref('stg_payment_requests') }} pr

    where pr.entity_type in (
        'meeting',
        'event',
        'product',
        'service'
    )

    and (
        pr.entity_type in ('product', 'service')

        or not exists (

            select 1
            from {{ ref('stg_order_items') }} oi

            where oi.business_id = pr.business_id
              and oi.entity_type = pr.entity_type
              and oi.entity_id = pr.entity_id

        )
    )

)

select
    dr.payment_request_id,
    dr.business_id,
    dr.client_id,
    dr.entity_type,
    dr.entity_id,

    case
        when dr.entity_type = 'meeting' then m.meeting_name
        when dr.entity_type = 'event' then e.event_name
        when dr.entity_type = 'product' then p.product_name
        when dr.entity_type = 'service' then s.service_name
    end as entity_name,

    dr.requested_amount,
    dr.item_amount,
    dr.currency,
    dr.request_status,
    dr.created_at,
    dr.updated_at,
    dr.deleted_at,

    'direct' as payment_flow,

    cast(null as string) as cart_id,
    cast(null as string) as order_item_id,
    cast(null as int64) as is_sale,
    cast(null as string) as selected_item_name,
    cast(null as string) as source_payment_id,
    cast(null as timestamp) as paid_at,

    false as is_synthetic_request

from direct_requests dr

left join {{ ref('stg_meetings') }} m
    on dr.entity_type = 'meeting'
   and dr.entity_id = m.meeting_id
   and dr.business_id = m.business_id

left join {{ ref('stg_events') }} e
    on dr.entity_type = 'event'
   and dr.entity_id = e.event_id
   and dr.business_id = e.business_id

left join {{ ref('stg_products') }} p
    on dr.entity_type = 'product'
   and dr.entity_id = p.product_id
   and dr.business_id = p.business_id

left join {{ ref('stg_services') }} s
    on dr.entity_type = 'service'
   and dr.entity_id = s.service_id
   and dr.business_id = s.business_id