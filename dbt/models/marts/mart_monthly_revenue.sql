-- One row per month: revenue, order volume, and average order value.
-- Only counts orders that were actually completed (delivered), matching how
-- Olist and most e-commerce businesses report realized revenue rather than
-- gross cart value on cancelled/unavailable orders.

with fct as (
    select * from {{ ref('fct_order_items') }}
    where order_status = 'delivered'
),

order_level as (
    -- collapse to one row per order first, so AOV isn't skewed by
    -- multi-item orders counting as multiple "orders"
    select
        order_id,
        order_month,
        sum(item_total_value) as order_value
    from fct
    group by order_id, order_month
)

select
    order_month,
    count(distinct order_id) as n_orders,
    sum(order_value)         as total_revenue,
    round(sum(order_value) / nullif(count(distinct order_id), 0), 2) as avg_order_value
from order_level
group by order_month
order by order_month
