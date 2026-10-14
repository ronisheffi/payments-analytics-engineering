-- Validates that each included payment request is counted once
-- and its total amount is preserved without double counting.

with mart_totals as (

    select
        payment_request_id,
        sum(request_amount_once) as mart_amount,
        countif(request_count_once = 1) as request_count

    from {{ ref('fct_payment_request_entities') }}

    group by payment_request_id

),

expected_totals as (

    select
        payment_request_id,
        requested_amount

    from {{ ref('stg_payment_requests') }}

    where entity_type in ('cart', 'product', 'service')

       or (
           entity_type in ('meeting', 'event')
           and not exists (
               select 1
               from {{ ref('stg_order_items') }} oi
               where oi.business_id = stg_payment_requests.business_id
                 and oi.entity_type = stg_payment_requests.entity_type
                 and oi.entity_id = stg_payment_requests.entity_id
           )
       )

    union all

    select
        concat('legacy_payment:', payment_id) as payment_request_id,
        amount as requested_amount

    from {{ ref('stg_payments') }}

    where payment_request_id is null

)

select
    e.payment_request_id,
    e.requested_amount,
    m.mart_amount,
    m.request_count

from expected_totals e

left join mart_totals m
    on e.payment_request_id = m.payment_request_id

where m.payment_request_id is null
   or m.mart_amount is distinct from e.requested_amount
   or m.request_count != 1