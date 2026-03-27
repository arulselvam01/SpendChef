# pages/1_login.py
import streamlit as st
from services.firebase import FirebaseService

def show():
    """Login page"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>🍳 SpendChef</h1>
            <p>Sign in to continue</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Login", type="primary", use_container_width=True):
                    if email and password:
                        firebase = FirebaseService()
                        user_id = email.replace('@', '_').replace('.', '_')
                        user = firebase.get_user(user_id)
                        
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user_id
                            st.session_state.user_email = email
                            st.session_state.user_name = user.get('name', 'User')
                            
                            # Load user data
                            st.session_state.pantry = firebase.get_pantry(user_id)
                            st.session_state.receipts = firebase.get_user_receipts(user_id)
                            st.session_state.transactions = firebase.get_transactions(user_id)
                            
                            budget = user.get('budget', {})
                            st.session_state.budget = {
                                'monthly': budget.get('monthly', 500),
                                'spent': budget.get('spent', 0),
                                'remaining': budget.get('remaining', 500)
                            }
                            
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("User not found. Please sign up first.")
                    else:
                        st.warning("Please enter email and password")
            
            with col2:
                if st.button("← Back", use_container_width=True):
                    st.session_state.show_login = False
                    st.rerun()
        
        with tab2:
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm Password", type="password")
            
            if st.button("Create Account", type="primary", use_container_width=True):
                if password != confirm:
                    st.error("Passwords do not match")
                elif email and password and name:
                    firebase = FirebaseService()
                    user_id = email.replace('@', '_').replace('.', '_')
                    
                    if firebase.get_user(user_id):
                        st.error("User already exists. Please login.")
                    else:
                        firebase.create_user(email, name, password)
                        st.success("Account created successfully! Please login.")
                else:
                    st.warning("Please fill all fields")