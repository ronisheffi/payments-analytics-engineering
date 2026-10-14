-- Staging model for payments.
-- Standardizes payment fields while preserving one row per payment.
-- Includes legacy payments without a payment request.

select
    cast(payment_id as string) as payment_id,
    cast(payment_request_id as string) as payment_request_id,
    cast(business_id as string) as business_id,

    safe_cast(amount as numeric) as amount,
    upper(trim(currency)) as currency,
    lower(trim(payment_status)) as payment_status,
    trim(selected_item_name) as selected_item_name,

    safe_cast(create_at as timestamp) as created_at,
    safe_cast(update_at as timestamp) as updated_at,
    safe_cast(delete_at as timestamp) as deleted_at,
    safe_cast(paid_at as timestamp) as paid_at

from {{ source('raw', 'payments') }}