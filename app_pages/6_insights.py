# pages/6_insights.py
import streamlit as st
from services.recipe_ai import RecipeAIService
from services.firebase import FirebaseService
from components.theme import apply_theme
from utils.helpers import format_currency

def format_inr(amount):
    """Format amount in Indian Rupees"""
    return f"₹{amount:,.2f}"

def show():
    """Insights Page - Recipes with leftover ingredients"""
    apply_theme()
    
    st.markdown('<h1 class="main-header">Smart Insights</h1>', unsafe_allow_html=True)
    
    if not st.session_state.pantry:
        st.warning("📦 Your pantry is empty. Add ingredients to get insights!")
        return
    
    # Leftover ingredients section
    st.subheader("🍽️ Recipes with Your Leftover Ingredients")
    
    ingredients_list = [item['name'] for item in st.session_state.pantry]
    
    recipe_ai = RecipeAIService()
    
    with st.spinner("🤖 Finding creative ways to use your leftovers..."):
        preferences = {'cuisine': "Any", 'dietary': "None", 'max_time': None}
        recipes = recipe_ai.generate_recipes(ingredients_list, preferences)
        
        if recipes:
            leftover_recipes = [r for r in recipes if r.get('match_percentage', 0) > 50]
            
            if leftover_recipes:
                recipe_cols = st.columns(3)
                for idx, recipe in enumerate(leftover_recipes[:3]):
                    with recipe_cols[idx % 3]:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border-radius: 15px;
                            padding: 1.2rem;
                            margin-bottom: 1rem;
                            color: white;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                            border-left: 4px solid #FF6B6B;
                            height: 100%;
                            min-height: 260px;
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;">
                            <div>
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;">
                                    <h3 style="margin: 0; color: white; font-size: 1rem;">🍳 {recipe.get('name', 'Recipe')}</h3>
                                    <span style="
                                        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
                                        padding: 0.2rem 0.6rem;
                                        border-radius: 20px;
                                        font-size: 0.7rem;">
                                        {recipe.get('match_percentage', 0):.0f}%
                                    </span>
                                </div>
                                <div style="display: flex; gap: 0.8rem; font-size: 0.7rem;">
                                    <span>✨ {len(recipe.get('available_ingredients', []))} ingredients</span>
                                    <span>⏱️ {recipe.get('prep_time', 'N/A')} mins</span>
                                </div>
                                <p style="font-size: 0.75rem;">
                                    {recipe.get('description', '')[:90]}...
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("📖 View Recipe"):
                            st.markdown("**✅ Available:**")
                            for ing in recipe.get('available_ingredients', []):
                                st.markdown(f"- {ing}")
                            
                            if recipe.get('missing_ingredients'):
                                st.markdown("**❌ Missing:**")
                                for ing in recipe.get('missing_ingredients', []):
                                    st.markdown(f"- {ing}")
                            
                            st.markdown("**📖 Steps:**")
                            for i, step in enumerate(recipe.get('instructions', []), 1):
                                st.markdown(f"{i}. {step}")
            else:
                st.info("✨ Try Recipe Assistant for more ideas!")
        else:
            st.info("💡 No recipes found")

    st.markdown("---")
    
    # Waste reduction tips
    st.subheader("♻️ Waste Reduction Tips")
    
    tips = [
        "🥬 Store herbs in water",
        "🍌 Freeze bananas",
        "🥕 Save scraps for broth",
        "🍞 Freeze bread",
        "🌿 Regrow onions",
        "🥑 Refrigerate avocados"
    ]
    
    col1, col2 = st.columns(2)
    for idx, tip in enumerate(tips):
        with col1 if idx % 2 == 0 else col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 12px;
                padding: 0.8rem;
                margin: 0.5rem 0;
                color: white;
                font-size: 0.85rem;">
                💡 {tip}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Shopping suggestions
    st.subheader("🛒 Smart Shopping Suggestions")
    
    if 'recipes' in locals() and recipes:
        all_missing = []
        for recipe in recipes[:5]:
            all_missing.extend(recipe.get('missing_ingredients', []))
        
        from collections import Counter
        common_missing = Counter(all_missing).most_common(5)
        
        if common_missing:
            st.markdown("**Buy these to unlock more recipes:**")
            for ingredient, count in common_missing:
                st.markdown(f"- {ingredient.title()} ({count} recipes)")
            
            if st.button("📝 Create Shopping List", use_container_width=True):
                shopping_list = [ing for ing, _ in common_missing]
                st.success("✅ Shopping list created!")
                for item in shopping_list:
                    st.write(f"- {item.title()}")
        else:
            st.info("🎉 You're fully stocked!")
    else:
        st.info("💡 Generate recipes first!")

    st.markdown("---")
    st.caption("💡 Use leftovers to save money & reduce waste!")