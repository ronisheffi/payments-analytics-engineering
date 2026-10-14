-- Standardizes items associated with POS carts.
-- Grain: one row per order item.

select
    cast(order_item_id as string) as order_item_id,
    cast(cart_id as string) as cart_id,
    cast(business_id as string) as business_id,
    lower(trim(item_type)) as item_type,
    lower(trim(entity_type)) as entity_type,
    cast(entity_id as string) as entity_id,
    safe_cast(amount as numeric) as amount,
    upper(trim(currency)) as currency,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'order_items') }}