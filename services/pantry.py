# services/pantry.py
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

class PantryService:
    """Pantry management service"""
    
    def __init__(self):
        self.categories = {
            'produce': ['vegetables', 'fruits', 'herbs', 'sabji', 'bhaji', 'phool', 'gobi', 'bhindi', 'tori', 'karela', 'tomato', 'onion', 'potato', 'carrot', 'apple', 'banana', 'orange'],
            'protein': ['meat', 'poultry', 'fish', 'tofu', 'beans', 'eggs', 'chicken', 'beef', 'pork', 'paneer', 'lentils', 'dal', 'tofu', 'soy'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'curd', 'dahi', 'ghee', 'cream', 'paneer'],
            'grains': ['rice', 'pasta', 'bread', 'oats', 'flour', 'atta', 'wheat', 'cereal', 'quinoa', 'noodles'],
            'canned': ['canned', 'tin', 'preserved', 'pickle'],
            'spices': ['salt', 'pepper', 'herbs', 'spices', 'masala', 'jeera', 'haldi', 'cumin', 'coriander', 'chilli', 'turmeric'],
            'beverages': ['water', 'juice', 'soda', 'coffee', 'tea', 'chai', 'drink', 'milk shake'],
            'snacks': ['chips', 'cookies', 'nuts', 'crackers', 'namkeen', 'biscuit', 'snack', 'chocolate', 'candy'],
            'frozen': ['frozen', 'ice cream', 'cold', 'freeze'],
            'other': []  # IMPORTANT: Added 'other' category
        }
    
    def add_ingredient(self, pantry: List[Dict], ingredient: Dict) -> List[Dict]:
        """Add ingredient to pantry"""
        existing = next((i for i in pantry if i['name'].lower() == ingredient['name'].lower()), None)
        
        if existing:
            existing['quantity'] = existing.get('quantity', 1) + ingredient.get('quantity', 1)
            existing['last_updated'] = datetime.now()
        else:
            ingredient['added_date'] = datetime.now()
            ingredient['last_updated'] = datetime.now()
            pantry.append(ingredient)
        
        return pantry
    
    def remove_ingredient(self, pantry: List[Dict], ingredient_name: str) -> List[Dict]:
        """Remove ingredient from pantry"""
        return [i for i in pantry if i['name'].lower() != ingredient_name.lower()]
    
    def update_quantity(self, pantry: List[Dict], ingredient_name: str, quantity: int) -> List[Dict]:
        """Update ingredient quantity"""
        for item in pantry:
            if item['name'].lower() == ingredient_name.lower():
                item['quantity'] = quantity
                item['last_updated'] = datetime.now()
                break
        return pantry
    
    def get_expiring_items(self, pantry: List[Dict], days: int = 7) -> List[Dict]:
        """Get items expiring soon"""
        expiring = []
        current_date = datetime.now()
        
        for item in pantry:
            if 'expiry_date' in item:
                expiry_date = item['expiry_date']
                if isinstance(expiry_date, str):
                    expiry_date = datetime.fromisoformat(expiry_date)
                
                days_left = (expiry_date - current_date).days
                if 0 <= days_left <= days:
                    expiring.append({
                        **item,
                        'days_left': days_left
                    })
        
        return sorted(expiring, key=lambda x: x['days_left'])
    
    def get_category_stats(self, pantry: List[Dict]) -> Dict:
        """Get statistics by category - FIXED with 'other' included"""
        # Initialize all categories with 0, including 'other'
        stats = {category: 0 for category in self.categories.keys()}
        
        # Ensure 'other' is in stats
        if 'other' not in stats:
            stats['other'] = 0
        
        for item in pantry:
            # Get category from item or use categorize_ingredient
            if 'category' in item and item['category']:
                item_category = item['category']
            else:
                item_category = self.categorize_ingredient(item['name'])
            
            # If category not in stats, default to 'other'
            if item_category not in stats:
                item_category = 'other'
            
            # Increment the count
            stats[item_category] = stats.get(item_category, 0) + 1
        
        return stats
    
    def categorize_ingredient(self, ingredient_name: str) -> str:
        """Categorize an ingredient"""
        name_lower = ingredient_name.lower()
        
        for category, keywords in self.categories.items():
            if category != 'other' and any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def suggest_shopping_list(self, pantry: List[Dict], recipes: List[Dict]) -> List[Dict]:
        """Suggest shopping list based on missing ingredients"""
        needed_ingredients = {}
        
        for recipe in recipes:
            for ingredient in recipe.get('missing_ingredients', []):
                needed_ingredients[ingredient] = needed_ingredients.get(ingredient, 0) + 1
        
        # Sort by frequency
        sorted_needed = sorted(needed_ingredients.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'name': name, 'recipes_using': count}
            for name, count in sorted_needed
        ]
    
    def get_low_stock_items(self, pantry: List[Dict], threshold: int = 2) -> List[Dict]:
        """Get items with low stock"""
        return [item for item in pantry if item.get('quantity', 0) <= threshold]
    
    def get_items_by_category(self, pantry: List[Dict], category: str) -> List[Dict]:
        """Get all items in a specific category"""
        return [item for item in pantry if self.categorize_ingredient(item['name']) == category]