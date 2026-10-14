-- Standardizes business information.
-- Grain: one row per business.

select
    cast(business_id as string) as business_id,
    trim(business_name) as business_name,
    upper(trim(country_code)) as country_code,
    trim(identity_group_code) as identity_group_code,
    trim(identity_group_description) as identity_group_description,
    lower(trim(status)) as status,
    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at
from {{ source('raw', 'businesses') }}