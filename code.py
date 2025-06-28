import streamlit as st
import pandas as pd

# Set page configuration with custom logo and app name
st.set_page_config(
    page_title="Jersey Orders",  # Custom app name
    page_icon="square_logo.png",  # Path to logo in repository
    layout="wide",  # Wider layout for better mobile display
)

# Streamlit app title
st.title("Jersey Orders")

# Password protection
password = st.text_input("Enter password:", type="password")
correct_password = "353614"  # Replace with your strong password
if password != correct_password:
    st.error("Incorrect password. Access denied.")
    st.stop()

# File uploader for orders CSV only
orders_file = st.file_uploader("Upload the orders CSV file", type=["csv"])

# Custom CSS for bordered box
st.markdown("""
    <style>
    .product-box {
        border: 2px solid #4CAF50;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        background-color: #f9f9f9;
        text-align: center;
    }
    .product-name {
        font-weight: bold;
        margin-bottom: 10px;
    }
    .size-quantity {
        margin-top: 10px;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

if orders_file is not None:
    # Load orders data
    df_new = pd.read_csv(orders_file)

    # Load products data from repository
    try:
        product_data = pd.read_csv("products_export.csv")
    except FileNotFoundError:
        st.error("products_export.csv not found in the app directory. Please ensure it's uploaded to the repository.")
        st.stop()

    # Process orders: Split into Product_Name and Size
    df_orders = (
        df_new[['*Product Name', '*Product Quantity']]
        .assign(
            Product_Name=lambda x: x['*Product Name'].str.rsplit(' - ', n=1).str[0],
            Size=lambda x: x['*Product Name'].str.rsplit(' - ', n=1).str[1]
        )
        .drop(columns='*Product Name')
    )

    # Process product data: Keep only Image Src for the primary image (Position=1)
    product_data = (
        product_data.loc[product_data['Image Position'] == 1, ['Title', 'Image Src']]
    )

    # Merge, sum quantities by Size, then format as "Size-Quantity" strings
    df_final = (
        pd.merge(df_orders, product_data, left_on='Product_Name', right_on='Title', how='left')
        .groupby(['Product_Name', 'Image Src', 'Size'])['*Product Quantity']
        .sum()
        .reset_index()
        .assign(Size_Quantity=lambda x: x['Size'] + '-' + x['*Product Quantity'].astype(str))
        .groupby(['Product_Name', 'Image Src'])
        .agg({'Size_Quantity': ', '.join})
        .reset_index()
        .rename(columns={'Product_Name': 'Product Name', 'Size_Quantity': 'Size & Quantity'})
    )

    # Display the results in a grid optimized for mobile
    st.subheader("Product Grid")
    cols_per_row = 2 if st.session_state.get('is_mobile', False) else 3  # Fewer columns on mobile
    rows = (len(df_final) + cols_per_row - 1) // cols_per_row

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            idx = row * cols_per_row + col_idx
            if idx < len(df_final):
                with cols[col_idx]:
                    # Create a bordered box for each product
                    product_name = df_final.iloc[idx]['Product Name']
                    image_url = df_final.iloc[idx]['Image Src']
                    size_quantity = df_final.iloc[idx]['Size & Quantity']
                    
                    # Render the box with product details
                    st.markdown(
                        f"""
                        <div class="product-box">
                            <div class="product-name">{product_name}</div>
                            <img src="{image_url}" style="max-width:100%; height:auto;" onerror="this.src='https://via.placeholder.com/150';">
                            <div class="size-quantity">{size_quantity}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
else:
    st.write("Please upload the orders CSV file to proceed.")
