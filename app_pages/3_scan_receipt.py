# pages/3_scan_receipt.py
import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
from datetime import datetime
from services.ocr import OCRService
from services.firebase import FirebaseService
from components.theme import apply_theme

def format_inr(amount):
    """Format amount in Indian Rupees"""
    return f"₹{amount:,.2f}"

def show():
    """Scan Receipt Page"""
    apply_theme()
    
    st.markdown('<h1 class="main-header">Scan Receipt</h1>', unsafe_allow_html=True)
    st.markdown("Upload your grocery receipt to automatically extract items and add them to your pantry and budget tracking.", text_alignment="center")
    
    # Initialize session state
    if 'scanned_items' not in st.session_state:
        st.session_state.scanned_items = []
    if 'scan_result' not in st.session_state:
        st.session_state.scan_result = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'items_added' not in st.session_state:
        st.session_state.items_added = False
    if 'added_message' not in st.session_state:
        st.session_state.added_message = ""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Upload Receipt")
        
        # Tips for Best Results
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h4 style="margin: 0 0 10px 0;">📸 Tips for Best Results</h4>
            <ul style="margin: 0; padding-left: 1.2rem;">
                <li>📱 Take photo in <strong>good lighting</strong> (natural light works best)</li>
                <li>📄 Ensure the receipt is <strong>flat and not crumpled</strong></li>
                <li>🔍 Keep the entire receipt <strong>in frame</strong></li>
                <li>✨ Make sure text is <strong>clear and readable</strong></li>
                <li>🌞 Avoid shadows or glare on the receipt</li>
                <li>📸 Hold camera <strong>steady and parallel</strong> to the receipt</li>
            </ul>
            <p style="margin-top: 10px; margin-bottom: 0;"><strong>💡 Pro tip:</strong> Scan receipts right after shopping while they're still flat!</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a receipt image...", 
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear photo of your receipt"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Receipt", use_container_width=True)
            
            # Image quality check
            img_width, img_height = image.size
            if img_width < 800 or img_height < 600:
                st.warning("⚠️ Low resolution image detected. For better results, use a clearer photo.")
            else:
                st.success("✅ Good image quality detected!")
            
            if st.button("🔍 Scan Receipt", type="primary", use_container_width=True):
                with st.spinner("🤖 Scanning your receipt..."):
                    ocr = OCRService()
                    result = ocr.scan_receipt(image)
                    
                    if result['success']:
                        # Add items to scanned_items list
                        for item in result['items']:
                            st.session_state.scanned_items.append({
                                'name': item['name'],
                                'price': item['price'],
                                'category': item['category'],
                                'quantity': item.get('quantity', 1)
                            })
                        st.session_state.scan_result = result
                        st.session_state.items_added = False
                        st.success(f"✅ Successfully scanned {result['total_items']} items from {result['store']}!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to scan receipt: {result.get('error', 'Unknown error')}")
                        st.info("💡 Tip: Try taking a clearer photo with better lighting.")
    
    with col2:
        st.subheader("✍️ Manual Entry")
        st.markdown("Can't scan? Add items manually:")
        
        with st.form("manual_item"):
            col_form1, col_form2 = st.columns(2)
            with col_form1:
                item_name = st.text_input("Item Name", placeholder="e.g., Milk, Bread, Chicken")
                item_price = st.number_input("Price (₹)", min_value=0.0, step=1.0, format="%.2f")
            with col_form2:
                item_category = st.selectbox("Category", 
                    ['groceries', 'produce', 'dairy', 'meat', 'grains', 'canned', 'frozen', 'beverages', 'snacks', 'other'])
                item_quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
            
            if st.form_submit_button("➕ Add Item", use_container_width=True):
                if item_name and item_price > 0:
                    st.session_state.scanned_items.append({
                        'name': item_name,
                        'price': item_price,
                        'category': item_category,
                        'quantity': item_quantity
                    })
                    st.session_state.items_added = False
                    st.success(f"✅ Added {item_name} to list!")
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter item name and price")
        
        st.markdown("---")
        
        # Display success message if items were added
        if st.session_state.items_added and st.session_state.added_message:
            st.success(st.session_state.added_message)
        
        # Display Items Table (Right under Manual Entry)
        if st.session_state.scanned_items:
            st.subheader("📋 Items to Add")
            st.markdown("Review items before adding to pantry:")
            
            # Create DataFrame for display
            df = pd.DataFrame(st.session_state.scanned_items)
            
            # Display simple table
            st.dataframe(
                df[['name', 'price', 'category', 'quantity']],
                use_container_width=True,
                column_config={
                    "name": "Item Name",
                    "price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                    "category": "Category",
                    "quantity": "Qty"
                }
            )
            
            # Show total
            total = sum(item['price'] * item['quantity'] for item in st.session_state.scanned_items)
            st.info(f"💰 **Total Amount:** {format_inr(total)}")
            
            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("✅ Confirm & Save", type="primary", use_container_width=True):
                    firebase = FirebaseService()
                    total_amount = 0
                    
                    for item in st.session_state.scanned_items:
                        total_amount += item['price'] * item['quantity']
                        
                        # Add transaction
                        transaction = {
                            'description': item['name'],
                            'amount': item['price'] * item['quantity'],
                            'category': item['category'],
                            'date': datetime.now()
                        }
                        firebase.add_transaction(st.session_state.user_id, transaction)
                        
                        # Update pantry
                        current_pantry = {i['name'].lower(): i for i in st.session_state.pantry}
                        name_lower = item['name'].lower()
                        
                        if name_lower in current_pantry:
                            current_pantry[name_lower]['quantity'] = current_pantry[name_lower].get('quantity', 1) + item['quantity']
                            current_pantry[name_lower]['last_updated'] = datetime.now()
                            current_pantry[name_lower]['price'] = item['price']
                        else:
                            current_pantry[name_lower] = {
                                'name': item['name'],
                                'category': item['category'],
                                'quantity': item['quantity'],
                                'price': item['price'],
                                'added_date': datetime.now()
                            }
                        
                        st.session_state.pantry = list(current_pantry.values())
                        firebase.update_pantry(st.session_state.user_id, st.session_state.pantry)
                    
                    # Save receipt if scanned
                    if st.session_state.scan_result:
                        receipt_data = {
                            'store': st.session_state.scan_result['store'],
                            'items': st.session_state.scanned_items,
                            'total_amount': total_amount,
                            'scanned_at': datetime.now()
                        }
                        firebase.save_receipt(st.session_state.user_id, receipt_data)
                    
                    # Update budget
                    user = firebase.get_user(st.session_state.user_id)
                    if user:
                        budget = user.get('budget', {})
                        st.session_state.budget = {
                            'monthly': budget.get('monthly', 500),
                            'spent': budget.get('spent', 0) + total_amount,
                            'remaining': budget.get('remaining', 500) - total_amount
                        }
                    
                    # Refresh transactions
                    st.session_state.transactions = firebase.get_transactions(st.session_state.user_id)
                    
                    # Set flag to show success message but keep items
                    st.session_state.items_added = True
                    item_count = len(st.session_state.scanned_items)
                    st.session_state.added_message = f"🎉 Successfully added {item_count} items to your pantry!"
                    
                    # Don't clear the items - keep them visible
                    st.balloons()
                    st.rerun()
            
            with col_btn2:
                if st.button("✏️ Edit Items", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.session_state.items_added = False
                    st.rerun()
            
            with col_btn3:
                if st.button("🗑️ Clear All", use_container_width=True):
                    st.session_state.scanned_items = []
                    st.session_state.scan_result = None
                    st.session_state.edit_mode = False
                    st.session_state.items_added = False
                    st.rerun()
    
    # Edit Mode - Separate section for editing with working remove button
    if st.session_state.edit_mode and st.session_state.scanned_items:
        st.markdown("---")
        st.subheader("✏️ Edit Items")
        st.markdown("Edit or remove items before saving to pantry:")
        
        # Display items with remove buttons using unique keys
        for idx, item in enumerate(st.session_state.scanned_items):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                
                with col1:
                    new_name = st.text_input("Item Name", value=item['name'], key=f"edit_name_{idx}_{item['name']}")
                with col2:
                    new_price = st.number_input("Price (₹)", value=float(item['price']), min_value=0.0, step=1.0, 
                                                key=f"edit_price_{idx}_{item['name']}", format="%.2f")
                with col3:
                    new_category = st.selectbox("Category", 
                        ['groceries', 'produce', 'dairy', 'meat', 'grains', 'canned', 'frozen', 'beverages', 'snacks', 'other'],
                        index=['groceries', 'produce', 'dairy', 'meat', 'grains', 'canned', 'frozen', 'beverages', 'snacks', 'other'].index(item['category']) if item['category'] in ['groceries', 'produce', 'dairy', 'meat', 'grains', 'canned', 'frozen', 'beverages', 'snacks', 'other'] else 0,
                        key=f"edit_cat_{idx}_{item['name']}")
                with col4:
                    new_qty = st.number_input("Quantity", value=item.get('quantity', 1), min_value=1, step=1, 
                                             key=f"edit_qty_{idx}_{item['name']}")
                with col5:
                    if st.button("🗑️ Remove", key=f"remove_{idx}_{item['name']}"):
                        st.session_state.scanned_items.pop(idx)
                        st.session_state.items_added = False
                        st.rerun()
                
                # Update the item in the list
                if idx < len(st.session_state.scanned_items):
                    st.session_state.scanned_items[idx]['name'] = new_name
                    st.session_state.scanned_items[idx]['price'] = new_price
                    st.session_state.scanned_items[idx]['category'] = new_category
                    st.session_state.scanned_items[idx]['quantity'] = new_qty
                
                st.markdown("---")
        
        # Edit action buttons
        col_edit1, col_edit2 = st.columns(2)
        
        with col_edit1:
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.items_added = False
                st.success("✅ Items updated successfully!")
                st.rerun()
        
        with col_edit2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.edit_mode = False
                st.rerun()
    
    # Category breakdown chart (shown when there are items and not in edit mode)
    if st.session_state.scanned_items and not st.session_state.edit_mode:
        st.markdown("---")
        st.subheader("📊 Category Breakdown")
        category_sum = {}
        for item in st.session_state.scanned_items:
            category_sum[item['category']] = category_sum.get(item['category'], 0) + (item['price'] * item['quantity'])
        
        if category_sum:
            category_df = pd.DataFrame(list(category_sum.items()), columns=['category', 'total'])
            fig = px.pie(category_df, values='total', names='category', 
                        title='Spending by Category',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent scans preview
    st.subheader("📜 Recent Scans")
    firebase = FirebaseService()
    recent_receipts = firebase.get_user_receipts(st.session_state.user_id)[:3]
    
    if recent_receipts:
        for receipt in recent_receipts:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"🏪 **{receipt.get('store', 'Store')}**")
                with col2:
                    date = receipt.get('scanned_at', datetime.now())
                    if isinstance(date, str):
                        date = datetime.fromisoformat(date)
                    st.write(f"📅 {date.strftime('%d %b %Y')}")
                with col3:
                    total = receipt.get('total_amount', sum(item['price'] * item.get('quantity', 1) for item in receipt.get('items', [])))
                    st.write(f"💰 {format_inr(total)}")
                st.divider()
    else:
        st.info("No recent scans. Upload your first receipt to get started!")