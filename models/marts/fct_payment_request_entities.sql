{{ config(materialized='table') }}

-- Unified payment request + entity fact table.
-- Direct requests, cart items and synthetic legacy requests.
-- Grain:
--   Direct: payment_request_id + entity
--   Cart:   payment_request_id + order_item_id
--   Legacy: one synthetic request per payment

with all_request_entities as (

    select * from {{ ref('int_direct_request_entities') }}

    union all

    select * from {{ ref('int_cart_request_entities') }}

    union all

    select * from {{ ref('int_legacy_payment_requests') }}

),

final as (

    select
        *,

        -- Stable identifier for each analytical row
        case
            when payment_flow in ('pos', 'non_pos_cart', 'unknown_cart')
                then concat(
                    payment_request_id, ':',
                    coalesce(order_item_id, 'missing_item')
                )
            else payment_request_id
        end as request_entity_key,

        -- Count each payment request only once
        case
            when row_number() over (
                partition by payment_request_id
                order by
                    case when order_item_id is null then 1 else 0 end,
                    order_item_id
            ) = 1
                then requested_amount
            else 0
        end as request_amount_once,

        -- Count each payment request only once
        case
            when row_number() over (
                partition by payment_request_id
                order by
                    case when order_item_id is null then 1 else 0 end,
                    order_item_id
            ) = 1
                then 1
            else 0
        end as request_count_once

    from all_request_entities

)

select * from final