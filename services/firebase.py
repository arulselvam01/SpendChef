# services/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os
import streamlit as st

class FirebaseService:
    """Firebase service for authentication and database operations"""
    
    def __init__(self):
        """Initialize Firebase connection"""
        self.db = None
        self.initialized = False
        
        if not firebase_admin._apps:
            try:
                # Try to get from Streamlit secrets
                if hasattr(st, 'secrets') and 'FIREBASE' in st.secrets:
                    cred_dict = {
                        "type": "service_account",
                        "project_id": st.secrets["FIREBASE"]["project_id"],
                        "private_key_id": st.secrets["FIREBASE"]["private_key_id"],
                        "private_key": st.secrets["FIREBASE"]["private_key"].replace('\\n', '\n'),
                        "client_email": st.secrets["FIREBASE"]["client_email"],
                        "client_id": st.secrets["FIREBASE"]["client_id"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['FIREBASE']['client_email']}"
                    }
                    cred = credentials.Certificate(cred_dict)
                else:
                    # Use environment variables
                    project_id = os.getenv("FIREBASE_PROJECT_ID")
                    if not project_id:
                        st.error("Firebase credentials not found. Please configure FIREBASE_PROJECT_ID in environment variables.")
                        return
                    
                    cred_dict = {
                        "type": "service_account",
                        "project_id": project_id,
                        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL')}"
                    }
                    cred = credentials.Certificate(cred_dict)
                
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.initialized = True
                print("✅ Firebase initialized successfully")
            except Exception as e:
                st.error(f"❌ Firebase initialization error: {e}")
                print(f"Firebase error: {e}")
                self.initialized = False
        else:
            try:
                self.db = firestore.client()
                self.initialized = True
            except Exception as e:
                print(f"Error getting Firestore client: {e}")
                self.initialized = False
    
    def _check_firestore(self):
        """Check if Firestore is available"""
        if not self.initialized or not self.db:
            st.error("Firestore not available. Please check your Firebase configuration.")
            return False
        return True
    
    # User Management
    def create_user(self, email: str, name: str, password: str = None) -> Dict:
        """Create a new user"""
        if not self._check_firestore():
            return None
        
        user_id = email.replace('@', '_').replace('.', '_')
        
        user_data = {
            'email': email,
            'name': name,
            'created_at': firestore.SERVER_TIMESTAMP,
            'settings': {
                'theme': 'light',
                'notifications': True,
                'currency': 'INR',
                'monthly_budget': 500
            },
            'budget': {
                'monthly': 500,
                'spent': 0,
                'remaining': 500
            }
        }
        
        try:
            self.db.collection('users').document(user_id).set(user_data)
            print(f"✅ User created: {user_id}")
            return user_data
        except Exception as e:
            st.error(f"Error creating user: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        if not self._check_firestore():
            return None
        
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            st.error(f"Error getting user: {e}")
            return None
    
    def update_user_settings(self, user_id: str, settings: Dict):
        """Update user settings"""
        if not self._check_firestore():
            return
        
        try:
            self.db.collection('users').document(user_id).update({'settings': settings})
        except Exception as e:
            st.error(f"Error updating settings: {e}")
    
    def update_budget(self, user_id: str, monthly_budget: float):
        """Update user's monthly budget"""
        if not self._check_firestore():
            return
        
        try:
            self.db.collection('users').document(user_id).update({
                'budget.monthly': monthly_budget
            })
        except Exception as e:
            st.error(f"Error updating budget: {e}")
    
    # Transaction Management
    def add_transaction(self, user_id: str, transaction: Dict) -> str:
        """Add a transaction"""
        if not self._check_firestore():
            return None
        
        transaction.update({
            'user_id': user_id,
            'created_at': firestore.SERVER_TIMESTAMP,
            'date': transaction.get('date', datetime.now())
        })
        
        try:
            doc_ref = self.db.collection('transactions').document()
            doc_ref.set(transaction)
            
            # Update user's spent amount
            user = self.get_user(user_id)
            if user:
                current_spent = user.get('budget', {}).get('spent', 0)
                new_spent = current_spent + transaction.get('amount', 0)
                monthly_budget = user.get('budget', {}).get('monthly', 500)
                self.db.collection('users').document(user_id).update({
                    'budget.spent': new_spent,
                    'budget.remaining': monthly_budget - new_spent
                })
            
            return doc_ref.id
        except Exception as e:
            st.error(f"Error adding transaction: {e}")
            return None
    
    def get_transactions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user transactions"""
        if not self._check_firestore():
            return []
        
        try:
            transactions = []
            docs = self.db.collection('transactions')\
                .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            for doc in docs:
                trans = doc.to_dict()
                trans['id'] = doc.id
                transactions.append(trans)
            
            return transactions
        except Exception as e:
            st.error(f"Error getting transactions: {e}")
            return []
    
    # Receipt Management
    def save_receipt(self, user_id: str, receipt_data: Dict) -> str:
        """Save scanned receipt"""
        if not self._check_firestore():
            return None
        
        receipt_data.update({
            'user_id': user_id,
            'created_at': firestore.SERVER_TIMESTAMP,
            'scanned_at': datetime.now()
        })
        
        try:
            doc_ref = self.db.collection('receipts').document()
            doc_ref.set(receipt_data)
            return doc_ref.id
        except Exception as e:
            st.error(f"Error saving receipt: {e}")
            return None
    
    def get_user_receipts(self, user_id: str) -> List[Dict]:
        """Get all receipts for a user"""
        if not self._check_firestore():
            return []
        
        try:
            receipts = []
            docs = self.db.collection('receipts')\
                .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .stream()
            
            for doc in docs:
                receipt = doc.to_dict()
                receipt['id'] = doc.id
                receipts.append(receipt)
            
            return receipts
        except Exception as e:
            st.error(f"Error getting receipts: {e}")
            return []
    
    def delete_receipt(self, receipt_id: str):
        """Delete a receipt"""
        if not self._check_firestore():
            return
        
        try:
            self.db.collection('receipts').document(receipt_id).delete()
        except Exception as e:
            st.error(f"Error deleting receipt: {e}")
    
    # Pantry Management
    def update_pantry(self, user_id: str, ingredients: List[Dict]):
        """Update user's pantry"""
        if not self._check_firestore():
            return
        
        pantry_data = {
            'user_id': user_id,
            'ingredients': ingredients,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        try:
            self.db.collection('pantry').document(user_id).set(pantry_data)
        except Exception as e:
            st.error(f"Error updating pantry: {e}")
    
    def get_pantry(self, user_id: str) -> List[Dict]:
        """Get user's pantry"""
        if not self._check_firestore():
            return []
        
        try:
            doc = self.db.collection('pantry').document(user_id).get()
            if doc.exists:
                return doc.to_dict().get('ingredients', [])
            return []
        except Exception as e:
            st.error(f"Error getting pantry: {e}")
            return []
    
    # Recipe Management
    def save_recipe(self, user_id: str, recipe_data: Dict):
        """Save a recipe to user's collection"""
        if not self._check_firestore():
            return None
        
        recipe_data.update({
            'user_id': user_id,
            'saved_at': firestore.SERVER_TIMESTAMP
        })
        
        try:
            doc_ref = self.db.collection('saved_recipes').document()
            doc_ref.set(recipe_data)
            return doc_ref.id
        except Exception as e:
            st.error(f"Error saving recipe: {e}")
            return None
    
    def get_saved_recipes(self, user_id: str) -> List[Dict]:
        """Get user's saved recipes"""
        if not self._check_firestore():
            return []
        
        try:
            recipes = []
            docs = self.db.collection('saved_recipes')\
                .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
                .order_by('saved_at', direction=firestore.Query.DESCENDING)\
                .stream()
            
            for doc in docs:
                recipe = doc.to_dict()
                recipe['id'] = doc.id
                recipes.append(recipe)
            
            return recipes
        except Exception as e:
            st.error(f"Error getting saved recipes: {e}")
            return []
    
    # Export Data
    def export_user_data(self, user_id: str) -> Dict:
        """Export all user data"""
        return {
            'user': self.get_user(user_id),
            'transactions': self.get_transactions(user_id, limit=1000),
            'receipts': self.get_user_receipts(user_id),
            'pantry': self.get_pantry(user_id),
            'saved_recipes': self.get_saved_recipes(user_id),
            'export_date': datetime.now().isoformat()
        }


# In services/firebase.py, make sure the save_recipe method is properly implemented:

def save_recipe(self, user_id: str, recipe_data: Dict):
    """Save a recipe to user's collection"""
    if not self._check_firestore():
        return None
    
    recipe_data.update({
        'user_id': user_id,
        'saved_at': firestore.SERVER_TIMESTAMP
    })
    
    try:
        doc_ref = self.db.collection('saved_recipes').document()
        doc_ref.set(recipe_data)
        return doc_ref.id
    except Exception as e:
        st.error(f"Error saving recipe: {e}")
        return None

def get_saved_recipes(self, user_id: str) -> List[Dict]:
    """Get user's saved recipes"""
    if not self._check_firestore():
        return []
    
    try:
        recipes = []
        docs = self.db.collection('saved_recipes')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .order_by('saved_at', direction=firestore.Query.DESCENDING)\
            .stream()
        
        for doc in docs:
            recipe = doc.to_dict()
            recipe['id'] = doc.id
            recipes.append(recipe)
        
        return recipes
    except Exception as e:
        st.error(f"Error getting saved recipes: {e}")
        return []