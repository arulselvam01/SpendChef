# pages/7_settings.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from services.firebase import FirebaseService
from components.theme import apply_theme

def format_inr(amount):
    """Format amount in Indian Rupees"""
    return f"₹{amount:,.2f}"

def show():
    """Settings Page"""
    apply_theme()
    
    st.markdown('<h1 class="main-header">Settings</h1>', unsafe_allow_html=True)
    st.markdown("Customize your SpendChef experience")
    
    firebase = FirebaseService()
    user = firebase.get_user(st.session_state.user_id)
    
    if not user:
        st.error("User not found")
        return
    
    # Create tabs for different settings
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Budget", 
        "🍽️ Food Preferences", 
        "🔔 Notifications", 
        "📊 Data Management",
        "🗑️ Delete Data"
    ])
    
    # Tab 1: Budget Settings
    with tab1:
        st.subheader("💰 Budget Settings")
        st.markdown("Set your monthly food budget and track your spending")
        
        # Get current budget from session state
        current_budget = st.session_state.budget.get('monthly', 500)
        current_spent = st.session_state.budget.get('spent', 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_budget = st.number_input(
                "Monthly Food Budget (₹)", 
                min_value=100, 
                max_value=100000, 
                value=int(current_budget),
                step=500,
                help="Set your monthly budget for groceries and food expenses"
            )
        
        with col2:
            remaining = new_budget - current_spent if new_budget > current_spent else 0
            st.metric("Current Spending", format_inr(current_spent))
            st.metric("Budget Remaining", format_inr(remaining))
        
        if new_budget != current_budget:
            if st.button("💾 Update Budget", type="primary", use_container_width=True):
                # Update in Firebase
                firebase.update_budget(st.session_state.user_id, new_budget)
                
                # Update session state
                st.session_state.budget['monthly'] = new_budget
                st.session_state.budget['remaining'] = new_budget - current_spent
                
                st.success(f"✅ Budget updated to {format_inr(new_budget)}!")
                st.rerun()
        
        # Spending insights
        st.markdown("---")
        st.markdown("### 📊 Spending Insights")
        
        if st.session_state.transactions:
            monthly_spent = st.session_state.budget['spent']
            budget_percentage = (monthly_spent / new_budget) * 100 if new_budget > 0 else 0
            
            if budget_percentage > 100:
                st.error(f"⚠️ You've exceeded your budget by {format_inr(monthly_spent - new_budget)}")
            elif budget_percentage > 80:
                st.warning(f"⚠️ You've used {budget_percentage:.0f}% of your budget. Consider reducing spending.")
            else:
                st.success(f"✅ You're on track! Used {budget_percentage:.0f}% of your budget.")
            
            st.info(f"📅 Total spent this month: {format_inr(monthly_spent)}")
        else:
            st.info("No spending data yet. Scan receipts to track your spending!")
    
    # Tab 2: Food Preferences
    with tab2:
        st.subheader("🍽️ Food Preferences")
        st.markdown("Customize your recipe recommendations")
        
        # Get current preferences
        user_preferences = user.get('preferences', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🍳 Cuisine Preferences")
            cuisine_options = ["Italian", "Asian", "Mexican", "American", "Indian", "Mediterranean", "French", "Thai", "Japanese"]
            selected_cuisines = st.multiselect(
                "Select your favorite cuisines",
                cuisine_options,
                default=user_preferences.get('cuisines', [])
            )
        
        with col2:
            st.markdown("### 🥗 Dietary Restrictions")
            diet_options = ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Paleo", "Low-Carb", "High-Protein"]
            dietary_restrictions = st.multiselect(
                "Select dietary restrictions",
                diet_options,
                default=user_preferences.get('dietary', [])
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⏱️ Cooking Preferences")
            max_prep_time = st.slider(
                "Maximum prep time (minutes)",
                min_value=10,
                max_value=120,
                value=user_preferences.get('max_prep_time', 45),
                step=5
            )
        
        with col2:
            st.markdown("### 🔥 Spice Level")
            spice_level = st.select_slider(
                "Preferred spice level",
                options=["Mild", "Medium", "Hot", "Very Hot"],
                value=user_preferences.get('spice_level', 'Medium')
            )
        
        st.markdown("---")
        
        st.markdown("### ❌ Allergies")
        allergies = st.text_area(
            "List any food allergies (comma separated)",
            value=", ".join(user_preferences.get('allergies', [])) if user_preferences.get('allergies') else "",
            placeholder="e.g., peanuts, shellfish, dairy",
            help="We'll exclude recipes containing these ingredients"
        )
        
        if st.button("💾 Save Food Preferences", type="primary", use_container_width=True):
            # Update preferences
            updated_preferences = {
                'cuisines': selected_cuisines,
                'dietary': dietary_restrictions,
                'max_prep_time': max_prep_time,
                'spice_level': spice_level,
                'allergies': [a.strip() for a in allergies.split(",")] if allergies else []
            }
            
            firebase.update_user_settings(st.session_state.user_id, updated_preferences)
            st.success("✅ Food preferences saved! Your recipe recommendations will now be personalized.")
            st.balloons()
    
    # Tab 3: Notifications
    with tab3:
        st.subheader("🔔 Notification Settings")
        st.markdown("Manage your notification preferences")
        
        user_settings = user.get('settings', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📧 Email Notifications")
            email_notifications = st.checkbox(
                "Receive email notifications",
                value=user_settings.get('email_notifications', True)
            )
            
            expiry_alerts = st.checkbox(
                "Expiring items alerts",
                value=user_settings.get('expiry_alerts', True),
                help="Get notified when items are about to expire"
            )
        
        with col2:
            st.markdown("### 🍳 Recipe Updates")
            recipe_recommendations = st.checkbox(
                "Weekly recipe recommendations",
                value=user_settings.get('recipe_recommendations', True)
            )
            
            budget_alerts = st.checkbox(
                "Budget alerts",
                value=user_settings.get('budget_alerts', True),
                help="Get notified when you're close to your budget limit"
            )
        
        st.markdown("---")
        
        st.markdown("### ⏰ Reminder Schedule")
        reminder_day = st.selectbox(
            "Weekly reminder day",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(
                user_settings.get('reminder_day', 'Monday')
            )
        )
        
        if st.button("💾 Save Notification Settings", type="primary", use_container_width=True):
            updated_settings = {
                'email_notifications': email_notifications,
                'expiry_alerts': expiry_alerts,
                'recipe_recommendations': recipe_recommendations,
                'budget_alerts': budget_alerts,
                'reminder_day': reminder_day
            }
            
            firebase.update_user_settings(st.session_state.user_id, updated_settings)
            st.success("✅ Notification settings saved!")
    
    # Tab 4: Data Management
    with tab4:
        st.subheader("📊 Data Management")
        st.markdown("Export and manage your data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📥 Export Data")
            st.write("Export all your SpendChef data including:")
            st.write("- User profile and settings")
            st.write("- Transaction history")
            st.write("- Scanned receipts")
            st.write("- Pantry items")
            
            if st.button("📥 Export All Data", type="primary", use_container_width=True):
                data = firebase.export_user_data(st.session_state.user_id)
                
                # Convert to JSON
                json_data = json.dumps(data, default=str, indent=2)
                
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"spendchef_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                # Also offer CSV export for transactions
                if st.session_state.transactions:
                    df = pd.DataFrame(st.session_state.transactions)
                    csv_data = df.to_csv(index=False)
                    
                    st.download_button(
                        label="Download Transactions CSV",
                        data=csv_data,
                        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                st.success("Data ready for download!")
        
        with col2:
            st.markdown("### 📋 Receipt Management")
            st.write("Manage your scanned receipts")
            
            receipts = st.session_state.receipts
            
            if receipts:
                st.write(f"Total receipts: {len(receipts)}")
                
                for receipt in receipts[:3]:
                    with st.expander(f"📄 {receipt.get('store', 'Receipt')} - {receipt.get('scanned_at', datetime.now()).strftime('%d %b %Y') if isinstance(receipt.get('scanned_at'), datetime) else 'Unknown'}"):
                        st.write(f"**Store:** {receipt.get('store', 'Unknown')}")
                        st.write(f"**Total Items:** {receipt.get('total_items', 0)}")
                        st.write(f"**Total Amount:** {format_inr(receipt.get('total_amount', 0))}")
                        
                        st.write("**Items:**")
                        for item in receipt.get('items', [])[:5]:
                            st.write(f"- {item['name']}: {format_inr(item['price'])}")
                        
                        if st.button(f"🗑️ Delete Receipt", key=f"delete_receipt_{receipt.get('id')}"):
                            firebase.delete_receipt(receipt.get('id'))
                            st.session_state.receipts = firebase.get_user_receipts(st.session_state.user_id)
                            st.success("Receipt deleted!")
                            st.rerun()
                
                if len(receipts) > 3:
                    st.info(f"And {len(receipts) - 3} more receipts...")
            else:
                st.info("No receipts found")
    
    # Tab 5: Delete Data
    with tab5:
        st.subheader("🗑️ Delete Data")
        st.warning("⚠️ Warning: This action cannot be undone!")
        
        st.markdown("### What would you like to delete?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            delete_transactions = st.checkbox("Delete all transactions")
            delete_receipts = st.checkbox("Delete all receipts")
        
        with col2:
            delete_pantry = st.checkbox("Delete all pantry items")
            delete_all_data = st.checkbox("Delete ALL data (including profile)")
        
        st.markdown("---")
        
        if delete_all_data:
            st.error("⚠️ This will delete ALL your data including profile. This cannot be undone!")
        
        confirmation = st.text_input("Type 'DELETE' to confirm deletion:")
        
        if st.button("🗑️ Delete Selected Data", type="secondary", use_container_width=True):
            if confirmation == "DELETE":
                # Delete selected data
                if delete_all_data:
                    st.warning("This would delete all user data in production")
                    st.info("Feature implementation pending - would delete user profile and all associated data")
                else:
                    if delete_transactions:
                        st.session_state.transactions = []
                        st.success("✅ Transactions deleted!")
                    
                    if delete_receipts:
                        for receipt in st.session_state.receipts:
                            firebase.delete_receipt(receipt.get('id'))
                        st.session_state.receipts = []
                        st.success("✅ Receipts deleted!")
                    
                    if delete_pantry:
                        st.session_state.pantry = []
                        firebase.update_pantry(st.session_state.user_id, [])
                        st.success("✅ Pantry items deleted!")
                    
                    st.rerun()
            else:
                st.error("❌ Please type 'DELETE' to confirm")
    
    st.markdown("---")
    st.caption("🍳 SpendChef v1.0 - Your AI-Powered Kitchen Assistant")