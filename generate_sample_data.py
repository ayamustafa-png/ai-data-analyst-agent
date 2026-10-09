"""Generate a realistic e-commerce dataset with known patterns for demoing the agent.

Planted patterns:
- Electronics sales decline over the last 3 months
- Email channel has the best ROI, Paid Social the worst
- ~8% missing discounts, ~1% duplicated rows, a few negative quantities
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 6000
dates = pd.date_range("2025-10-01", "2026-09-30", freq="D")

categories = ["Electronics", "Fashion", "Home", "Beauty", "Sports"]
channels = ["Email", "Organic", "Paid Search", "Paid Social", "Referral"]
base_price = {"Electronics": 420, "Fashion": 60, "Home": 110, "Beauty": 35, "Sports": 80}
cost_per_order = {"Email": 2, "Organic": 0, "Paid Search": 14, "Paid Social": 22, "Referral": 6}

rows = []
for i in range(N):
    d = rng.choice(dates)
    cat = rng.choice(categories, p=[0.25, 0.25, 0.2, 0.15, 0.15])
    # Electronics orders get dropped in the last 3 months to plant a decline
    if cat == "Electronics" and pd.Timestamp(d) >= pd.Timestamp("2026-07-01") and rng.random() < 0.6:
        cat = rng.choice(["Fashion", "Home", "Beauty", "Sports"])
    ch = rng.choice(channels, p=[0.15, 0.3, 0.2, 0.2, 0.15])
    qty = int(rng.integers(1, 5))
    price = round(base_price[cat] * rng.uniform(0.7, 1.3), 2)
    discount = round(float(rng.choice([0, 0.05, 0.1, 0.2])), 2)
    revenue = round(qty * price * (1 - discount), 2)
    if ch == "Email":
        revenue = round(revenue * 1.25, 2)       # Email converts to bigger baskets
    if ch == "Paid Social":
        revenue = round(revenue * 0.8, 2)
    rows.append({
        "order_id": 100000 + i, "order_date": pd.Timestamp(d).date().isoformat(),
        "customer_id": int(rng.integers(1, 1800)), "category": cat, "channel": ch,
        "quantity": qty, "unit_price": price, "discount": discount,
        "revenue": revenue, "marketing_cost": cost_per_order[ch] + round(float(rng.uniform(0, 3)), 2),
    })

df = pd.DataFrame(rows)
df.loc[rng.choice(N, int(N * 0.08), replace=False), "discount"] = np.nan
df.loc[rng.choice(N, 5, replace=False), "quantity"] = -1
df = pd.concat([df, df.sample(int(N * 0.01), random_state=1)], ignore_index=True)
df.to_csv("sample_data/ecommerce_orders.csv", index=False)
print(f"Saved {len(df)} rows to sample_data/ecommerce_orders.csv")
