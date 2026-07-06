-- Grain: one row per unique customer (customer_unique_id), aggregating
-- across the order-scoped customer_id records that Olist's raw schema uses.

with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    customer_unique_id,
    -- a person can order from multiple "customer_id" locations over time;
    -- take the most common state/city as their representative location
    arg_max(customer_state, cnt) as customer_state,
    arg_max(customer_city, cnt) as customer_city,
    count(distinct customer_id) as order_account_count
from (
    select
        customer_unique_id,
        customer_state,
        customer_city,
        customer_id,
        count(*) over (partition by customer_unique_id, customer_state, customer_city) as cnt
    from customers
)
group by customer_unique_id
