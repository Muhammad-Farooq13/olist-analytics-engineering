-- One row per customer state: delivery speed and on-time rate — the view an
-- operations/logistics team would use to find underperforming regions.

with fct as (
    select * from {{ ref('fct_order_items') }}
    where order_status = 'delivered'
      and delivery_days is not null
),

orders_with_state as (
    select distinct
        order_id,
        delivery_days,
        is_late_delivery,
        customer_state
    from fct
)

select
    customer_state,
    count(*)                                                        as n_orders,
    round(avg(delivery_days), 1)                                    as avg_delivery_days,
    round(100.0 * sum(case when is_late_delivery then 1 else 0 end) / count(*), 2) as pct_late_deliveries
from orders_with_state
group by customer_state
order by n_orders desc
