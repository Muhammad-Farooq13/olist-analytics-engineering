-- Cleaned, typed, renamed view over the raw orders table. Staging models do
-- 1:1 light cleaning only (renaming, casting, trimming) — no joins or
-- business logic, which belongs in marts.

with source as (
    select * from {{ source('raw', 'raw_orders') }}
)

select
    order_id,
    customer_id,
    order_status,
    cast(order_purchase_timestamp as timestamp)        as order_purchase_ts,
    cast(order_approved_at as timestamp)                as order_approved_ts,
    cast(order_delivered_carrier_date as timestamp)     as order_delivered_carrier_ts,
    cast(order_delivered_customer_date as timestamp)    as order_delivered_customer_ts,
    cast(order_estimated_delivery_date as timestamp)    as order_estimated_delivery_ts
from source
