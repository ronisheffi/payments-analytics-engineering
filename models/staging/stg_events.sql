-- Standardizes event information.
-- Grain: one row per event.

select
    cast(event_id as string) as event_id,
    cast(business_id as string) as business_id,
    trim(event_name) as event_name,
    trim(description) as description,
    safe_cast(event_at as timestamp) as event_at,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'events') }}