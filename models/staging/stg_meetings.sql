-- Standardizes meeting information.
-- Grain: one row per meeting.

select
    cast(meeting_id as string) as meeting_id,
    cast(business_id as string) as business_id,
    cast(client_id as string) as client_id,
    trim(meeting_name) as meeting_name,
    trim(description) as description,
    safe_cast(scheduled_at as timestamp) as scheduled_at,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'meetings') }}