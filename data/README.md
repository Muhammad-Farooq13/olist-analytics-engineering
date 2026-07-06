# Dataset

**Source:** "Brazilian E-Commerce Public Dataset by Olist" — real, anonymized
commercial order data from Olist, the largest department store in Brazilian
online marketplaces (2016–2018, ~99,441 orders).

**License:** CC BY-NC-SA 4.0 (Attribution-NonCommercial-ShareAlike) —
**non-commercial use only**, attribution required, derivatives must share
under the same license. This repository is a portfolio/educational analytics
engineering project, consistent with that license; it is not a commercial
product and should not be repurposed as one without separately licensing the
underlying data from Olist/Kaggle.

**Original publisher:** Olist, distributed via Kaggle
(https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

**Fetched via:** a GitHub mirror of the original Kaggle CSVs (`src/ingest.py`
downloads them at build time), since this sandbox has no direct network path
to kaggle.com.

## Tables ingested

| File | Rows | Description |
|---|---|---|
| `olist_orders_dataset.csv` | 99,441 | Order-level status and timestamps (purchase, approval, delivery) |
| `olist_order_items_dataset.csv` | 112,650 | Line items per order (product, seller, price, freight) |
| `olist_customers_dataset.csv` | 99,441 | Customer ID and location |
| `olist_products_dataset.csv` | 32,951 | Product category and physical attributes |
| `olist_order_payments_dataset.csv` | 103,886 | Payment method, installments, value per order |
| `product_category_name_translation.csv` | 71 | Portuguese → English category name mapping |

## Why this dataset

Real order/item/payment/customer tables with genuine data-quality quirks
(missing delivery dates for cancelled orders, multi-item orders, multiple
payment methods per order) are exactly what an analytics engineering
pipeline needs to be tested against — far more representative of an actual
data warehouse than clean synthetic sales data. It's a well-known,
widely-cited dataset in the data community, which also means anyone
reviewing this project can independently verify the source and numbers.

## Re-fetching

```bash
python -m src.ingest
```
