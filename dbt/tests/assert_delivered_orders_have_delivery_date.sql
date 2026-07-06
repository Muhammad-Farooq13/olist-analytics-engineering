-- A delivered order should always have a delivered_customer timestamp.
-- In practice, 8 of the 99,441 real Olist orders (~0.008%) are marked
-- "delivered" with no delivery timestamp recorded — a genuine data-quality
-- quirk in the upstream source, not a bug in this pipeline. Configured as a
-- warning rather than a hard failure so it's visible in every dbt run
-- without blocking the build, exactly how a real data team would triage a
-- small, known, low-impact source anomaly.

{{ config(severity = 'warn') }}

select *
from {{ ref('stg_orders') }}
where order_status = 'delivered'
  and order_delivered_customer_ts is null
