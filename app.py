import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Retail Sales Intelligence App", layout="wide")
st.title("📊 Retail Sales Intelligence Dashboard")

# --- STEP 1: DATA INTEGRATION (File Uploads) ---
st.sidebar.header("1. Upload Datasets")
sales_file = st.sidebar.file_uploader("Upload retail_weekly_sales.xlsx", type=['xlsx'])
store_file = st.sidebar.file_uploader("Upload store_master.xlsx", type=['xlsx'])

if sales_file and store_file:
    # Load data
    try:
        sales_df = pd.read_excel(sales_file)
        store_df = pd.read_excel(store_file)
        
        # Merge datasets (Assuming 'Store_ID' is the common column)
        # Note: Adjust 'Store_ID' if your Excel column is named differently (e.g., 'store_id', 'Store ID')
        df = pd.merge(sales_df, store_df, on="Store_ID", how="left")
        
        # --- FILTERS ---
        st.sidebar.header("2. Filters")
        
        # Helper function for multiselect
        def multiselect_filter(column_name, label):
            if column_name in df.columns:
                options = df[column_name].unique().tolist()
                selected = st.sidebar.multiselect(label, options, default=options)
                return selected
            return []

        weeks = multiselect_filter("Week", "Select Week")
        regions = multiselect_filter("Region", "Select Region")
        stores = multiselect_filter("Store_Name", "Select Store")
        cities = multiselect_filter("City", "Select City")
        formats = multiselect_filter("Store_Format", "Select Store Format")
        categories = multiselect_filter("Product_Category", "Select Category")

        # Apply Filters
        filtered_df = df[
            (df["Week"].isin(weeks)) &
            (df["Region"].isin(regions)) &
            (df["Store_Name"].isin(stores)) &
            (df["City"].isin(cities)) &
            (df["Store_Format"].isin(formats)) &
            (df["Product_Category"].isin(categories))
        ]

        # --- STEP 5: BUSINESS LOGIC & KPI CALCULATIONS ---
        # Assuming standard column names. Adjust if your dataset differs.
        net_sales = filtered_df["Net_Sales"].sum()
        target_sales = filtered_df["Target_Sales"].sum()
        target_achievement = (net_sales / target_sales * 100) if target_sales > 0 else 0
        
        total_transactions = filtered_df["Transactions"].sum()
        atv = (net_sales / total_transactions) if total_transactions > 0 else 0
        
        return_amount = filtered_df["Return_Amount"].sum()
        return_rate = (return_amount / net_sales * 100) if net_sales > 0 else 0
        
        discount_amount = filtered_df["Discount_Amount"].sum()
        gross_sales = filtered_df["Gross_Sales"].sum()
        discount_rate = (discount_amount / gross_sales * 100) if gross_sales > 0 else 0

        # --- STEP 4: BUILD DASHBOARD (KPI Cards) ---
        st.subheader("Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Net Sales", f"${net_sales:,.2f}")
        col2.metric("Target Achievement", f"{target_achievement:.1f}%")
        col3.metric("Avg Transaction Value", f"${atv:.2f}")
        col4.metric("Return Rate", f"{return_rate:.1f}%")
        col5.metric("Discount Rate", f"{discount_rate:.1f}%")
        
        st.markdown("---")

        # --- CHARTS ---
        st.subheader("Visual Insights")
        c1, c2 = st.columns(2)
        
        with c1:
            # Weekly Trend
            weekly_trend = filtered_df.groupby("Week")["Net_Sales"].sum().reset_index()
            fig_trend = px.line(weekly_trend, x="Week", y="Net_Sales", title="Weekly Sales Trend", markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Category Performance
            cat_perf = filtered_df.groupby("Product_Category")["Net_Sales"].sum().reset_index()
            fig_cat = px.bar(cat_perf, x="Product_Category", y="Net_Sales", title="Category Performance", color="Product_Category")
            st.plotly_chart(fig_cat, use_container_width=True)

        with c2:
            # Sales by Region
            region_sales = filtered_df.groupby("Region")["Net_Sales"].sum().reset_index()
            fig_region = px.pie(region_sales, names="Region", values="Net_Sales", title="Sales by Region")
            st.plotly_chart(fig_region, use_container_width=True)
            
            # Store Leaderboard (Top 10)
            store_sales = filtered_df.groupby("Store_Name")["Net_Sales"].sum().reset_index().sort_values(by="Net_Sales", ascending=False).head(10)
            fig_store = px.bar(store_sales, x="Net_Sales", y="Store_Name", orientation='h', title="Store Leaderboard (Top 10)")
            st.plotly_chart(fig_store, use_container_width=True)

        # Stockout Risk (Assuming columns 'Inventory_Level' and 'Sales_Velocity' exist)
        if "Inventory_Level" in filtered_df.columns and "Net_Sales" in filtered_df.columns:
            st.subheader("Stockout Risk Analysis")
            fig_stock = px.scatter(filtered_df, x="Net_Sales", y="Inventory_Level", color="Product_Category", hover_data=["Store_Name"], title="Inventory Level vs Net Sales (Lower right = High Stockout Risk)")
            st.plotly_chart(fig_stock, use_container_width=True)

        st.markdown("---")

        # --- BUSINESS INSIGHT SUMMARY ---
        st.subheader("💡 Business Insight Summary")
        
        # Best/Worst Regions
        best_region = region_sales.loc[region_sales["Net_Sales"].idxmax()]["Region"]
        worst_region = region_sales.loc[region_sales["Net_Sales"].idxmin()]["Region"]
        
        # Stores missing target
        store_targets = filtered_df.groupby("Store_Name")[["Net_Sales", "Target_Sales"]].sum().reset_index()
        missed_target_stores = store_targets[store_targets["Net_Sales"] < store_targets["Target_Sales"]]["Store_Name"].tolist()
        
        # High return categories
        cat_returns = filtered_df.groupby("Product_Category").apply(lambda x: x["Return_Amount"].sum() / x["Net_Sales"].sum() * 100 if x["Net_Sales"].sum() > 0 else 0).reset_index(name="Return_Rate")
        high_return_cats = cat_returns[cat_returns["Return_Rate"] > 5]["Product_Category"].tolist() # Assuming >5% is high

        st.info(f"**Top Performing Region:** {best_region} | **Lowest Performing Region:** {worst_region}")
        st.warning(f"**Stores Missing Target:** {', '.join(missed_target_stores) if missed_target_stores else 'None'}")
        st.error(f"**High Return Categories (>5%):** {', '.join(high_return_cats) if high_return_cats else 'None'}")

        # --- EXPORT / DOWNLOAD ---
        st.markdown("---")
        st.subheader("Export Data")
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name='filtered_retail_sales.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"An error occurred while processing the data. Please ensure your Excel files have the correct column names. Error details: {e}")
        st.write("Expected columns include: Store_ID, Week, Region, Store_Name, City, Store_Format, Product_Category, Net_Sales, Target_Sales, Transactions, Return_Amount, Discount_Amount, Gross_Sales, Inventory_Level.")

else:
    st.info("Please upload both `retail_weekly_sales.xlsx` and `store_master.xlsx` in the sidebar to view the dashboard.")
