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

    st.markdown("---")
    st.subheader("Sales Log Management")

    # Display Sales Log
    if not sales_log.empty:
        st.markdown("### Current Sales Log")
        st.dataframe(sales_log)

        # Edit a Sale
        st.markdown("### Edit a Sale")
        sale_to_edit = st.selectbox("Select a Reference Number to Edit:", sales_log["Reference Number"])
        if sale_to_edit:
            row_index = sales_log[sales_log["Reference Number"] == sale_to_edit].index[0]
            new_product = st.text_input(
                "Edit Product Sold", sales_log.loc[row_index, "Product Sold"]
            )
            new_quantity = st.number_input(
                "Edit Quantity", min_value=1, value=int(sales_log.loc[row_index, "Quantity"])
            )
            new_total_price = st.number_input(
                "Edit Total Price", min_value=0.0, value=float(sales_log.loc[row_index, "Total Price"])
            )
            new_payment_method = st.selectbox(
                "Edit Payment Method", ["Cash", "Zelle"], index=["Cash", "Zelle"].index(sales_log.loc[row_index, "Payment Method"])
            )
            if st.button("Update Sale", key="update_sale_button"):
                sales_log.at[row_index, "Product Sold"] = new_product
                sales_log.at[row_index, "Quantity"] = new_quantity
                sales_log.at[row_index, "Total Price"] = new_total_price
                sales_log.at[row_index, "Payment Method"] = new_payment_method
                sales_log.to_csv(sales_log_file, index=False)
                st.success(f"Sale with Reference Number {sale_to_edit} updated successfully!")
                st.experimental_rerun()

        # Delete a Sale
        st.markdown("### Delete a Sale")
        sale_to_delete = st.selectbox("Select a Reference Number to Delete:", sales_log["Reference Number"])
        if st.button("Delete Sale", key="delete_sale_button"):
            sales_log.drop(sales_log[sales_log["Reference Number"] == sale_to_delete].index, inplace=True)
            sales_log.to_csv(sales_log_file, index=False)
            st.success(f"Sale with Reference Number {sale_to_delete} deleted successfully!")
            st.experimental_rerun()

    else:
        st.info("No sales data available yet.")

    # Download Sales Log
    st.markdown("### Download Sales Log")
    csv = sales_log.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Sales Log as CSV",
        data=csv,
        file_name="sales_log.csv",
        mime="text/csv",
    )

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
