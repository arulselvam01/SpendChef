# services/ocr.py
import re
import numpy as np
from typing import List, Dict, Any, Tuple
import pytesseract
from PIL import Image
import cv2
import io

class OCRService:
    """AI-powered receipt scanning service for Indian grocery receipts"""
    
    def __init__(self):
        # Common Indian grocery items
        self.common_items = {
            'milk': ['milk', 'dairy milk', '2% milk', 'toned milk', 'full cream milk', 'amul milk', 'nandini milk'],
            'bread': ['bread', 'loaf', 'baguette', 'brown bread', 'white bread', 'britannia bread'],
            'eggs': ['eggs', 'egg', 'dozen eggs', 'brown eggs', 'egg tray'],
            'cheese': ['cheese', 'cheddar', 'mozzarella', 'paneer', 'amul cheese', 'go cheese'],
            'chicken': ['chicken', 'breast', 'thigh', 'drumstick', 'leg piece', 'broiler'],
            'beef': ['beef', 'steak', 'ground beef', 'buff'],
            'pork': ['pork', 'bacon', 'ham'],
            'fish': ['salmon', 'tuna', 'fish', 'pomfret', 'bangda', 'surmai', 'rohu', 'mackerel'],
            'rice': ['rice', 'basmati', 'jasmine', 'ponni', 'sona masoori', 'kerala rice', 'ponni rice'],
            'pasta': ['pasta', 'spaghetti', 'noodles', 'macaroni', 'penne', 'fusilli'],
            'tomatoes': ['tomato', 'tomatoes', 'tamatar', 'cherry tomato'],
            'onions': ['onion', 'onions', 'pyaz', 'red onion', 'shallots'],
            'potatoes': ['potato', 'potatoes', 'aloo', 'baby potato'],
            'carrots': ['carrot', 'carrots', 'gajar'],
            'apples': ['apple', 'apples', 'seb', 'washington apple', 'kashmir apple'],
            'bananas': ['banana', 'bananas', 'kela', 'robusta', 'yellaki'],
            'oranges': ['orange', 'oranges', 'santra', 'kinnow', 'mosambi'],
            'curd': ['curd', 'yogurt', 'dahi', 'greek yogurt', 'curd pack'],
            'butter': ['butter', 'makhan', 'amul butter', 'butter block'],
            'oil': ['oil', 'cooking oil', 'sunflower oil', 'olive oil', 'refined oil', 'groundnut oil', 'coconut oil'],
            'atta': ['atta', 'wheat flour', 'whole wheat flour', 'aata', 'ashirvaad atta', 'pillsbury atta'],
            'sugar': ['sugar', 'cheeni', 'white sugar', 'brown sugar', 'powdered sugar'],
            'salt': ['salt', 'namak', 'table salt', 'rock salt', 'sendha namak', 'tata salt'],
            'tea': ['tea', 'chai', 'tea leaves', 'red label', 'taj mahal tea', 'wagh bakri', 'brooke bond'],
            'coffee': ['coffee', 'coffee powder', 'nescafe', 'bru', 'filter coffee', 'continental coffee'],
            'biscuits': ['biscuits', 'cookie', 'parle', 'good day', 'hide and seek', 'oreo', 'marie gold'],
            'chips': ['chips', 'lays', 'kurkure', 'namkeen', 'mixture', 'bingo', 'doritos'],
            'soap': ['soap', 'bath soap', 'dove', 'lux', 'lifebuoy', 'cinthol', 'pears', 'santoor'],
            'shampoo': ['shampoo', 'hair wash', 'dove shampoo', 'clinic plus', 'head & shoulders', 'sunsilk'],
            'detergent': ['detergent', 'surf excel', 'ariel', 'washing powder', 'tide', 'rin']
        }
        
        # Indian stores
        self.indian_stores = [
            'dmart', 'reliance fresh', 'reliance smart', 'big bazaar', 'more', 
            'star bazaar', 'spar', 'foodhall', 'nature\'s basket', 'hypercity',
            'ratnadeep', 'nilgiris', 'amul', 'local store', 'supermarket', 'metro',
            'vishal mega mart', 'easyday', 'spencer\'s', 'heritage fresh', 'fresh'
        ]
    
    def scan_receipt(self, image: Image.Image) -> Dict[str, Any]:
        """Scan receipt image and extract items with improved preprocessing"""
        try:
            # Enhanced image preprocessing
            img_array = np.array(image)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply adaptive thresholding for better text extraction
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 15, 2)
            
            # Denoise
            denoised = cv2.medianBlur(thresh, 3)
            
            # Dilate to connect text components
            kernel = np.ones((2, 2), np.uint8)
            dilated = cv2.dilate(denoised, kernel, iterations=1)
            
            # Try multiple PSM modes for better text extraction
            psm_modes = [6, 4, 3, 8, 13]  # Different page segmentation modes
            combined_text = ""
            
            for psm in psm_modes:
                config = f'--psm {psm} --oem 3'
                text = pytesseract.image_to_string(dilated, config=config)
                combined_text += text + "\n"
            
            # Also try with the original gray image
            text_orig = pytesseract.image_to_string(gray, config='--psm 6')
            combined_text += text_orig + "\n"
            
            # Parse items
            items = self._parse_receipt_text(combined_text)
            
            # Calculate total
            total = sum(item.get('price', 0) for item in items)
            
            return {
                'success': True,
                'raw_text': combined_text[:500],  # Limit for display
                'items': items,
                'total_items': len(items),
                'total_amount': total,
                'store': self._extract_store_name(combined_text)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'items': []
            }
    
    def _parse_receipt_text(self, text: str) -> List[Dict]:
        """Parse receipt text to extract items with improved pattern matching"""
        lines = text.split('\n')
        items = []
        
        # Enhanced patterns for Indian prices
        price_patterns = [
            r'₹\s*(\d+\.\d{2})',  # ₹100.00
            r'Rs\.?\s*(\d+\.\d{2})',  # Rs.100.00 or Rs 100.00
            r'(\d+\.\d{2})\s*₹',  # 100.00₹
            r'(\d+\.\d{2})$',  # price at end of line
            r'\s(\d+\.\d{2})\s',  # price between spaces
            r'(\d+)\s*\.\s*(\d{2})',  # 100 . 00 format
            r'(\d+\.\d{2})',  # any decimal number
        ]
        
        # Patterns for whole numbers
        whole_price_patterns = [
            r'₹\s*(\d+)\s*$',
            r'Rs\.?\s*(\d+)\s*$',
            r'(\d+)\s*$'
        ]
        
        # Common noise words to skip
        noise_keywords = [
            'total', 'subtotal', 'tax', 'gst', 'discount', 'bill', 
            'thank', 'visit', 'customer', 'card', 'cash', 'change',
            'sub total', 'grand total', 'amount', 'paid', 'balance',
            'gstin', 'invoice', 'date', 'time', 'counter', 'bill no'
        ]
        
        # Words that indicate an item line (not prices)
        item_indicators = ['@', 'kg', 'gm', 'ltr', 'ml', 'pack', 'pkt', 'piece', 'each', 'qty', 'nos', 'x']
        
        for line in lines:
            line = line.strip().lower()
            if not line or len(line) < 4:
                continue
            
            # Skip lines with noise keywords
            if any(keyword in line for keyword in noise_keywords):
                continue
            
            price = None
            
            # Try to extract price
            for pattern in price_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    try:
                        if isinstance(matches[-1], tuple):
                            price_str = '.'.join(matches[-1])
                        else:
                            price_str = matches[-1]
                        price = float(price_str)
                        break
                    except:
                        continue
            
            # If no decimal price found, try whole number patterns
            if price is None:
                for pattern in whole_price_patterns:
                    matches = re.findall(pattern, line)
                    if matches:
                        try:
                            price = float(matches[-1])
                            break
                        except:
                            continue
            
            if price and price > 0 and price < 50000:  # Reasonable price range
                # Extract item name by removing price and other noise
                item_name = line
                
                # Remove price patterns
                for pattern in price_patterns + whole_price_patterns:
                    item_name = re.sub(pattern, '', item_name)
                
                # Clean up item name
                item_name = re.sub(r'[^\w\s]', '', item_name)
                item_name = re.sub(r'\s+', ' ', item_name).strip()
                
                # Remove common noise words
                for noise in noise_keywords:
                    item_name = re.sub(rf'\b{noise}\b', '', item_name, flags=re.IGNORECASE)
                
                # Remove measurement units
                units = ['kg', 'gm', 'g', 'ml', 'l', 'lt', 'pack', 'pkt', 'piece', 'pcs', 'each', 'qty', 'nos']
                for unit in units:
                    item_name = re.sub(rf'\b\d+\.?\d*\s*{unit}\b', '', item_name, flags=re.IGNORECASE)
                    item_name = re.sub(rf'\b{unit}\b', '', item_name, flags=re.IGNORECASE)
                
                # Remove numbers that might be quantities
                item_name = re.sub(r'^\d+\s*', '', item_name)
                item_name = re.sub(r'\s\d+$', '', item_name)
                
                item_name = item_name.strip()
                
                # Skip if item name is too short or just numbers
                if item_name and len(item_name) > 1 and not item_name.isdigit():
                    # Check if this looks like an item (has at least one letter)
                    if any(c.isalpha() for c in item_name):
                        category = self._categorize_item(item_name)
                        
                        # Extract quantity
                        quantity = 1
                        qty_match = re.search(r'(\d+)\s*x\s*\d+', line) or re.search(r'(\d+)\s*pc', line)
                        if qty_match:
                            quantity = int(qty_match.group(1))
                        
                        items.append({
                            'name': item_name.title(),
                            'price': price,
                            'category': category,
                            'quantity': quantity
                        })
        
        # Remove duplicates based on name and similar price
        unique_items = []
        for item in items:
            # Check if similar item exists
            exists = False
            for existing in unique_items:
                if existing['name'].lower() == item['name'].lower() and abs(existing['price'] - item['price']) < 1:
                    existing['quantity'] += item['quantity']
                    exists = True
                    break
            if not exists:
                unique_items.append(item)
        
        return unique_items
    
    def _categorize_item(self, item_name: str) -> str:
        """Categorize item based on name with improved Indian context"""
        item_name = item_name.lower()
        
        # First check common items
        for category, keywords in self.common_items.items():
            if any(keyword in item_name for keyword in keywords):
                return category
        
        # Check for Indian categories with more keywords
        categories_mapping = {
            'produce': ['sabji', 'bhaji', 'vegetable', 'veg', 'tarkari', 'phool', 'gobi', 'bhindi', 'tori', 'karela', 
                       'fruit', 'apple', 'banana', 'orange', 'grape', 'mango', 'cucumber', 'pumpkin', 'brinjal'],
            'protein': ['paneer', 'tofu', 'soy', 'chicken', 'mutton', 'fish', 'prawn', 'egg', 'meat', 'lentil', 'dal'],
            'dairy': ['milk', 'curd', 'yogurt', 'dahi', 'ghee', 'butter', 'cheese', 'cream', 'paneer'],
            'grains': ['atta', 'flour', 'rice', 'wheat', 'pasta', 'noodles', 'bread', 'roti', 'bajra', 'jowar'],
            'spices': ['masala', 'spice', 'jeera', 'haldi', 'dhania', 'mirch', 'cumin', 'coriander', 'turmeric', 
                      'chilli', 'pepper', 'salt', 'garam masala', 'sambar powder'],
            'beverages': ['soda', 'coke', 'pepsi', 'water', 'juice', 'frooti', 'slice', 'tea', 'coffee', 'chai'],
            'snacks': ['snack', 'chip', 'cookie', 'namkeen', 'biscuit', 'mixture', 'kachori', 'samosa', 'cake'],
            'household': ['soap', 'shampoo', 'cleaner', 'detergent', 'dove', 'lux', 'surf', 'ariel', 'tide', 'dettol']
        }
        
        for category, keywords in categories_mapping.items():
            if any(keyword in item_name for keyword in keywords):
                return category
        
        # Check for any product with these suffixes
        if any(suffix in item_name for suffix in ['food', 'product', 'brand', 'special', 'premium']):
            return 'other'
        
        return 'other'
    
    def _extract_store_name(self, text: str) -> str:
        """Extract store name from receipt with better Indian store support"""
        lines = text.split('\n')
        
        # Check first 15 lines for store name
        for line in lines[:15]:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Check Indian stores first
            for store in self.indian_stores:
                if store in line_lower:
                    return line_clean.title()
            
            # Check for common patterns
            patterns = [
                r'([A-Za-z\s]+)\s+(supermarket|super market|grocery|store|mart|hyper|fresh)',
                r'(welcome to|thank you for shopping at)\s+([A-Za-z\s]+)',
                r'([A-Za-z\s]+)\s+bill',
                r'([A-Za-z\s]+)\s+receipt'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line_lower, re.IGNORECASE)
                if match:
                    store_name = match.group(1) if len(match.groups()) > 1 else match.group(0)
                    return store_name.strip().title()
            
            # Look for capitalized words (potential store name)
            words = line_clean.split()
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 3 and word.lower() not in ['total', 'subtotal', 'amount', 'date', 'time']:
                    # Check if it's likely a store name
                    if i < 3:  # Usually store name appears early
                        return ' '.join(words[:min(3, len(words))]).title()
        
        return "Local Store"