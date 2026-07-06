"""Interactive analytics dashboard over the Olist DuckDB warehouse.

A different serving paradigm than the other projects' FastAPI endpoints —
this is what an analytics engineer would actually hand to a stakeholder:
a self-serve dashboard over the marts, not an API.

Run locally:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config, resolve_path  # noqa: E402

st.set_page_config(page_title="Olist Analytics", page_icon="📊", layout="wide")


@st.cache_resource
def get_connection():
    config = load_config()
    warehouse_path = resolve_path(config["warehouse"]["path"])
    if not warehouse_path.exists():
        st.error("Warehouse not found. Run `make build` first to ingest data and run dbt.")
        st.stop()
    return duckdb.connect(str(warehouse_path), read_only=True)


con = get_connection()

st.title("📊 Olist E-Commerce Analytics")
st.caption(
    "Real Brazilian e-commerce data (2016–2018), transformed with dbt + DuckDB. "
    "CC BY-NC-SA 4.0 — non-commercial demo."
)

# ---- Headline KPIs ----
kpi_row = con.execute(
    """
    select
        (select sum(total_revenue) from marts.mart_monthly_revenue) as total_revenue,
        (select sum(n_orders) from marts.mart_monthly_revenue) as total_orders,
        (select count(*) from marts.dim_customers) as n_customers,
        (select round(avg(pct_late_deliveries), 2) from marts.mart_delivery_performance) as avg_pct_late
    """
).fetchone()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue (delivered)", f"R$ {kpi_row[0]:,.0f}")
col2.metric("Total Orders", f"{kpi_row[1]:,}")
col3.metric("Unique Customers", f"{kpi_row[2]:,}")
col4.metric("Avg. Late Delivery Rate", f"{kpi_row[3]:.1f}%")

st.divider()

# ---- Monthly revenue trend ----
st.subheader("Monthly Revenue Trend")
revenue_df = con.execute(
    "select order_month, total_revenue, n_orders, avg_order_value "
    "from marts.mart_monthly_revenue order by order_month"
).df()
st.line_chart(revenue_df.set_index("order_month")["total_revenue"])

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Orders per Month")
    st.bar_chart(revenue_df.set_index("order_month")["n_orders"])
with col_b:
    st.subheader("Average Order Value per Month")
    st.line_chart(revenue_df.set_index("order_month")["avg_order_value"])

st.divider()

# ---- Category performance ----
st.subheader("Top Categories by Revenue")
top_n = st.slider("Number of categories to show", 5, 30, 10)
category_df = con.execute(
    f"select category, n_items_sold, n_orders, total_revenue, avg_item_price "
    f"from marts.mart_category_performance order by total_revenue desc limit {top_n}"
).df()
st.bar_chart(category_df.set_index("category")["total_revenue"])
st.dataframe(category_df, use_container_width=True)

st.divider()

# ---- Delivery performance ----
st.subheader("Delivery Performance by State")
delivery_df = con.execute(
    "select customer_state, n_orders, avg_delivery_days, pct_late_deliveries "
    "from marts.mart_delivery_performance order by n_orders desc"
).df()
st.dataframe(delivery_df, use_container_width=True)
