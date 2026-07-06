-- Grain: one row per order line item (order_id, order_item_id).
-- This is the central fact table everything else rolls up from.

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

payments as (
    select * from {{ ref('stg_payments') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
)

select
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    c.customer_unique_id,
    c.customer_state,
    c.customer_city,
    o.order_status,
    o.order_purchase_ts,
    o.order_delivered_customer_ts,
    o.order_estimated_delivery_ts,
    date_trunc('month', o.order_purchase_ts)::date as order_month,

    oi.item_price,
    oi.freight_value,
    oi.item_price + oi.freight_value as item_total_value,

    p.total_payment_value as order_total_payment_value,
    p.primary_payment_type,
    p.max_installments,

    -- delivery performance, only meaningful for delivered orders
    case
        when o.order_delivered_customer_ts is not null
        then date_diff('day', o.order_purchase_ts, o.order_delivered_customer_ts)
    end as delivery_days,

    case
        when o.order_delivered_customer_ts is not null and o.order_estimated_delivery_ts is not null
        then o.order_delivered_customer_ts > o.order_estimated_delivery_ts
    end as is_late_delivery

from order_items oi
inner join orders o
    on oi.order_id = o.order_id
left join payments p
    on oi.order_id = p.order_id
left join customers c
    on o.customer_id = c.customer_id
