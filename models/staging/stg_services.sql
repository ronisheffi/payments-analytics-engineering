-- Grain: one row per service.
select
    cast(service_id as string) as service_id,
    cast(business_id as string) as business_id,
    trim(service_name) as service_name,
    trim(description) as description,
    safe_cast(price as numeric) as price,
    upper(trim(currency)) as currency,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'services') }}