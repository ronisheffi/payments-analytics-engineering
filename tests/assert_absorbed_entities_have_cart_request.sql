-- Ensures every meeting or event excluded from the direct flow
-- is represented by a valid cart payment request.

with absorbed_entities as (

    select
        pr.payment_request_id,
        pr.business_id,
        pr.entity_type,
        pr.entity_id

    from {{ ref('stg_payment_requests') }} pr

    where pr.entity_type in ('meeting', 'event')
      and exists (

          select 1
          from {{ ref('stg_order_items') }} oi

          where oi.business_id = pr.business_id
            and oi.entity_type = pr.entity_type
            and oi.entity_id = pr.entity_id

      )

)

select *
from absorbed_entities ae

where not exists (

    select 1

    from {{ ref('stg_order_items') }} oi

    join {{ ref('stg_carts') }} c
        on oi.cart_id = c.cart_id
       and oi.business_id = c.business_id

    join {{ ref('stg_payment_requests') }} pr
        on pr.entity_type = 'cart'
       and pr.entity_id = c.cart_id
       and pr.business_id = c.business_id

    where oi.business_id = ae.business_id
      and oi.entity_type = ae.entity_type
      and oi.entity_id = ae.entity_id

)