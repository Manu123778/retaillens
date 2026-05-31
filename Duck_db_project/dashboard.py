import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RetailLens Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: #0a0e1a;
    color: #e8eaf0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1422 !important;
    border-right: 1px solid #1e2640;
}
[data-testid="stSidebar"] * {
    color: #a0a8c0 !important;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #141928 0%, #1a2035 100%);
    border: 1px solid #1e2d50;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-card.blue::before  { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.kpi-card.green::before { background: linear-gradient(90deg, #10b981, #34d399); }
.kpi-card.amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-card.pink::before  { background: linear-gradient(90deg, #ec4899, #f472b6); }

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #6b7a99;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 600;
    color: #e8eaf0;
    font-family: 'DM Mono', monospace;
    margin-bottom: 4px;
}
.kpi-sub {
    font-size: 12px;
    color: #4a5578;
}

/* Chart containers */
.chart-card {
    background: #141928;
    border: 1px solid #1e2640;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
}

/* Section headers */
.section-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #3b82f6;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2640;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: #0f1422;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1e2640;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #6b7a99 !important;
    font-weight: 500;
    font-size: 13px;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: #1e2d50 !important;
    color: #60a5fa !important;
}

/* Metric delta */
[data-testid="stMetricDelta"] { font-size: 12px; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e2640; border-radius: 3px; }

/* DataFrame */
.stDataFrame { border-radius: 12px; overflow: hidden; }

div[data-testid="stHorizontalBlock"] > div { gap: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────────────────────────
DARK_BG    = "#141928"
GRID_COLOR = "#1e2640"
TEXT_COLOR = "#a0a8c0"
ACCENT     = ["#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4"]

def set_chart_style(fig, ax_list=None):
    fig.patch.set_facecolor(DARK_BG)
    axes = ax_list if ax_list else fig.get_axes()
    for ax in (axes if isinstance(axes, list) else [axes]):
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=TEXT_COLOR, labelsize=10)
        ax.xaxis.label.set_color(TEXT_COLOR)
        ax.yaxis.label.set_color(TEXT_COLOR)
        ax.title.set_color("#e8eaf0")
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"₹{x/1e6:.1f}M" if x >= 1e6 else
                          f"₹{x/1e3:.0f}K" if x >= 1e3 else f"{x:.0f}"
        ))

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    con  = duckdb.connect()

    for tbl in ["users", "products", "orders", "events"]:
        path = os.path.join(base, f"{tbl}.csv").replace("\\", "/")
        con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{path}')")

    q1 = con.execute("""
        SELECT order_month,
            COUNT(order_id) AS total_orders,
            COUNT(DISTINCT user_id) AS unique_buyers,
            ROUND(SUM(order_value_inr),0) AS total_revenue,
            ROUND(AVG(order_value_inr),0) AS avg_order_value,
            ROUND((SUM(order_value_inr) - LAG(SUM(order_value_inr))
                OVER (ORDER BY order_month)) * 100.0 /
                NULLIF(LAG(SUM(order_value_inr)) OVER (ORDER BY order_month),0),1
            ) AS mom_growth_pct
        FROM orders WHERE status='Delivered'
        GROUP BY order_month ORDER BY order_month
    """).fetchdf()

    q2 = con.execute("""
        SELECT u.city, COUNT(o.order_id) AS orders,
            ROUND(SUM(o.order_value_inr),0) AS revenue_inr,
            ROUND(AVG(o.order_value_inr),0) AS aov_inr,
            ROUND(SUM(o.order_value_inr)*100.0/SUM(SUM(o.order_value_inr)) OVER(),1) AS revenue_share_pct
        FROM orders o JOIN users u ON o.user_id=u.user_id
        WHERE o.status='Delivered' GROUP BY u.city ORDER BY revenue_inr DESC
    """).fetchdf()

    q3 = con.execute("""
        SELECT p.category, COUNT(o.order_id) AS orders, SUM(o.quantity) AS units_sold,
            ROUND(SUM(o.order_value_inr),0) AS revenue_inr,
            ROUND(AVG(o.order_value_inr),0) AS aov_inr,
            ROUND(SUM(o.order_value_inr)*100.0/SUM(SUM(o.order_value_inr)) OVER(),1) AS revenue_share_pct
        FROM orders o JOIN products p ON o.product_id=p.product_id
        WHERE o.status='Delivered' GROUP BY p.category ORDER BY revenue_inr DESC
    """).fetchdf()

    q4 = con.execute("""
        SELECT p.category, COUNT(o.order_id) AS total_orders,
            SUM(CASE WHEN o.status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,
            SUM(CASE WHEN o.status='Returned'  THEN 1 ELSE 0 END) AS returned,
            ROUND(SUM(CASE WHEN o.status='Cancelled' THEN 1 ELSE 0 END)*100.0/COUNT(o.order_id),1) AS cancel_rate_pct,
            ROUND(SUM(CASE WHEN o.status='Returned'  THEN 1 ELSE 0 END)*100.0/COUNT(o.order_id),1) AS return_rate_pct
        FROM orders o JOIN products p ON o.product_id=p.product_id
        GROUP BY p.category ORDER BY cancel_rate_pct DESC
    """).fetchdf()

    q5 = con.execute("""
        SELECT payment_method, COUNT(order_id) AS orders,
            ROUND(SUM(order_value_inr),0) AS revenue_inr,
            ROUND(AVG(order_value_inr),0) AS aov_inr
        FROM orders WHERE status='Delivered'
        GROUP BY payment_method ORDER BY revenue_inr DESC
    """).fetchdf()

    q6 = con.execute("""
        SELECT u.is_premium, COUNT(DISTINCT u.user_id) AS users,
            COUNT(o.order_id) AS orders,
            ROUND(SUM(o.order_value_inr),0) AS total_revenue_inr,
            ROUND(AVG(o.order_value_inr),0) AS aov_inr,
            ROUND(SUM(o.order_value_inr)/NULLIF(COUNT(DISTINCT u.user_id),0),0) AS revenue_per_user_inr
        FROM users u LEFT JOIN orders o ON u.user_id=o.user_id AND o.status='Delivered'
        GROUP BY u.is_premium
    """).fetchdf()

    funnel = con.execute("""
        SELECT event_type,
            COUNT(DISTINCT user_id) AS unique_users,
            ROUND(COUNT(DISTINCT user_id)*100.0/MAX(COUNT(DISTINCT user_id)) OVER(),1) AS pct_of_top
        FROM events GROUP BY event_type
        ORDER BY CASE event_type
            WHEN 'view' THEN 1 WHEN 'add_to_cart' THEN 2
            WHEN 'checkout' THEN 3 WHEN 'purchase' THEN 4 END
    """).fetchdf()

    con.close()
    return q1, q2, q3, q4, q5, q6, funnel

df_monthly, df_city, df_cat, df_returns, df_payment, df_premium, df_funnel = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 RetailLens")
    st.markdown("**Indian E-commerce Analytics**")
    st.markdown("---")
    st.markdown("**Dataset**")
    st.markdown("🗓 Jan – Dec 2024")
    st.markdown("👥 5,000 users")
    st.markdown("📦 20,000 orders")
    st.markdown("🛍 200 products")
    st.markdown("🏙 8 Indian cities")
    st.markdown("---")
    st.markdown("**Built by**")
    st.markdown("Manu")
    st.markdown("Data Analytics Portfolio")
    st.markdown("---")
    st.markdown("**Stack**")
    st.markdown("`Python` `DuckDB` `Pandas`")
    st.markdown("`Matplotlib` `Streamlit`")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 32px 0 24px 0;'>
    <div style='font-size:11px;letter-spacing:2px;text-transform:uppercase;
                color:#3b82f6;font-weight:600;margin-bottom:8px;'>
        ANALYTICS DASHBOARD
    </div>
    <div style='font-size:36px;font-weight:600;color:#e8eaf0;line-height:1.1;'>
        RetailLens
    </div>
    <div style='font-size:15px;color:#6b7a99;margin-top:6px;'>
        Full-year performance overview · Indian E-commerce · FY 2024
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_gmv    = df_monthly["total_revenue"].sum()
total_orders = df_monthly["total_orders"].sum()
avg_aov      = df_monthly["avg_order_value"].mean()
conversion   = round(df_funnel[df_funnel["event_type"]=="purchase"]["unique_users"].values[0] /
                     df_funnel[df_funnel["event_type"]=="view"]["unique_users"].values[0] * 100, 1)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class='kpi-card blue'>
        <div class='kpi-label'>Total GMV</div>
        <div class='kpi-value'>₹{total_gmv/1e7:.1f}Cr</div>
        <div class='kpi-sub'>Full Year 2024</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class='kpi-card green'>
        <div class='kpi-label'>Total Orders</div>
        <div class='kpi-value'>{int(total_orders):,}</div>
        <div class='kpi-sub'>Delivered orders</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class='kpi-card amber'>
        <div class='kpi-label'>Avg Order Value</div>
        <div class='kpi-value'>₹{int(avg_aov):,}</div>
        <div class='kpi-sub'>Per delivered order</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class='kpi-card pink'>
        <div class='kpi-label'>Conversion Rate</div>
        <div class='kpi-value'>{conversion}%</div>
        <div class='kpi-sub'>View → Purchase</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Overview", "💰  Revenue", "📦  Products", "👥  Customers"
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-title'>Monthly Performance</div>", unsafe_allow_html=True)

    fig, ax1 = plt.subplots(figsize=(13, 4.5))
    set_chart_style(fig, [ax1])

    ax1.bar(df_monthly["order_month"], df_monthly["total_revenue"],
            color="#3b82f6", alpha=0.75, width=0.6, zorder=2)
    ax1.set_ylabel("GMV (₹)", color=TEXT_COLOR, fontsize=11)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"₹{x/1e6:.0f}M"))
    ax1.tick_params(axis="x", rotation=40, labelsize=9)
    ax1.set_axisbelow(True)
    ax1.yaxis.grid(True, color=GRID_COLOR, linewidth=0.6)
    ax1.xaxis.grid(False)

    ax2 = ax1.twinx()
    ax2.set_facecolor(DARK_BG)
    valid = df_monthly.dropna(subset=["mom_growth_pct"])
    ax2.plot(valid["order_month"], valid["mom_growth_pct"],
             color="#10b981", marker="o", markersize=5,
             linewidth=2, linestyle="--", zorder=3)
    ax2.axhline(0, color="#ec4899", linestyle=":", linewidth=1, alpha=0.6)
    ax2.set_ylabel("MoM Growth %", color=TEXT_COLOR, fontsize=11)
    ax2.tick_params(colors=TEXT_COLOR, labelsize=10)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    for spine in ax2.spines.values():
        spine.set_edgecolor(GRID_COLOR)

    p1 = mpatches.Patch(color="#3b82f6", alpha=0.75, label="Monthly GMV")
    p2 = mpatches.Patch(color="#10b981", label="MoM Growth %")
    ax1.legend(handles=[p1, p2], loc="upper left",
               facecolor=DARK_BG, edgecolor=GRID_COLOR,
               labelcolor=TEXT_COLOR, fontsize=10)
    ax1.set_title("Monthly GMV & Growth Trend", color="#e8eaf0", fontsize=13,
                  fontweight="600", pad=14)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Conversion Funnel</div>", unsafe_allow_html=True)

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        fig, ax = plt.subplots(figsize=(8, 3.5))
        set_chart_style(fig, [ax])
        stages   = df_funnel["event_type"].tolist()
        users    = df_funnel["unique_users"].tolist()
        clrs     = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981"]
        bars = ax.barh(stages[::-1], users[::-1], color=clrs[::-1],
                       alpha=0.85, height=0.5)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}"))
        ax.set_xlabel("Unique Users", color=TEXT_COLOR, fontsize=10)
        ax.set_title("Funnel Drop-off by Stage", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.6)
        ax.set_axisbelow(True)
        for bar, val, pct in zip(bars, users[::-1], df_funnel["pct_of_top"].tolist()[::-1]):
            ax.text(bar.get_width() + 80, bar.get_y() + bar.get_height()/2,
                    f"{int(val):,}  ({pct}%)", va="center",
                    color=TEXT_COLOR, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col_f2:
        st.markdown("<br>", unsafe_allow_html=True)
        for _, row in df_funnel.iterrows():
            color = {"view":"#3b82f6","add_to_cart":"#8b5cf6",
                     "checkout":"#f59e0b","purchase":"#10b981"}.get(row["event_type"],"#fff")
            st.markdown(f"""
            <div style='background:#1a2035;border-left:3px solid {color};
                        padding:10px 14px;border-radius:0 8px 8px 0;margin-bottom:8px;'>
                <div style='font-size:11px;color:#6b7a99;text-transform:uppercase;
                            letter-spacing:1px;'>{row['event_type'].replace('_',' ')}</div>
                <div style='font-size:20px;font-weight:600;color:#e8eaf0;
                            font-family:DM Mono,monospace;'>{int(row['unique_users']):,}</div>
                <div style='font-size:11px;color:{color};'>{row['pct_of_top']}% of views</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — Revenue
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-title'>Revenue by City</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        set_chart_style(fig, [ax])
        colors_city = [ACCENT[i % len(ACCENT)] for i in range(len(df_city))]
        bars = ax.barh(df_city["city"][::-1], df_city["revenue_inr"][::-1],
                       color=colors_city[::-1], alpha=0.85, height=0.55)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"₹{x/1e6:.0f}M"))
        ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_title("Revenue by City", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        for bar, share in zip(bars, df_city["revenue_share_pct"].tolist()[::-1]):
            ax.text(bar.get_width() + 1e5, bar.get_y() + bar.get_height()/2,
                    f"{share}%", va="center", color=TEXT_COLOR, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(DARK_BG)
        wedges, texts, autotexts = ax.pie(
            df_city["revenue_share_pct"], labels=df_city["city"],
            autopct="%1.1f%%", colors=ACCENT,
            wedgeprops={"edgecolor": DARK_BG, "linewidth": 2, "width": 0.55},
            startangle=140, pctdistance=0.75)
        for t in texts:
            t.set_color(TEXT_COLOR); t.set_fontsize(9)
        for at in autotexts:
            at.set_color("#e8eaf0"); at.set_fontsize(8); at.set_fontweight("600")
        ax.set_title("Revenue Share by City", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Payment Methods</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        fig.patch.set_facecolor(DARK_BG); ax.set_facecolor(DARK_BG)
        wedges, texts, autotexts = ax.pie(
            df_payment["orders"], labels=df_payment["payment_method"],
            autopct="%1.1f%%", colors=ACCENT,
            wedgeprops={"edgecolor": DARK_BG, "linewidth": 2, "width": 0.5},
            startangle=90)
        for t in texts:
            t.set_color(TEXT_COLOR); t.set_fontsize(9)
        for at in autotexts:
            at.set_color("#e8eaf0"); at.set_fontsize(8); at.set_fontweight("600")
        ax.set_title("Orders by Payment Method", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col4:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        set_chart_style(fig, [ax])
        clrs = [ACCENT[i % len(ACCENT)] for i in range(len(df_payment))]
        bars = ax.bar(df_payment["payment_method"], df_payment["aov_inr"],
                      color=clrs, alpha=0.85, width=0.5)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"₹{x:,.0f}"))
        ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", rotation=20, labelsize=9)
        ax.set_title("AOV by Payment Method", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 200,
                    f"₹{bar.get_height():,.0f}",
                    ha="center", color=TEXT_COLOR, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — Products
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>Category Performance</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        set_chart_style(fig, [ax])
        clrs = [ACCENT[i % len(ACCENT)] for i in range(len(df_cat))]
        bars = ax.bar(df_cat["category"], df_cat["revenue_inr"],
                      color=clrs, alpha=0.85, width=0.5)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"₹{x/1e6:.0f}M"))
        ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", rotation=15, labelsize=9)
        ax.set_title("Revenue by Category", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        for bar, share in zip(bars, df_cat["revenue_share_pct"]):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 2e5,
                    f"{share}%", ha="center", color=TEXT_COLOR, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        set_chart_style(fig, [ax])
        clrs = [ACCENT[i % len(ACCENT)] for i in range(len(df_cat))]
        bars = ax.bar(df_cat["category"], df_cat["aov_inr"],
                      color=clrs, alpha=0.85, width=0.5)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"₹{x:,.0f}"))
        ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", rotation=15, labelsize=9)
        ax.set_title("AOV by Category", color="#e8eaf0",
                     fontsize=12, fontweight="600", pad=12)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 100,
                    f"₹{bar.get_height():,.0f}",
                    ha="center", color=TEXT_COLOR, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Cancellation & Return Rates</div>", unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(13, 4))
    set_chart_style(fig, [ax])
    x     = range(len(df_returns))
    width = 0.32
    b1 = ax.bar([i - width/2 for i in x], df_returns["cancel_rate_pct"],
                width, label="Cancel Rate %", color="#ec4899", alpha=0.85)
    b2 = ax.bar([i + width/2 for i in x], df_returns["return_rate_pct"],
                width, label="Return Rate %", color="#f59e0b", alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(df_returns["category"], rotation=10, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Cancellation & Return Rate by Category", color="#e8eaf0",
                 fontsize=12, fontweight="600", pad=12)
    ax.legend(facecolor=DARK_BG, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=10)
    for bar in b1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f"{bar.get_height()}%", ha="center", color=TEXT_COLOR, fontsize=9)
    for bar in b2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f"{bar.get_height()}%", ha="center", color=TEXT_COLOR, fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ═══════════════════════════════════════════════════════════════════
# TAB 4 — Customers
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-title'>Premium vs Standard Users</div>", unsafe_allow_html=True)

    df_premium["label"] = df_premium["is_premium"].map({True: "Premium", False: "Standard"})
    metrics = [
        ("total_revenue_inr", "Total Revenue (₹)"),
        ("aov_inr",           "Avg Order Value (₹)"),
        ("revenue_per_user_inr", "Revenue / User (₹)"),
    ]

    cols = st.columns(3)
    colors_prem = ["#3b82f6", "#6b7a99"]
    for col, (metric, label) in zip(cols, metrics):
        with col:
            fig, ax = plt.subplots(figsize=(4, 3.5))
            set_chart_style(fig, [ax])
            bars = ax.bar(df_premium["label"], df_premium[metric],
                          color=colors_prem, alpha=0.85, width=0.45)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"₹{x/1e6:.1f}M" if x >= 1e6 else f"₹{x:,.0f}"))
            ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
            ax.set_axisbelow(True)
            ax.set_title(label, color="#e8eaf0", fontsize=11, fontweight="600", pad=10)
            for bar in bars:
                val = bar.get_height()
                label_txt = f"₹{val/1e6:.1f}M" if val >= 1e6 else f"₹{val:,.0f}"
                ax.text(bar.get_x() + bar.get_width()/2,
                        val + val * 0.02,
                        label_txt, ha="center", color=TEXT_COLOR, fontsize=9)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Summary Tables</div>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Monthly Revenue**")
        display_monthly = df_monthly[["order_month","total_orders",
                                      "total_revenue","mom_growth_pct"]].copy()
        display_monthly.columns = ["Month","Orders","Revenue (₹)","MoM Growth %"]
        display_monthly["Revenue (₹)"] = display_monthly["Revenue (₹)"].apply(
            lambda x: f"₹{x:,.0f}")
        st.dataframe(display_monthly, use_container_width=True, hide_index=True)

    with col_t2:
        st.markdown("**Category Summary**")
        display_cat = df_cat[["category","orders","revenue_inr","aov_inr"]].copy()
        display_cat.columns = ["Category","Orders","Revenue (₹)","AOV (₹)"]
        display_cat["Revenue (₹)"] = display_cat["Revenue (₹)"].apply(
            lambda x: f"₹{x:,.0f}")
        display_cat["AOV (₹)"] = display_cat["AOV (₹)"].apply(
            lambda x: f"₹{x:,.0f}")
        st.dataframe(display_cat, use_container_width=True, hide_index=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:40px 0 20px;
            color:#2d3550;font-size:12px;border-top:1px solid #1e2640;
            margin-top:40px;'>
    RetailLens · Built with Python, DuckDB & Streamlit · Portfolio Project 2024
</div>
""", unsafe_allow_html=True)
