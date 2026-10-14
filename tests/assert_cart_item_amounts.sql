-- Validates that every cart request contains items
-- and that item amounts sum to the requested amount.

with cart_totals as (

    select
        pr.payment_request_id,
        pr.requested_amount,
        sum(oi.amount) as total_item_amount,
        count(oi.order_item_id) as item_count

    from {{ ref('stg_payment_requests') }} pr

    left join {{ ref('stg_order_items') }} oi
        on pr.entity_id = oi.cart_id
       and pr.business_id = oi.business_id

    where pr.entity_type = 'cart'

    group by
        pr.payment_request_id,
        pr.requested_amount

)

select *
from cart_totals

where item_count = 0
   or total_item_amount is distinct from requested_amount