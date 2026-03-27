# services/recipe_ai.py
import json
import re
from typing import List, Dict, Optional
import streamlit as st
import os
from groq import Groq

class RecipeAIService:

    def __init__(self):
        self.api_key = None

        # Try to get from streamlit secrets (note: your secret is GROK_API_KEY)
        try:
            if hasattr(st, 'secrets'):
                if 'GROQ_API_KEY' in st.secrets:
                    self.api_key = st.secrets['GROQ_API_KEY']
                    print("✅ Found GROQ_API_KEY in st.secrets")
                elif 'GROK_API_KEY' in st.secrets:
                    self.api_key = st.secrets['GROK_API_KEY']
                    print("✅ Found GROK_API_KEY in st.secrets")
        except Exception as e:
            print("Secrets error:", e)

        # Try environment variable
        if not self.api_key:
            self.api_key = os.getenv('GROQ_API_KEY', '') or os.getenv('GROK_API_KEY', '')
            if self.api_key:
                print("✅ Found API key in environment")

        if not self.api_key:
            print("❌ NO API KEY - Using fallback recipes")
            st.warning("⚠️ Groq API key not configured. Using fallback recipes. Please add your API key to .streamlit/secrets.toml")

    def generate_recipes(self, ingredients: List[str], preferences: Dict = None) -> List[Dict]:
        if not self.api_key:
            return self.fallback()

        try:
            print("🚀 USING GROQ API...")
            
            client = Groq(api_key=self.api_key)

            # Build prompt with preferences
            prompt = f"""
Generate EXACTLY 3 creative recipes using these ingredients: {', '.join(ingredients)}.
"""

            if preferences:
                if preferences.get('cuisine') and preferences['cuisine'] != "Any":
                    prompt += f"Prefer {preferences['cuisine']} cuisine. "
                if preferences.get('dietary') and preferences['dietary'] != "None":
                    prompt += f"Follow {preferences['dietary']} diet. "
                if preferences.get('max_time') and preferences['max_time'] != "Any":
                    prompt += f"Max prep time: {preferences['max_time']} minutes. "

            prompt += """
Return ONLY JSON array. No other text.

Format:
[
  {
    "name": "Recipe Name",
    "ingredients": ["ingredient1", "ingredient2"],
    "instructions": ["step1", "step2", "step3"],
    "prep_time": 20,
    "difficulty": "Easy/Medium/Hard",
    "cuisine": "Cuisine Type",
    "description": "Short description"
  }
]
"""

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a professional chef. Return only JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = completion.choices[0].message.content
            print("RAW RESPONSE:", content[:200])

            # Clean response
            content = content.strip()
            content = content.replace("```json", "").replace("```", "")

            try:
                recipes = json.loads(content)
            except:
                # Try to extract JSON array
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    recipes = json.loads(match.group(0))
                else:
                    raise Exception("JSON parsing failed")

            # Add match percentage based on ingredients
            ingredient_set = set([i.lower() for i in ingredients])
            for recipe in recipes:
                recipe_ingredients = set([i.lower() for i in recipe.get('ingredients', [])])
                matches = len(ingredient_set.intersection(recipe_ingredients))
                total = len(recipe_ingredients)
                if total > 0:
                    match_percentage = (matches / total) * 100
                else:
                    match_percentage = 0
                recipe['match_percentage'] = min(match_percentage, 100)
                recipe['available_ingredients'] = list(ingredient_set.intersection(recipe_ingredients))
                recipe['missing_ingredients'] = list(recipe_ingredients - ingredient_set)

            return recipes[:3]

        except Exception as e:
            print("❌ AI ERROR:", str(e))
            st.error(f"AI Error: {str(e)}")
            return self.fallback()

    def fallback(self):
        print("⚠️ USING FALLBACK RECIPES")
        return [
            {
                "name": "Simple Vegetable Stir Fry",
                "ingredients": ["vegetables", "oil", "salt", "pepper"],
                "instructions": [
                    "Heat oil in a pan",
                    "Add vegetables and stir-fry for 5-7 minutes",
                    "Add salt and pepper to taste",
                    "Serve hot"
                ],
                "prep_time": 15,
                "difficulty": "Easy",
                "cuisine": "Asian",
                "description": "A quick and healthy stir-fry with your favorite vegetables.",
                "match_percentage": 50,
                "available_ingredients": [],
                "missing_ingredients": []
            },
            {
                "name": "Classic Omelette",
                "ingredients": ["eggs", "butter", "salt", "pepper"],
                "instructions": [
                    "Whisk eggs with salt and pepper",
                    "Heat butter in a non-stick pan",
                    "Pour eggs and cook until set",
                    "Fold and serve"
                ],
                "prep_time": 10,
                "difficulty": "Easy",
                "cuisine": "French",
                "description": "A classic omelette that's perfect for breakfast.",
                "match_percentage": 50,
                "available_ingredients": [],
                "missing_ingredients": []
            },
            {
                "name": "Quick Pasta",
                "ingredients": ["pasta", "olive oil", "garlic", "salt"],
                "instructions": [
                    "Cook pasta according to package instructions",
                    "Sauté garlic in olive oil",
                    "Toss pasta with garlic oil",
                    "Season with salt and serve"
                ],
                "prep_time": 20,
                "difficulty": "Easy",
                "cuisine": "Italian",
                "description": "Simple garlic pasta that's quick to make.",
                "match_percentage": 50,
                "available_ingredients": [],
                "missing_ingredients": []
            }
        ]

    def get_recipe_details(self, recipe_name: str) -> Optional[Dict]:
        return None

    def suggest_substitutions(self, ingredient: str):
        substitutions = {
            'butter': ['margarine', 'coconut oil', 'olive oil'],
            'eggs': ['flaxseed meal', 'mashed banana', 'applesauce'],
            'milk': ['almond milk', 'soy milk', 'oat milk'],
            'cheese': ['nutritional yeast', 'vegan cheese'],
            'sugar': ['honey', 'maple syrup', 'stevia'],
            'flour': ['almond flour', 'coconut flour', 'oat flour'],
        }
        
        ingredient_lower = ingredient.lower()
        for key, subs in substitutions.items():
            if key in ingredient_lower or ingredient_lower in key:
                return subs
        return []