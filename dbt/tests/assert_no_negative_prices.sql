-- A singular dbt test: fails (returns rows) if any order item has a
-- negative price or freight value. dbt tests pass when the query returns
-- zero rows.

select *
from {{ ref('stg_order_items') }}
where item_price < 0
   or freight_value < 0
