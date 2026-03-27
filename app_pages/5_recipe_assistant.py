# pages/5_recipe_assistant.py
import streamlit as st
from services.recipe_ai import RecipeAIService
from services.firebase import FirebaseService
from components.theme import apply_theme
from datetime import datetime

def show():
    """Recipe Assistant Page"""
    apply_theme()
    
    st.markdown('<h1 class="main-header">Recipe Assistant</h1>', unsafe_allow_html=True)
    st.markdown("Get personalized recipe suggestions based on your pantry", text_alignment="center")
    
    if not st.session_state.pantry:
        st.warning("🍽️ Your pantry is empty! Add some ingredients first to get recipe recommendations.")
        return
    
    # Recipe preferences
    st.subheader("🎯 Recipe Preferences")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cuisine = st.selectbox("Cuisine Preference", 
                               ["Any", "Italian", "Asian", "Mexican", "American", "Indian", "French", "Thai", "Chinese"])
    
    with col2:
        dietary = st.selectbox("Dietary Restriction",
                               ["None", "Vegetarian", "Vegan", "Gluten-Free", "Keto", "High-Protein"])
    
    with col3:
        max_time = st.selectbox("Max Prep Time", 
                                ["Any", "15 mins", "30 mins", "45 mins", "60 mins"])
    
    # Display available ingredients
    st.subheader("📦 Available Ingredients")
    ingredients_list = [item['name'] for item in st.session_state.pantry]
    
    # Display ingredients in a nice grid
    cols = st.columns(4)
    for idx, ingredient in enumerate(ingredients_list):
        with cols[idx % 4]:
            st.markdown(f'<span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; margin: 0.2rem; color: white;">{ingredient}</span>', unsafe_allow_html=True)
    
    if len(ingredients_list) > 12:
        st.caption(f"... and {len(ingredients_list) - 12} more ingredients")
    
    st.markdown("---")
    
    # Generate recipes button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("✨ Generate Recipes", use_container_width=True):
            with st.spinner("🧠 Creating delicious recipes for you..."):
                recipe_ai = RecipeAIService()
                
                preferences = {
                    'cuisine': None if cuisine == "Any" else cuisine,
                    'dietary': None if dietary == "None" else dietary,
                    'max_time': None if max_time == "Any" else max_time.split()[0]
                }
                
                recipes = recipe_ai.generate_recipes(ingredients_list, preferences)
                
                if recipes:
                    st.success(f"✨ Generated {len(recipes)} delicious recipes for you!")
                    st.session_state.generated_recipes = recipes
                    
                    # Display recipes vertically (one after another)
                    for recipe in recipes:
                        difficulty_color = {
                            'Easy': '#FFD966',
                            'Medium': '#FFB347',
                            'Hard': '#FF6B6B'
                        }.get(recipe.get('difficulty', 'Medium'), '#FFD966')
                        
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border-radius: 15px;
                            padding: 1.2rem;
                            margin-bottom: 1rem;
                            color: white;
                            height: 100%;
                            width: 100%;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                            border-left: 4px solid #FF6B6B;
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                                <h3 style="margin: 0; color: white; font-size: 1.1rem;">🍳 {recipe.get('name', 'Recipe')}</h3>
                                <span style="
                                    background: linear-gradient(135deg, #FF6B6B, #FF8E53);
                                    color: white;
                                    padding: 0.2rem 0.6rem;
                                    border-radius: 20px;
                                    font-size: 0.7rem;
                                    font-weight: bold;">
                                    {recipe.get('match_percentage', 0):.0f}%
                                </span>
                            </div>
                            <div style="display: flex; gap: 1rem; margin-bottom: 0.5rem; font-size: 0.75rem;">
                                <span>⏱️ {recipe.get('prep_time', 'N/A')} mins</span>
                                <span>📊 <span style="color: {difficulty_color};">{recipe.get('difficulty', 'Medium')}</span></span>
                            </div>
                            <p style="color: rgba(255,255,255,0.9); font-size: 0.8rem; line-height: 1.4;">
                                {recipe.get('description', 'A delicious recipe made with your available ingredients.')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander(f"📖 View Full Recipe", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**🥘 Ingredients:**")
                                for ing in recipe.get('ingredients', []):
                                    if ing.lower() in [i.lower() for i in ingredients_list]:
                                        st.markdown(f"✅ {ing}")
                                    else:
                                        st.markdown(f"❌ {ing}")
                            
                            with col2:
                                st.markdown("**📖 Instructions:**")
                                for i, step in enumerate(recipe.get('instructions', []), 1):
                                    st.markdown(f"{i}. {step}")
                else:
                    st.warning("😕 Couldn't generate recipes. Please try again with different preferences.")
    
    st.markdown("---")
    
    # Quick Tips
    st.subheader("💡 Pro Tips for Better Recipes")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 12px;
            color: white;
            border-left: 4px solid #FF6B6B;">
            <h4 style="color: white; margin-bottom: 0.5rem;">🎯 Get the best results:</h4>
            <ul style="margin: 0; padding-left: 1rem;">
                <li>Add more ingredients to your pantry</li>
                <li>Select specific cuisine preferences</li>
                <li>Choose dietary restrictions that match your needs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tip_col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 12px;
            color: white;
            border-left: 4px solid #FF6B6B;">
            <h4 style="color: white; margin-bottom: 0.5rem;">🍳 Recipe Suggestions:</h4>
            <ul style="margin: 0; padding-left: 1rem;">
                <li>Save recipes you like for quick access</li>
                <li>Try different cuisine combinations</li>
                <li>Use leftover ingredients for creative dishes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)