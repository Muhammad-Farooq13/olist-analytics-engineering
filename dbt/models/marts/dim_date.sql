-- A self-contained date spine covering the full range of order activity,
-- generated natively in DuckDB rather than pulling in the dbt_utils package
-- (kept dependency-free since this environment has no network access to
-- the dbt package hub).

with bounds as (
    select
        min(order_purchase_ts)::date as min_date,
        max(order_purchase_ts)::date as max_date
    from {{ ref('stg_orders') }}
),

spine as (
    select unnest(generate_series(
        (select min_date from bounds),
        (select max_date from bounds),
        interval 1 day
    )) as date_day
)

select
    date_day,
    extract(year from date_day)                as year,
    extract(month from date_day)                as month,
    extract(day from date_day)                  as day_of_month,
    extract(dow from date_day)                  as day_of_week,
    strftime(date_day, '%Y-%m')                 as year_month,
    strftime(date_day, '%B')                    as month_name,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from spine
