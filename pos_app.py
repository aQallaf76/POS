import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# --- File Paths ---
PRODUCT_FILE = "products.csv"
SALES_LOG_FILE = "sales_log.csv"
ZELLE_IMAGE = "qr_code.png"  # Ensure this image exists in the same directory as this script

# --- Session State Initialization ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

# --- Load or Create Product List ---
@st.cache_data
def load_products():
    try:
        return pd.read_csv(PRODUCT_FILE)
    except FileNotFoundError:
        default_products = pd.DataFrame({
            "Product Name": ["Mini Pancakes", "Rice Crispy Cup", "Strawberries Fondue", "Matcha"],
            "Price (USD)": [7.00, 6.00, 6.00, 5.00]
        })
        default_products.to_csv(PRODUCT_FILE, index=False)
        return default_products

products = load_products()

# --- Load Sales Log ---
@st.cache_data
def load_sales_log():
    try:
        return pd.read_csv(SALES_LOG_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Reference Number", "Date", "Product Sold", "Quantity", "Total Price", "Payment Method"])

sales_log = load_sales_log()

# --- Navigation Helper ---
def navigate_to(page):
    st.session_state.current_page = page

# --- Admin Panel ---
def admin_page():
    global products, sales_log

    st.title("🔧 Admin Panel")

    # --- Total Sales ---
    if not sales_log.empty:
        st.subheader("💰 Sales Overview")
        total_sales = sales_log["Total Price"].sum()
        st.metric(label="Total Revenue (USD)", value=f"${total_sales:.2f}")

        # Top Selling Products
        st.markdown("#### Top Selling Products")
        product_sales = sales_log.groupby("Product Sold")["Quantity"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        product_sales.plot(kind="bar", ax=ax, color="skyblue", edgecolor="black")
        ax.set_title("Top Selling Products")
        ax.set_ylabel("Quantity Sold")
        ax.set_xlabel("Products")
        st.pyplot(fig)

    # --- Sales Log ---
    st.subheader("📋 Sales Log Management")
    if not sales_log.empty:
        st.markdown("#### Current Sales Log")
        st.dataframe(sales_log)

        # Edit a Sale
        sale_to_edit = st.selectbox("Select a Reference Number to Edit:", [None] + list(sales_log["Reference Number"]))
        if sale_to_edit:
            row_index = sales_log[sales_log["Reference Number"] == sale_to_edit].index[0]
            new_product = st.text_input("Edit Product Sold", sales_log.loc[row_index, "Product Sold"])
            new_quantity = st.number_input("Edit Quantity", min_value=1, value=int(sales_log.loc[row_index, "Quantity"]))
            new_total_price = st.number_input("Edit Total Price", min_value=0.0, value=float(sales_log.loc[row_index, "Total Price"]))
            new_payment_method = st.selectbox(
                "Edit Payment Method", ["Cash", "Zelle"],
                index=["Cash", "Zelle"].index(sales_log.loc[row_index, "Payment Method"]),
            )
            if st.button("Update Sale"):
                sales_log.at[row_index, "Product Sold"] = new_product
                sales_log.at[row_index, "Quantity"] = new_quantity
                sales_log.at[row_index, "Total Price"] = new_total_price
                sales_log.at[row_index, "Payment Method"] = new_payment_method
                sales_log.to_csv(SALES_LOG_FILE, index=False)
                st.success(f"Sale with Reference Number {sale_to_edit} updated successfully!")

        # Delete a Sale
        sale_to_delete = st.selectbox("Select a Reference Number to Delete:", sales_log["Reference Number"])
        if st.button("Delete Sale"):
            sales_log = sales_log[sales_log["Reference Number"] != sale_to_delete]
            sales_log.to_csv(SALES_LOG_FILE, index=False)
            st.success(f"Sale with Reference Number {sale_to_delete} deleted successfully!")
    else:
        st.info("No sales data available yet.")

    # --- Product Management ---
    st.subheader("🛍️ Product Management")

    # Display Products
    st.markdown("#### Current Product Catalog")
    st.dataframe(products)

    # Add a Product
    with st.form("add_product_form"):
        new_product_name = st.text_input("New Product Name")
        new_product_price = st.number_input("New Product Price (USD)", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Product")
        if submitted:
            if new_product_name and new_product_price > 0:
                new_product = pd.DataFrame({"Product Name": [new_product_name], "Price (USD)": [new_product_price]})
                products = pd.concat([products, new_product], ignore_index=True)
                products.to_csv(PRODUCT_FILE, index=False)
                st.success(f"Product '{new_product_name}' added successfully!")

    # Navigation
    if st.button("Back to Main Menu"):
        navigate_to("Home")

# --- Main POS App ---
def home_page():
    global sales_log

    st.title("🍴 Mini Pancakes POS")
    st.subheader("Effortlessly manage sales for your delicious items!")

    # Select Products
    st.markdown("#### Step 1: Select Products")
    selected_products = st.multiselect("Choose products:", products["Product Name"])

    quantities = []
    for product in selected_products:
        qty = st.number_input(f"Enter quantity for {product}:", min_value=1, value=1, key=f"qty_{product}")
        quantities.append(qty)

    # Calculate Total
    if selected_products:
        selected_prices = products[products["Product Name"].isin(selected_products)]["Price (USD)"]
        total_price = sum(selected_prices.values * quantities)
        st.subheader(f"🛒 Total Price: **${total_price:.2f}**")

        # Payment Method
        st.markdown("#### Step 2: Choose Payment Method")
        payment_method = st.radio("Payment Method:", ["Cash", "Zelle"], key="payment_method")

        # Show Zelle QR Code if selected
        if payment_method == "Zelle":
            st.image(ZELLE_IMAGE, caption="Scan this QR code to pay", width=200)

        # Confirm Sale
        if st.button("Confirm Sale"):
            reference_number = datetime.now().strftime("%Y%m%d%H%M%S")
            sale = {
                "Reference Number": reference_number,
                "Date": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "Product Sold": ", ".join(selected_products),
                "Quantity": sum(quantities),
                "Total Price": total_price,
                "Payment Method": payment_method
            }
            new_entry = pd.DataFrame([sale])
            sales_log = pd.concat([sales_log, new_entry], ignore_index=True)
            sales_log.to_csv(SALES_LOG_FILE, index=False)
            st.success(f"Sale confirmed! Reference Number: {reference_number}")

    # Navigation
    if st.button("Go to Admin Page"):
        navigate_to("Admin")

# --- Page Navigation ---
if st.session_state.current_page == "Home":
    home_page()
elif st.session_state.current_page == "Admin":
    admin_page()
