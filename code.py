import streamlit as st
import pandas as pd
import os

# Set page configuration with custom logo and app name, with fallback
logo_path = "square_logo.png"
if os.path.exists(logo_path):
    st.set_page_config(
        page_title="Jersey Orders",
        page_icon=logo_path,
        layout="wide",
    )
else:
    st.set_page_config(
        page_title="Jersey Orders",
        layout="wide",
    )
    st.warning("logo.png not found in the repository. Using default icon.")

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

# Initialize session state for checkbox status
if 'checked_boxes' not in st.session_state:
    st.session_state.checked_boxes = {}

# Custom CSS for bordered box and copy button
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
    .product-box-gray {
        border-color: #808080 !important;
    }
    .product-name {
        font-weight: bold;
        margin-bottom: 10px;
    }
    .size-quantity {
        margin-top: 10px;
        font-size: 0.9em;
    }
    .copy-button {
        display: inline-block;
        margin: 10px 5px 0 5px;
        padding: 8px 16px;
        background-color: #a2d2ff;
        color: #03045e;
        text-decoration: none;
        border-radius: 5px;
        font-size: 0.9em;
        font-weight: bold;
        cursor: pointer;
        border: none;
    }
    .copy-button:hover {
        background-color: #87b5ff;
    }
    .checkbox-container {
        margin-top: 10px;
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
                    
                    # Generate a unique key for each checkbox
                    checkbox_key = f"checkbox_{idx}"
                    
                    # Format text for clipboard
                    clipboard_text = f"Product: {product_name}, Sizes: {size_quantity}"
                    
                    # Determine the box class based on checkbox state
                    box_class = "product-box-gray" if st.session_state.checked_boxes.get(checkbox_key, False) else "product-box"
                    
                    # Display the product box
                    st.markdown(
                        f"""
                        <div class="{box_class}">
                            <div class="product-name">{product_name}</div>
                            <img src="{image_url}" style="max-width:100%; height:auto;" onerror="this.src='https://via.placeholder.com/150';">
                            <div class="size-quantity">{size_quantity}</div>
                            <button class="copy-button" onclick="navigator.clipboard.writeText('{clipboard_text}')">Copy Details</button>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Add the checkbox and update session state on change
                    checked = st.checkbox(
                        "Mark as complete",
                        key=checkbox_key,
                        value=st.session_state.checked_boxes.get(checkbox_key, False),
                        on_change=lambda k=checkbox_key: st.session_state.checked_boxes.update({k: not st.session_state.checked_boxes.get(k, False)})
                    )
                    
                    # Update the session state
                    st.session_state.checked_boxes[checkbox_key] = checked
            else:
                st.write("Please upload the orders CSV file to proceed.")
