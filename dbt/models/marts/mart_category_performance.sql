-- One row per product category: revenue, item volume, and average price —
-- the "what's actually selling" view a merchandising or category manager
-- would look at.

with fct as (
    select * from {{ ref('fct_order_items') }}
    where order_status = 'delivered'
),

products as (
    select * from {{ ref('dim_products') }}
)

select
    coalesce(p.category_english, 'unknown') as category,
    count(*)                                as n_items_sold,
    count(distinct f.order_id)              as n_orders,
    sum(f.item_price)                       as total_revenue,
    round(avg(f.item_price), 2)             as avg_item_price
from fct f
left join products p
    on f.product_id = p.product_id
group by coalesce(p.category_english, 'unknown')
order by total_revenue desc
