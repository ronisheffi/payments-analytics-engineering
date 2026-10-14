-- Standardizes POS carts.
-- Grain: one row per cart.

select
    cast(cart_id as string) as cart_id,
    cast(business_id as string) as business_id,
    safe_cast(is_sale as int64) as is_sale,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'carts') }}