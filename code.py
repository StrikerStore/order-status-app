import streamlit as st
import pandas as pd
import os
import hashlib
import json
import numpy as np

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

# More secure password protection
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        correct_password_hash = "62b8171d2c7265e9a8bd7868ed74792f2a518afc577c490d8efb29e4e6446bee"
        entered_password_hash = hashlib.sha256(st.session_state["password"].encode()).hexdigest()
        
        if entered_password_hash == correct_password_hash:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password:", type="password", on_change=password_entered, key="password")
        st.error("Incorrect password. Access denied.")
        return False
    else:
        return True

if not check_password():
    st.stop()

orders_file = st.file_uploader("Upload the orders CSV file", type=["csv"])

if 'checked_boxes' not in st.session_state:
    st.session_state.checked_boxes = {}
if 'edited_quantities' not in st.session_state:
    st.session_state.edited_quantities = {}

import re

def sort_sizes(size_quantity_str):
    if not isinstance(size_quantity_str, str):
        return size_quantity_str

    s = size_quantity_str.strip()

    # Pull off an optional leading label like "Player " or "Fan "
    m = re.match(r'^(Player|Fan)\s+', s, flags=re.I)
    label = ''
    if m:
        label = m.group(1).title() + ' '   # keep nice casing
        s = s[m.end():]                    # remove the label from the string we sort

    # Define the order you want
    size_order = ['S', 'M', 'L', 'XL', '2XL']

    # Parse pairs like "S-4", "2XL-7"
    pairs = [p.strip() for p in s.split(',') if p.strip()]
    ordered, others = [], []
    for p in pairs:
        if '-' in p:
            size, qty = p.rsplit('-', 1)
            size, qty = size.strip(), qty.strip()
            if size in size_order:
                ordered.append((size_order.index(size), f"{size}-{qty}"))
            else:
                others.append(p)  # keep unknown sizes as-is (after the known ones)

    # Sort known sizes by your order, then append others in their original order
    ordered_sorted = [pair for _, pair in sorted(ordered, key=lambda t: t[0])]
    result = ', '.join(ordered_sorted + others)

    # Reattach the label (once) at the start
    return f"{label}{result}" if label else result


def get_rto_info_for_product(product_name, rto_data):
    # Robust: strip and lower for both sides
    name = product_name.strip().lower()
    matches = rto_data[rto_data['Product_Name'].str.strip().str.lower() == name]
    if matches.empty:
        return None
    rto_info = {}
    for _, row in matches.iterrows():
        vendor = row['Vendor']
        size = row['Size'] if 'Size' in row and pd.notna(row['Size']) else None
        qunatity = row['Quantity'] if 'Quantity' in row and pd.notna(row['Quantity']) else None
        if vendor not in rto_info:
            rto_info[vendor] = []
        if size:
            rto_info[vendor].append(f"{size}-{qunatity}" if qunatity else size)
    return rto_info

# Card CSS
st.markdown("""
    <style>
    body, .stApp {
        background: #f7f7f9 !important;
    }
    .minimal-card {
        background: #fff;
        border-radius: 12px;
        padding: 16px 12px 10px 12px;
        margin: 10px 0;
        min-height: 220px;
        max-width: 350px;
        min-width: 0;
        box-shadow: none;
        border: 1px solid #ececec;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .minimal-card-completed {
        background: #f4f4f4;
        border: 1px solid #e0e0e0;
        opacity: 0.8;
    }
    .minimal-product-name {
        font-size: 1.08em;
        font-weight: 600;
        color: #222;
        margin-bottom: 8px;
        letter-spacing: 0.01em;
    }
    .minimal-product-name-completed {
        color: #888;
    }
    .minimal-img {
        display: block;
        margin: 0 auto 10px auto;
        border-radius: 8px;
        width: 120px;
        height: auto;
        object-fit: contain;
        background: #f7f7f9;
    }
    .minimal-img-completed {
        filter: grayscale(70%) opacity(0.8);
    }
    .minimal-section-label {
        font-size: 0.92em;
        color: #888;
        font-weight: 500;
        margin-bottom: 2px;
        margin-top: 6px;
        letter-spacing: 0.01em;
    }
    .minimal-size-qty {
        font-size: 1em;
        color: #333;
        font-weight: 500;
        margin-bottom: 4px;
        background: #f5f5f7;
        border-radius: 6px;
        padding: 4px 8px;
        display: inline-block;
    }
    .minimal-rto {
        margin-top: 4px;
        margin-bottom: 6px;
        font-size: 0.95em;
        color: #444;
        font-weight: 500;
        display: flex;
        flex-wrap: wrap;
        gap: 4px 8px;
    }
    .minimal-rto-tag {
        background: #e6eaff;
        color: #2a3a5e;
        border-radius: 8px;
        padding: 2px 8px;
        font-size: 0.88em;
        font-weight: 500;
        margin-right: 4px;
        margin-bottom: 2px;
    }
    .minimal-checkbox {
        margin-top: 8px;
    }
    @media (max-width: 900px) {
        .minimal-card { max-width: 100vw; }
    }
    @media (max-width: 600px) {
        .minimal-card { min-width: 0; max-width: 100vw; padding: 10px 4vw 8px 4vw; }
        .minimal-img { width: 120px; }
    }
    </style>
""", unsafe_allow_html=True)

if orders_file is not None:
    df_new = pd.read_csv(orders_file)
    if "Error Remarks" in df_new.columns:
        df_new = df_new.drop(columns=[col for col in df_new.columns if "Error Remarks" in col])
    # Drop duplicates
    df_new = df_new.drop_duplicates()
    try:
        product_data = pd.read_csv("products_export.csv")
    except FileNotFoundError:
        st.error("products_export.csv not found in the app directory. Please ensure it's uploaded to the repository.")
        st.stop()
    rto_file_path = "rto_details.csv"
    try:
        rto_data = pd.read_csv(rto_file_path)
    except FileNotFoundError:
        st.warning("rto_details.csv not found. Please upload it.")
        st.stop()

    # Regex pattern: removes the last -something if it's letters/numbers (sizes like M, L, XL, 2XL, 24-26, etc.)
    pattern = r'-(?:[A-Za-z]+|\d+(?:-\d+)?)+$'

    # For product_data
    product_data = (
        product_data.loc[product_data['Image Position'] == 1, ['Title', 'Image Src', 'Variant SKU']]
        .assign(
            SKU=lambda x: x['Variant SKU'].str.replace(pattern, '', regex=True)
        )
    )

    # For df_orders
    df_orders = (
        df_new[['*Product Name', '*Product Quantity', '*SKU']]
        .assign(
            Product_Name=lambda x: x['*Product Name'].str.rsplit(' - ', n=1).str[0],
            Size=lambda x: x['*Product Name'].str.rsplit(' - ', n=1).str[1],
            SKU=lambda x: x['*SKU'].str.replace(pattern, '', regex=True)
        )
        .drop(columns=['*Product Name', '*SKU'])
    )
    df_orders_grouped = (
        df_orders.groupby(['Product_Name', 'Size', 'SKU'])['*Product Quantity']
        .sum()
        .reset_index()
    )


    df_size_qty = (
        df_orders_grouped
        .assign(
            Size_Quantity=lambda x: x['Size'] + '-' + x['*Product Quantity'].astype(str),
            SKU=lambda x: x['SKU']
        )
        .groupby('Product_Name')
        .agg({
            'Size_Quantity': ', '.join,
            'SKU': 'first'
        })
        .reset_index()
        .assign(
            Size_Quantity=lambda x: np.where(
                x['Product_Name'].str.contains("Player", case=False, na=False),
                "Player " + x['Size_Quantity'],
                np.where(
                    x['Product_Name'].str.contains("Fan", case=False, na=False),
                    "Fan " + x['Size_Quantity'],
                    x['Size_Quantity']
                )
            )
        )
    )



    df_size_qty['Size_Quantity'] = df_size_qty['Size_Quantity'].apply(sort_sizes)
    df_final = pd.merge(df_size_qty, product_data, left_on='SKU', right_on='SKU', how='left')
    df_final = df_final.rename(columns={'Product_Name': 'Product Name', 'Size_Quantity': 'Size & Quantity'})
    st.subheader("Product Grid")
    total_products = len(df_final)
    completed_count = sum(1 for i in range(total_products) if st.session_state.checked_boxes.get(f"checkbox_{i}", False))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", total_products)
    with col2:
        st.metric("Completed", completed_count)
    with col3:
        st.metric("Remaining", total_products - completed_count)
    # Responsive: 1 col on mobile, 2 on desktop/tablet
    cols_per_row = 1 if st.session_state.get('is_mobile', False) else 3
    rows = (len(df_final) + cols_per_row - 1) // cols_per_row
    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            idx = row * cols_per_row + col_idx
            if idx < len(df_final):
                product_name = df_final.iloc[idx]['Product Name']
                image_url = df_final.iloc[idx]['Image Src']
                original_size_quantity = df_final.iloc[idx]['Size & Quantity']
                edited_key = f"edited_{idx}"
                current_size_quantity = st.session_state.edited_quantities.get(edited_key, original_size_quantity)
                checkbox_key = f"checkbox_{idx}"
                is_completed = st.session_state.checked_boxes.get(checkbox_key, False)
                card_class = "minimal-card minimal-card-completed" if is_completed else "minimal-card"
                name_class = "minimal-product-name minimal-product-name-completed" if is_completed else "minimal-product-name"
                img_class = "minimal-img minimal-img-completed" if is_completed else "minimal-img"
                # RTO info
                rto_info = get_rto_info_for_product(product_name, rto_data)
                rto_tags_html = ""
                if rto_info:
                    tags = []
                    for vendor, sizes in rto_info.items():
                        sizes_str = ', '.join(sizes)
                        tags.append(f'<span class="minimal-rto-tag">RTO-{vendor.upper()}: {sizes_str}</span>')
                    rto_tags_html = f"<div class='minimal-rto'>{''.join(tags)}</div>"
                # Card HTML
                card_html = f"""
                <div class='{card_class}'>
                  <div class='{name_class}'>{product_name}</div>
                  <img src='{image_url if pd.notna(image_url) and image_url else 'https://via.placeholder.com/150'}' class='{img_class}' />
                  {rto_tags_html}
                </div>
                """
                cols[col_idx].markdown(card_html, unsafe_allow_html=True)
                # Editable input and save button (outside HTML for Streamlit state)
                col_input, col_save = cols[col_idx].columns([3, 1])
                with col_input:
                    new_quantity = st.text_input(
                        "Size & Quantity:",
                        value=current_size_quantity,
                        key=f"input_{idx}",
                        label_visibility="collapsed",
                        disabled=is_completed
                    )
                with col_save:
                    if not is_completed:
                        if st.button("💾", key=f"save_{idx}", help="Save changes"):
                            st.session_state.edited_quantities[edited_key] = new_quantity
                            st.rerun()
                    else:
                        st.write("")
                def update_checkbox_state(key):
                    st.session_state.checked_boxes[key] = not st.session_state.checked_boxes.get(key, False)
                checked = cols[col_idx].checkbox(
                    "Mark as complete" if not is_completed else "Completed",
                    key=checkbox_key,
                    value=is_completed,
                    on_change=update_checkbox_state,
                    args=(checkbox_key,)
                )
                st.session_state.checked_boxes[checkbox_key] = checked
else:
    st.write("Please upload the orders CSV file to proceed.")
