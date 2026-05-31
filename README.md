# RetailLens — E-commerce Analytics Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://retaillens-i9dgbwhmargyx7app5rvkir.streamlit.app/)

> A full-year analytics dashboard simulating a real Indian e-commerce business — built with Python, DuckDB, and Streamlit.

---

## 🔗 Live Demo

**[→ Open Dashboard](https://retaillens-i9dgbwhmargyx7app5rvkir.streamlit.app/)**

---

## 📌 Problem Statement

E-commerce companies generate thousands of orders every day across multiple cities, categories, and customer segments. Without proper analytics, it is impossible to answer questions like:

- Is the business growing month over month?
- Which city and category drives the most revenue?
- Where are customers dropping off in the purchase funnel?
- Which customer segment is most valuable?

This project builds an end-to-end analytics pipeline that answers all of these questions using a simulated Indian e-commerce dataset.

---

## 📊 Dashboard Overview

| Tab | What it shows |
|---|---|
| 📈 Overview | Monthly GMV trend, MoM growth, conversion funnel |
| 💰 Revenue | Revenue by city, payment method breakdown, AOV comparison |
| 📦 Products | Category performance, cancellation & return rates |
| 👥 Customers | Premium vs standard users, revenue per user |

---

## 🗃 Dataset

Fully synthetic dataset simulating a real Indian e-commerce platform for FY 2024.

| Table | Rows | Description |
|---|---|---|
| `users.csv` | 5,000 | City, age, gender, acquisition channel, premium status |
| `products.csv` | 200 | Category, price, brand tier, rating |
| `orders.csv` | 20,000 | Order value, status, payment method, date |
| `events.csv` | ~51,000 | User funnel events — view, add to cart, checkout, purchase |

**8 Indian cities:** Bengaluru, Mumbai, Delhi, Hyderabad, Chennai, Pune, Kolkata, Ahmedabad

**5 product categories:** Electronics, Clothing, FMCG, Books, Home & Kitchen

---

## 🔍 Key Metrics Computed

**Business metrics**
- Monthly GMV and Month-on-Month growth rate
- Average Order Value (AOV) by city, category, and payment method
- Revenue share by city and category

**Funnel metrics**
- View → Add to Cart → Checkout → Purchase conversion rates
- Drop-off percentage at each funnel stage
- Device-level conversion (Mobile vs Desktop vs Tablet)

**Customer metrics**
- Premium vs Standard user revenue comparison
- Revenue per user by segment
- Cancellation and return rates by category

---

## 💡 Key Findings

- **Overall conversion rate is 14.6%** — 30,090 product views resulted in 4,395 purchases
- **Bengaluru drives 22% of total revenue**, the highest among all cities
- **Electronics contributes the highest GMV** despite being a smaller volume category due to high AOV
- **UPI is the most used payment method** at 42% of all transactions
- **Premium users generate 2.3x more revenue per user** compared to standard users
- **May 2024 was the peak revenue month** at ₹2.49 Cr GMV

---

## 🛠 Tech Stack

| Layer | Tool |
|---|---|
| Data generation | Python (`numpy`, `pandas`) |
| Analytics engine | DuckDB |
| Data manipulation | Pandas |
| Visualisation | Matplotlib, Seaborn |
| Dashboard | Streamlit |
| Deployment | Streamlit Cloud |

---

## 📁 Project Structure

```
retaillens/
├── data/
│   └── generate_data.py      # Synthetic dataset generator
├── users.csv                 # Generated users table
├── products.csv              # Generated products table
├── orders.csv                # Generated orders table
├── events.csv                # Generated funnel events table
├── duck_db_project.ipynb     # SQL analysis + EDA notebook
├── dashboard.py              # Streamlit dashboard
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🚀 Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/retaillens.git
cd retaillens
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Generate the dataset**
```bash
python data/generate_data.py
```

**4. Launch the dashboard**
```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501`

---

## 📈 Business Recommendations

Based on the analysis:

1. **Fix mobile checkout** — Mobile has the highest traffic but checkout drop-off is significant. A simplified mobile checkout flow could recover lost revenue.
2. **Double down on Bengaluru and Mumbai** — These two cities account for 42% of total revenue. Targeted campaigns here will have the highest ROI.
3. **Electronics retention strategy** — High AOV but low repeat purchase rate. Post-purchase follow-up campaigns can improve LTV.
4. **Re-engage at-risk premium users** — Premium users who haven't ordered in 60+ days represent high-value churn. A personalised discount can bring them back.

---

## 👤 Author

**Manu**
Data Analytics Portfolio · Bengaluru, India

---

*Built as a portfolio project to demonstrate end-to-end data analytics skills — from data generation and SQL analysis to dashboard deployment.*
