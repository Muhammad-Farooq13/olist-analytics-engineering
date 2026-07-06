-- An order can have multiple payment rows (e.g. split across a voucher and
-- a credit card). This aggregates to one row per order so it can be joined
-- 1:1 onto fct_order_items without fanning out the grain.

with source as (
    select * from {{ source('raw', 'raw_payments') }}
)

select
    order_id,
    sum(payment_value)                                          as total_payment_value,
    max(payment_installments)                                   as max_installments,
    count(*)                                                     as payment_row_count,
    -- the payment method used for the largest share of the order's value
    arg_max(payment_type, payment_value)                         as primary_payment_type
from source
group by order_id
