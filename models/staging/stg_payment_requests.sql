-- Staging model for payment requests.
-- Standardizes data types, naming conventions and status values.
-- Preserves the original grain: one row per payment request.

select
    cast(payment_request_id as string) as payment_request_id,
    cast(business_id as string) as business_id,
    cast(client_id as string) as client_id,

    lower(trim(entity_type)) as entity_type,
    cast(entity_id as string) as entity_id,

    safe_cast(requested_amount as numeric) as requested_amount,
    upper(trim(currency)) as currency,
    lower(trim(request_status)) as request_status,

    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at

from {{ source('raw', 'payment_requests') }}