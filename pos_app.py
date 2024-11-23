import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- Admin Password ---
DEFAULT_PASSWORD = "admin123"  # Default password for login

# --- User Authentication ---
def authenticate():
    st.title("🔑 User Login")
    st.subheader("Please enter your password to access the POS system.")

    password = st.text_input("Password:", type="password", key="login_password")
    if st.button("Login", key="login_button"):
        if password == DEFAULT_PASSWORD:
            st.session_state.authenticated = True
            st.success("Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")

# --- Authentication Check ---
if not st.session_state.authenticated:
    authenticate()
    st.stop()

# --- Load or Create Product List ---
product_file = "products.csv"
try:
    products = pd.read_csv(product_file)
except FileNotFoundError:
    # Default products
    products = pd.DataFrame({
        "Product Name": ["Mini Pancakes", "Rice Crispy Cup", "Strawberries Fondue", "Matcha"],
        "Price (USD)": [7.00, 6.00, 6.00, 5.00]
    })
    products.to_csv(product_file, index=False)

# --- Load Sales Log ---
sales_log_file = "sales_log.csv"
try:
    sales_log = pd.read_csv(sales_log_file)
except FileNotFoundError:
    sales_log = pd.DataFrame(columns=["Reference Number", "Date", "Product Sold", "Quantity", "Total Price", "Payment Method"])

# --- Admin Product Management ---
def admin_page():
    st.title("🔧 Admin Panel")
    st.subheader("Manage your product catalog and view sales performance.")

    # Total Sales
    if not sales_log.empty:
        st.markdown("### Total Sales")
        total_sales = sales_log["Total Price"].sum()
        st.metric(label="💰 Total Revenue (USD)", value=f"${total_sales:.2f}")

        # Top Selling Products
        st.markdown("### Top Selling Products")
        product_sales = sales_log.groupby("Product Sold")["Quantity"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        product_sales.plot(kind="bar", ax=ax, color="skyblue", edgecolor="black")
        ax.set_title("Top Selling Products")
        ax.set_ylabel("Quantity Sold")
        ax.set_xlabel("Products")
        st.pyplot(fig)
    else:
        st.info("No sales data available yet.")

    # Display Current Products
    st.markdown("---")
    st.subheader("Current Product Catalog")
    st.dataframe(products)

    # Add Product
    st.markdown("### Add a New Product")
    new_product_name = st.text_input("New Product Name")
    new_product_price = st.number_input("New Product Price (USD)", min_value=0.0, step=0.01)
    if st.button("Add Product", key="add_product_button"):
        if new_product_name and new_product_price > 0:
            new_product = pd.DataFrame({"Product Name": [new_product_name], "Price (USD)": [new_product_price]})
            updated_products = pd.concat([products, new_product], ignore_index=True)
            updated_products.to_csv(product_file, index=False)
            st.success(f"Product '{new_product_name}' added successfully!")
            st.experimental_rerun()
        else:
            st.error("Please enter a valid product name and price.")

    # Edit Product
    st.markdown("### Edit an Existing Product")
    product_to_edit = st.selectbox("Select a product to edit:", products["Product Name"])
    if product_to_edit:
        edited_name = st.text_input("Edit Product Name", value=product_to_edit)
        edited_price = st.number_input(
            "Edit Product Price (USD)",
            value=float(products.loc[products["Product Name"] == product_to_edit, "Price (USD)"].values[0]),
            min_value=0.0,
            step=0.01,
        )
        if st.button("Update Product", key="update_product_button"):
            products.loc[products["Product Name"] == product_to_edit, "Product Name"] = edited_name
            products.loc[products["Product Name"] == edited_name, "Price (USD)"] = edited_price
            products.to_csv(product_file, index=False)
            st.success(f"Product '{edited_name}' updated successfully!")
            st.experimental_rerun()

    # Delete Product
    st.markdown("### Delete a Product")
    product_to_delete = st.selectbox("Select a product to delete:", products["Product Name"])
    if st.button("Delete Product", key="delete_product_button"):
        updated_products = products[products["Product Name"] != product_to_delete]
        updated_products.to_csv(product_file, index=False)
        st.success(f"Product '{product_to_delete}' deleted successfully!")
        st.experimental_rerun()

    # Back to Main Page
    if st.button("Back to Main Menu", key="back_to_main_menu_button"):
        st.session_state.authenticated = True
        st.rerun()

# --- Main POS App ---
st.title("🍴 Mini Pancakes POS")
st.subheader("Effortlessly manage sales for your delicious items!")

# POS Main Page
st.markdown("### Step 1: Select Products")
selected_products = st.multiselect("Choose products:", products["Product Name"], key="product_select")

quantities = []
for product in selected_products:
    qty = st.number_input(f"Enter quantity for {product}:", min_value=1, value=1, key=f"quantity_{product}")
    quantities.append(qty)

if selected_products:
    selected_prices = products[products["Product Name"].isin(selected_products)]["Price (USD)"]
    total_price = sum(selected_prices.values * quantities)
    st.subheader(f"🛒 Total Price: **${total_price:.2f}**")
else:
    total_price = 0

# Proceed to Payment
if selected_products:
    st.markdown("### Step 2: Choose Payment Method")
    payment_method = st.radio("Payment Method:", ["Cash", "Zelle"], key="payment_method")

    # Confirm Sale for Cash
    if payment_method == "Cash" and st.button("Confirm Sale (Cash)", key="confirm_cash_sale"):
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
        sales_log.to_csv(sales_log_file, index=False)
        st.success(f"Sale confirmed! Reference Number: {reference_number}")

    # Confirm Sale for Zelle
    elif payment_method == "Zelle":
        st.subheader("📱 Zelle Payment")
        st.image("qr_code.png", caption="Scan this QR code to pay", width=200)  # Ensure correct file path

        if st.button("Confirm Sale (Zelle)", key="confirm_payment_button"):
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
            sales_log.to_csv(sales_log_file, index=False)
            st.success(f"Sale logged successfully! Reference Number: {reference_number}")

# Admin Access
st.markdown("---")
if st.button("Go to Admin Page", key="go_to_admin_button"):
    admin_page()
    st.stop()
