# pages/2_home.py - Fixed with consistent ML predictions

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.dashboard import DashboardWidgets
from services.firebase import FirebaseService
from services.pantry import PantryService
from services.predictions import SpendingPredictor


def format_inr(amount):
    """Format amount in Indian Rupees"""
    return f"₹{amount:,.2f}"


def calculate_actual_stats(transactions):
    """Calculate actual spending statistics from transactions"""
    if not transactions:
        return {
            'total_spent': 0,
            'days_count': 0,
            'daily_avg': 0,
            'simple_monthly': 0
        }
    
    total_spent = sum(t.get('amount', 0) for t in transactions)
    
    # Count unique days
    unique_dates = set()
    for t in transactions:
        date = t.get('date')
        if date:
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace('Z', '+00:00')).replace(tzinfo=None)
                    unique_dates.add(date.date())
                except:
                    pass
            elif hasattr(date, 'date'):
                unique_dates.add(date.date())
    
    days_count = max(len(unique_dates), 1)
    daily_avg = total_spent / days_count
    simple_monthly = daily_avg * 30
    
    return {
        'total_spent': total_spent,
        'days_count': days_count,
        'daily_avg': daily_avg,
        'simple_monthly': simple_monthly
    }


def show():
    """Home/Dashboard page with consistent ML predictions"""

    # Header
    st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0;">
            <h1 style="font-size: 5rem; margin: 0; background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                SpendChef
            </h1>
            <p style="font-size: 1.25rem; color: #5a6c7e; margin: 0;">Your AI-Powered Kitchen Assistant</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### 👋 Welcome back, {st.session_state.user_name}!")

    firebase = FirebaseService()

    # Load fresh data
    if st.session_state.user_id:
        user = firebase.get_user(st.session_state.user_id)

        if user:
            budget_data = user.get('budget', {})
            monthly = budget_data.get('monthly', 500)
            spent = budget_data.get('spent', 0)
            remaining = monthly - spent

            st.session_state.budget = {
                'monthly': monthly,
                'spent': spent,
                'remaining': remaining
            }

            st.session_state.transactions = firebase.get_transactions(st.session_state.user_id)
            st.session_state.pantry = firebase.get_pantry(st.session_state.user_id)

    pantry_items = st.session_state.pantry
    
    # Get expiring items count
    expiring_count = 0
    now = datetime.now().replace(tzinfo=None)
    for item in pantry_items:
        if item.get('expiry_date'):
            try:
                expiry_date = item['expiry_date']
                if isinstance(expiry_date, str):
                    expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).replace(tzinfo=None)
                if (expiry_date - now).days <= 7:
                    expiring_count += 1
            except:
                pass

    # Quick Overview
    st.markdown("### 📊 Quick Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 Monthly Budget", format_inr(st.session_state.budget['monthly']))

    with col2:
        spent = st.session_state.budget['spent']
        st.metric("💸 Spent", format_inr(spent))

    with col3:
        remaining = st.session_state.budget['remaining']
        st.metric("💵 Remaining", format_inr(remaining))

    with col4:
        pantry_value = sum(item.get('price', 0) for item in pantry_items)
        st.metric("📦 Pantry Value", format_inr(pantry_value))

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Spending Overview")
        chart = DashboardWidgets.budget_gauge(
            st.session_state.budget['spent'],
            st.session_state.budget['monthly']
        )
        if chart:
            chart.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No spending data yet")

    with col2:
        st.markdown("#### Category Breakdown")
        if st.session_state.transactions:
            chart = DashboardWidgets.category_breakdown(st.session_state.transactions)
            if chart:
                chart.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No transactions yet")
            
    st.markdown("---")
    
    # ==============================
    # 🔮 SMART PREDICTIONS
    # ==============================
    st.markdown("### 🔮 Smart Predictions")
    
    # Get actual stats from transactions
    actual_stats = calculate_actual_stats(st.session_state.transactions)
    
    # Initialize ML predictor
    predictor = SpendingPredictor()
    
    # Set initial values
    predicted_monthly = actual_stats['simple_monthly']
    trend_analysis = {'trend': 'stable', 'insight': f'Spending {format_inr(actual_stats["daily_avg"])}/day'}
    ml_status = "Data Collection"
    
    # Try ML if enough data
    if len(st.session_state.transactions) >= 3 and actual_stats['days_count'] >= 2:
        try:
            # Train model
            score = predictor.train_model(st.session_state.transactions)
            
            # Get ML predictions
            ml_predictions = predictor.predict_next_month(st.session_state.transactions)
            trend_analysis = predictor.get_trend_analysis(st.session_state.transactions)
            
            if ml_predictions and ml_predictions.get('predicted_total', 0) > 0:
                # Use ML but don't let it override reality too much
                ml_value = ml_predictions['predicted_total']
                simple_value = actual_stats['simple_monthly']
                
                # Blend: 50% ML, 50% simple (so it doesn't override)
                predicted_monthly = (ml_value * 0.5) + (simple_value * 0.5)
                ml_status = f"ML Active (Score: {score:.0%})"
            else:
                predicted_monthly = actual_stats['simple_monthly']
                ml_status = "Simple Mode"
                
        except Exception as e:
            predicted_monthly = actual_stats['simple_monthly']
            ml_status = "Simple Mode"
    else:
        predicted_monthly = actual_stats['simple_monthly']
        ml_status = f"Need {3 - len(st.session_state.transactions)} more transactions"
    
    # Display actual stats
    if actual_stats['days_count'] > 0:
        st.info(f"📊 **Actual:** {format_inr(actual_stats['total_spent'])} over {actual_stats['days_count']} days | **Daily Avg:** {format_inr(actual_stats['daily_avg'])}")
    
    # Cap predictions to realistic values
    budget_monthly = st.session_state.budget['monthly']
    predicted_monthly = min(predicted_monthly, budget_monthly * 2)
    predicted_monthly = max(predicted_monthly, 0)
    
    expected_savings = budget_monthly - predicted_monthly

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea, #764ba2);
                    padding: 1rem; border-radius: 12px; color: white;">
            <h4 style="margin: 0;">📊 Next Month</h4>
            <h2 style="margin: 0; font-size: 1.8rem;">{format_inr(predicted_monthly)}</h2>
            <p style="margin: 0; font-size: 1rem;">Formula: {format_inr(actual_stats['daily_avg'])} × 30 = {format_inr(actual_stats['simple_monthly'])}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        savings_color = "#28a745" if expected_savings >= 0 else "#dc3545"
        st.markdown(f"""
        <div style="background: {savings_color};
                    padding: 1rem; border-radius: 12px; color: white;">
            <h4 style="margin: 0;">💰 Expected</h4>
            <h2 style="margin: 0; font-size: 1.8rem;">{format_inr(expected_savings)}</h2>
            <p style="margin: 0; font-size: 1rem;">{'Savings' if expected_savings >= 0 else 'Deficit'}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        trend_emoji = "📈" if trend_analysis.get('trend') == 'increasing' else "📉" if trend_analysis.get('trend') == 'decreasing' else "➡️"
        st.markdown(f"""
        <div style="background: #f39c12;
                    padding: 1rem; border-radius: 12px; color: white;">
            <h4 style="margin: 0;">📈 Trend</h4>
            <h2 style="margin: 0; font-size: 1rem;">{trend_emoji} {trend_analysis.get('trend', 'Stable').title()}</h2>
            <p style="margin: 0; font-size: 1rem;">ML Analysis</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background: #00b894;
                    padding: 1rem; border-radius: 12px; color: white;">
            <h4 style="margin: 0;">🧠 Insight</h4>
            <p style="margin: 0; font-size: 1rem;">{trend_analysis.get('insight', 'Add more transactions for insights')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show formula
    st.caption(f" Daily Avg {format_inr(actual_stats['daily_avg'])} × 30 days = {format_inr(actual_stats['simple_monthly'])} | ML adjusted to {format_inr(predicted_monthly)}")

    st.markdown("---")
    
    # Recent Transactions
    st.markdown("### 🔄 Recent Items Added")
    
    if st.session_state.transactions:
        recent = sorted(st.session_state.transactions, 
                       key=lambda x: x.get('date', datetime.min), 
                       reverse=True)[:5]
        
        for txn in recent:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                desc = txn.get('description', 'No description')[:30]
                st.write(f"**{desc}**")
            with col2:
                category = txn.get('category', 'other')
                category_icons = {
                    'groceries': '🛒', 'restaurants': '🍽️', 'utilities': '💡',
                    'transportation': '🚗', 'entertainment': '🎬', 'shopping': '🛍️',
                    'healthcare': '🏥', 'other': '📌'
                }
                icon = category_icons.get(category, '📌')
                st.write(f"{icon} {category.title()}")
            with col3:
                date = txn.get('date')
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '+00:00')).replace(tzinfo=None)
                    except:
                        date = datetime.now().replace(tzinfo=None)
                elif hasattr(date, 'tzinfo'):
                    date = date.replace(tzinfo=None)
                st.write(date.strftime('%d %b %Y') if hasattr(date, 'strftime') else str(date))
            with col4:
                st.write(format_inr(txn.get('amount', 0)))
    else:
        st.info("✨ No transactions yet. Scan your first receipt to get started!")
