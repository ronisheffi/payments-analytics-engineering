-- Ensures meetings and events absorbed into a cart
-- are not also represented as standalone direct requests.

select
    m.payment_request_id,
    m.entity_type,
    m.entity_id,
    m.business_id

from {{ ref('fct_payment_request_entities') }} m

where m.payment_flow = 'direct'
  and m.entity_type in ('meeting', 'event')

  and exists (

      select 1
      from {{ ref('stg_order_items') }} oi

      where oi.business_id = m.business_id
        and oi.entity_type = m.entity_type
        and oi.entity_id = m.entity_id

  )