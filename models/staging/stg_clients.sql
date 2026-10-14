-- Standardizes client information.
-- Grain: one row per client.

select
    cast(client_id as string) as client_id,
    cast(business_id as string) as business_id,
    trim(client_name) as client_name,
    upper(trim(country_code)) as country_code,
    trim(identity_group_code) as identity_group_code,
    trim(identity_group_description) as identity_group_description,
    lower(trim(status)) as status,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'clients') }}