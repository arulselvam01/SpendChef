# pages/4_pantry.py
import streamlit as st
import pandas as pd
from datetime import datetime
from services.firebase import FirebaseService
from services.pantry import PantryService
from components.theme import apply_theme
from utils.helpers import format_currency

def format_inr(amount):
    """Format amount in Indian Rupees"""
    return f"₹{amount:,.2f}"

def show():
    """Pantry Management Page"""
    apply_theme()
    
    st.markdown('<h1 class="main-header">Pantry Management</h1>', unsafe_allow_html=True)
    
    pantry_service = PantryService()
    firebase = FirebaseService()
    
    # Refresh pantry data from Firebase
    if st.session_state.user_id:
        st.session_state.pantry = firebase.get_pantry(st.session_state.user_id)
    
    # Add new ingredient
    st.subheader("➕ Add New Ingredient")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_item = st.text_input("Ingredient Name", placeholder="e.g., Tomato, Chicken, Rice")
    with col2:
        new_category = st.selectbox("Category", 
            ['produce', 'protein', 'dairy', 'grains', 'canned', 'spices', 'beverages', 'snacks', 'frozen', 'other'])
    with col3:
        new_quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
    
    # Center the button
    col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])
    with col2_btn:
        if st.button("➕ Add to Pantry", type="primary", use_container_width=True):
            if new_item:
                ingredient = {
                    'name': new_item,
                    'category': new_category,
                    'quantity': new_quantity,
                    'added_date': datetime.now()
                }
                st.session_state.pantry = pantry_service.add_ingredient(st.session_state.pantry, ingredient)
                firebase.update_pantry(st.session_state.user_id, st.session_state.pantry)
                st.success(f"✅ Added {new_item} to pantry!")
                st.rerun()
            else:
                st.warning("⚠️ Please enter ingredient name")
    
    st.markdown("---")
    
    # Display pantry items
    if st.session_state.pantry:
        # Stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_items = len(st.session_state.pantry)
            st.metric("📦 Total Items", total_items)
        
        with col2:
            categories = len(set(item.get('category', 'other') for item in st.session_state.pantry))
            st.metric("🏷️ Categories", categories)
        
        with col3:
            total_value = sum(item.get('price', 0) for item in st.session_state.pantry)
            st.metric("💰 Total Value", format_inr(total_value))
        
        # Category breakdown - FIXED
        try:
            category_stats = pantry_service.get_category_stats(st.session_state.pantry)
        except Exception as e:
            st.warning(f"Error loading category stats: {e}")
            category_stats = {}
        
        # Only show if there are categories with items
        if category_stats and any(count > 0 for count in category_stats.values()):
            st.subheader("📊 Pantry Breakdown by Category")
            
            # Filter only categories with count > 0
            active_categories = {k: v for k, v in category_stats.items() if v > 0}
            if active_categories:
                cols = st.columns(min(4, len(active_categories)))
                for idx, (category, count) in enumerate(active_categories.items()):
                    with cols[idx % 4]:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    border-radius: 10px; padding: 1rem; text-align: center; color: white;">
                            <h2 style="margin: 0; font-size: 2rem;">{count}</h2>
                            <p style="margin: 0; font-size: 0.9rem;">{category.title()}</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Search and filter
        st.subheader("🔍 Your Ingredients")
        
        search = st.text_input("Search ingredients", placeholder="e.g., chicken, rice...")
        
        # Get unique categories for filter
        unique_categories = list(set(item.get('category', 'other') for item in st.session_state.pantry))
        category_filter = st.selectbox("Filter by category", ["All"] + sorted(unique_categories))
        
        filtered_items = st.session_state.pantry
        if search:
            filtered_items = [i for i in filtered_items if search.lower() in i['name'].lower()]
        if category_filter != "All":
            filtered_items = [i for i in filtered_items if i.get('category', 'other') == category_filter]
        
        # Show result count
        st.caption(f"Showing {len(filtered_items)} of {len(st.session_state.pantry)} items")
        
        # Display ingredients in grid
        if filtered_items:
            # Sort by name
            filtered_items.sort(key=lambda x: x['name'].lower())
            
            cols = st.columns(3)
            for idx, item in enumerate(filtered_items):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"""
                        <div style="background: #A855F7; border-radius: 10px; padding: 1rem; 
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem;
                                    border-left: 4px solid #FF6B6B;">
                            <h4 style="margin: 0 0 0.5rem 0;">{item['name']}</h4>
                            <p style="margin: 0.2rem 0;"><strong>📦 Quantity:</strong> {item.get('quantity', 1)}</p>
                            <p style="margin: 0.2rem 0;"><strong>🏷️ Category:</strong> {item.get('category', 'other').title()}</p>
                            <small style="color: #95a5a6;">Added: {item.get('added_date', datetime.now()).strftime('%d %b %Y') if isinstance(item.get('added_date'), datetime) else 'Recently'}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"📉 Use", key=f"use_{item['name']}_{idx}", use_container_width=True):
                                # Decrease quantity
                                new_qty = item.get('quantity', 1) - 1
                                if new_qty <= 0:
                                    st.session_state.pantry = pantry_service.remove_ingredient(
                                        st.session_state.pantry, item['name']
                                    )
                                    st.success(f"✅ Removed {item['name']} from pantry")
                                else:
                                    st.session_state.pantry = pantry_service.update_quantity(
                                        st.session_state.pantry, item['name'], new_qty
                                    )
                                    st.success(f"📉 Used 1 {item['name']}. Remaining: {new_qty}")
                                firebase.update_pantry(st.session_state.user_id, st.session_state.pantry)
                                st.rerun()
                        
                        with col2:
                            if st.button(f"🗑️ Remove", key=f"remove_{item['name']}_{idx}", use_container_width=True):
                                st.session_state.pantry = pantry_service.remove_ingredient(
                                    st.session_state.pantry, item['name']
                                )
                                firebase.update_pantry(st.session_state.user_id, st.session_state.pantry)
                                st.success(f"🗑️ Removed {item['name']} from pantry")
                                st.rerun()
        else:
            st.info("🔍 No ingredients found matching your search")
    else:
        st.info("📦 Your pantry is empty. Scan receipts or add items manually to get started!")
    
    st.markdown("---")
    
    # Current Inventory Section - Shows items from Firebase/database
    st.subheader("📋 Current Inventory Summary")
    
    # Get latest pantry data from Firebase
    if st.session_state.user_id:
        current_pantry = firebase.get_pantry(st.session_state.user_id)
    else:
        current_pantry = st.session_state.pantry
    
    if current_pantry:
        # Create a dataframe for inventory
        inventory_data = []
        for item in current_pantry:
            item_value = item.get('price', 0) * item.get('quantity', 1)
            inventory_data.append({
                'Ingredient': item['name'],
                'Category': item.get('category', 'other').title(),
                'Quantity': item.get('quantity', 1),
                'Unit Price': format_inr(item.get('price', 0)) if item.get('price', 0) > 0 else 'N/A',
                'Total Value': format_inr(item_value) if item_value > 0 else 'N/A',
                'Added On': item.get('added_date', datetime.now()).strftime('%d %b %Y') if isinstance(item.get('added_date'), datetime) else 'Recently'
            })
        
        # Display as dataframe
        df = pd.DataFrame(inventory_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export option
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Export Inventory as CSV",
                data=csv,
                file_name=f"pantry_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Quick stats
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_value_items = [item for item in current_pantry if item.get('price', 0) * item.get('quantity', 1) > 500]
            st.metric("💎 High Value Items (>₹500)", len(high_value_items))
        
        with col2:
            # Calculate most common category safely
            category_counts = {}
            for item in current_pantry:
                cat = item.get('category', 'other')
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            if category_counts:
                most_common = max(category_counts.items(), key=lambda x: x[1])[0].title()
            else:
                most_common = 'None'
            st.metric("🏆 Most Common Category", most_common)
        
        with col3:
            if current_pantry:
                avg_quantity = sum(item.get('quantity', 1) for item in current_pantry) / len(current_pantry)
            else:
                avg_quantity = 0
            st.metric("📊 Avg Quantity per Item", f"{avg_quantity:.1f}")
        
        # Refresh button
        st.markdown("---")
        if st.button("🔄 Refresh Inventory", use_container_width=True):
            st.session_state.pantry = firebase.get_pantry(st.session_state.user_id)
            st.rerun()
        
    else:
        st.info("📭 No items in inventory. Add some ingredients to see your inventory summary!")
        st.markdown("""
        ### 📝 How to add items:
        - **Scan Receipts**: Go to Scan Receipt page and upload your grocery receipt
        - **Manual Entry**: Use the form above to add items one by one
        - **Quick Add**: Click the "➕ Add to Pantry" button above
        """)
    
    st.markdown("---")
    st.caption("💡 Tip: Keep your pantry organized by regularly reviewing and updating inventory")