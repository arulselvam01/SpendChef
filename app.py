# app.py
import streamlit as st
import os
import sys
import importlib
from dotenv import load_dotenv

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SpendChef - Smart Kitchen Assistant",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'pantry' not in st.session_state:
        st.session_state.pantry = []
    if 'receipts' not in st.session_state:
        st.session_state.receipts = []
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'budget' not in st.session_state:
        st.session_state.budget = {'monthly': 500, 'spent': 0, 'remaining': 500}
    if 'saved_recipes' not in st.session_state:
        st.session_state.saved_recipes = []
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False

init_session_state()

# Function to load pages dynamically
def load_page(page_number, page_name):
    """Load a page module dynamically"""
    try:
        module_name = f"app_pages.{page_number}_{page_name}"
        module = importlib.import_module(module_name)
        return module.show
    except Exception as e:
        return None

# Landing Page (Welcome Screen)
def landing_page():
    """Welcome landing page shown before login"""
    
    # Hero Section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1 style="font-size: 4rem; margin: 0;">🍳</h1>
            <h1 style="font-size: 5rem; background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                SpendChef
            </h1>
            <p style="font-size: 1.2rem; color: #5a6c7e;">Your AI-Powered Kitchen Assistant</p>
            <p style="font-size: 1rem; color: #7f8c8d;">Smart Receipt Scanning • AI Recipe Generator • Budget Tracking • Pantry Management</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login Button
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
    
    st.markdown("---")
    
    # Features Section
    st.markdown("### ✨ What SpendChef Can Do For You")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2>📸</h2>
            <h4>Scan Receipts</h4>
            <p style="color: #7f8c8d;">Upload receipts and automatically track expenses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2>🤖</h2>
            <h4>AI Recipes</h4>
            <p style="color: #7f8c8d;">Get recipe suggestions based on your pantry</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2>💰</h2>
            <h4>Budget Tracking</h4>
            <p style="color: #7f8c8d;">Stay on top of your food spending</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2>📦</h2>
            <h4>Pantry Manager</h4>
            <p style="color: #7f8c8d;">Never forget what's in your kitchen</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("### 🚀 How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center;">
            <h4>Scan Receipts</h4>
            <p>Upload grocery receipts and let SpendChef extract items</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <h4>Build Pantry</h4>
            <p>Automatically track what you have at home</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center;">
            <h4>Get Recipes</h4>
            <p>Discover delicious meals from your ingredients</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # About Section
    st.markdown("### 📖 About SpendChef")
    st.markdown("""
    SpendChef is an intelligent kitchen assistant that helps you manage your food expenses, 
    track your pantry inventory, and discover delicious recipes using what you already have. 
    Designed to reduce food waste, SpendChef makes cooking smarter and more enjoyable.
    
    **Key Features:**
    - 📸 **Smart Receipt Scanning**: Upload receipts and automatically extract items and prices
    - 🤖 **Recipe Generation**: Get personalized recipes based on your available ingredients
    - 💰 **Budget Tracking**: Monitor your food spending and stay within your budget
    - 📦 **Pantry Management**: Keep track of what you have and when it expires
    - 💡 **Waste Reduction**: Get creative recipes for leftover ingredients
    
    Made with ❤️ for food lovers everywhere.
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #95a5a6; padding: 1rem;">
        <p>🍳 SpendChef - Smart Kitchen Assistant | © 2026 | Track, Cook, Save, Repeat</p>
    </div>
    """, unsafe_allow_html=True)

# Main app navigation
def main():
    """Main app with page routing"""
    
    # If not authenticated and not showing login, show landing page
    if not st.session_state.authenticated and not st.session_state.show_login:
        landing_page()
        return
    
    # Show login page if requested
    if not st.session_state.authenticated and st.session_state.show_login:
        login_func = load_page(1, "login")
        if login_func:
            login_func()
        return
    
    # Authenticated user - show dashboard with sidebar
    if st.session_state.authenticated:
        with st.sidebar:
            # Custom CSS for sidebar
            st.markdown("""
            <style>
            .sidebar-logo {
                text-align: center;
                padding: 1rem 0;
            }
            .user-info {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 1rem;
                margin: 1rem 0;
                text-align: left;
                color: white;
            }
            .user-name {
                font-size: 1.1rem;
                font-weight: bold;
                margin: 0;
            }
            .user-email {
                font-size: 0.8rem;
                opacity: 1;
                margin: 0;
            }
            .nav-item {
                padding: 0.5rem;
                margin: 0.2rem 0;
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            .nav-item:hover {
                background-color: rgba(255, 107, 107, 0.1);
                transform: translateX(5px);
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Logo/Brand
            st.markdown("""
            <div class="sidebar-logo">
                <h2 style="font-size: 2rem; margin: 0;">🍳</h2>
                <h1 style="font-size: 2.8rem; background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                SpendChef</h1>          
                <p style="font-size: 1rem; color: #95a5a6;">Smart Kitchen Assistant</p>
            </div>
            """, unsafe_allow_html=True)
            
            # User Info Card
            st.markdown(f"""
            <div class="user-info">
                <p class="user-name">👤 {st.session_state.user_name}</p>
                <p class="user-email">📧 {st.session_state.user_email}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            
            # Navigation menu
            from streamlit_option_menu import option_menu
            selected = option_menu(
                menu_title="Menu",
                options=["Dashboard", "Scan Receipt", "Pantry", "Recipe Assistant", "Insights", "Settings"],
                icons=["speedometer2", "camera", "box", "book", "graph-up", "gear"],
                menu_icon="list",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": "#A855F7", "font-size": "20px"},
                    "nav-link": {
                        "font-size": "15px", 
                        "text-align": "left", 
                        "margin": "5px 0",
                        "padding": "px",
                        "border-radius": "8px",
                        "color": "#E7ECF1"
                    },
                    "nav-link-selected": {
                        "background-color": "#A855F7", 
                        "color": "white",
                        "font-weight": "bold"
                    },
                    "nav-link-hover": {
                        "background-color": "rgba(255, 107, 107, 0.1)",
                        "color": "#A855F7"
                    }
                }
            )

            # Check if there's a current_page set from quick actions
            if st.session_state.get('current_page'):
                if st.session_state.current_page == "Scan Receipt":
                    selected = "Scan Receipt"
                elif st.session_state.current_page == "Recipe Assistant":
                    selected = "Recipe Assistant"
                elif st.session_state.current_page == "Pantry":
                    selected = "Pantry"
                elif st.session_state.current_page == "Settings":
                    selected = "Settings"
                # Clear the current_page after using it
                st.session_state.current_page = None
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.user_email = None
                st.session_state.user_name = None
                st.session_state.show_login = False
                st.rerun()
        
        # Page routing based on selection
        if selected == "Dashboard":
            home_func = load_page(2, "home")
            if home_func:
                home_func()
        elif selected == "Scan Receipt":
            scan_func = load_page(3, "scan_receipt")
            if scan_func:
                scan_func()
        elif selected == "Pantry":
            pantry_func = load_page(4, "pantry")
            if pantry_func:
                pantry_func()
        elif selected == "Recipe Assistant":
            recipe_func = load_page(5, "recipe_assistant")
            if recipe_func:
                recipe_func()
        elif selected == "Insights":
            insights_func = load_page(6, "insights")
            if insights_func:
                insights_func()
        elif selected == "Settings":
            settings_func = load_page(7, "settings")
            if settings_func:
                settings_func()

if __name__ == "__main__":
    main()