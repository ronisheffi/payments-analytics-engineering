-- Grain: one row per product.
select
    cast(product_id as string) as product_id,
    cast(business_id as string) as business_id,
    trim(product_name) as product_name,
    trim(description) as description,
    safe_cast(price as numeric) as price,
    upper(trim(currency)) as currency,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'products') }}