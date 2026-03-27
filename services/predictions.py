# services/predictions.py - Updated for better accuracy

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class SpendingPredictor:

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, transactions):
        """Prepare features for ML training"""
        if not transactions:
            return None, None

        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        # Group by day
        daily = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
        daily['date'] = pd.to_datetime(daily['date'])

        if len(daily) < 2:
            return None, None

        X, y = [], []
        window_size = min(2, len(daily) - 1)
        
        for i in range(window_size, len(daily)):
            last_window = daily['amount'].iloc[i-window_size:i].values
            d = daily['date'].iloc[i]

            features = [
                last_window.mean(),
                last_window.std() if len(last_window) > 1 else 0,
                last_window.max(),
                last_window.min(),
                last_window[-1],
                d.weekday(),
                int(d.weekday() >= 5),
                int(d.day <= 7),
                int(d.day >= 25),
                d.month
            ]
            X.append(features)
            y.append(daily['amount'].iloc[i])

        return np.array(X), np.array(y)

    def train_model(self, transactions):
        """Train ML model"""
        X, y = self.prepare_features(transactions)

        if X is None or len(X) < 1:
            self.is_trained = False
            return None

        self.model = RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42)
        
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            return self.model.score(X_scaled, y)
        except Exception as e:
            print(f"Training error: {e}")
            self.is_trained = False
            return None

    def predict_next_month(self, transactions, days=30):
        """Predict next month's spending"""
        if not transactions:
            return self._simple_prediction(transactions, days)

        try:
            if self.is_trained:
                ml_pred = self._ml_prediction(transactions, days)
                simple_pred = self._simple_prediction(transactions, days)
                
                # Blend predictions: 70% ML, 30% simple for better accuracy
                blended_total = (ml_pred['predicted_total'] * 0.7) + (simple_pred['predicted_total'] * 0.3)
                
                return {
                    "predicted_total": blended_total,
                    "confidence": ml_pred['confidence'],
                    "method": "ml+simple"
                }
        except Exception as e:
            print(f"ML prediction failed: {e}")

        return self._simple_prediction(transactions, days)

    def _ml_prediction(self, transactions, days):
        """ML-based prediction"""
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        daily = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
        daily['date'] = pd.to_datetime(daily['date'])

        lookback = min(len(daily), 7)
        last_values = daily['amount'].values[-lookback:]

        preds = []
        
        for i in range(days):
            d = datetime.now() + timedelta(days=i+1)

            features = np.array([[
                last_values.mean(),
                last_values.std() if len(last_values) > 1 else 0,
                last_values.max(),
                last_values.min(),
                last_values[-1],
                d.weekday(),
                int(d.weekday() >= 5),
                int(d.day <= 7),
                int(d.day >= 25),
                d.month
            ]])

            try:
                features_scaled = self.scaler.transform(features)
                pred = self.model.predict(features_scaled)[0]
                pred = max(0, pred)
            except:
                pred = last_values.mean() if len(last_values) > 0 else 0

            preds.append(pred)
            last_values = np.append(last_values[1:], pred) if len(last_values) > 1 else np.array([pred])

        total_predicted = sum(preds)
        
        return {
            "predicted_total": total_predicted,
            "confidence": min(75, 30 + len(transactions)),
            "method": "ml"
        }

    def _simple_prediction(self, transactions, days=30):
        """Simple average prediction"""
        if not transactions:
            return {"predicted_total": 0, "confidence": 0, "method": "simple"}

        total = sum(t.get("amount", 0) for t in transactions)

        dates = set()
        for t in transactions:
            try:
                d = pd.to_datetime(t["date"])
                dates.add(d.date())
            except:
                pass

        days_count = max(len(dates), 1)
        avg = total / days_count
        predicted_total = avg * days

        return {
            "predicted_total": predicted_total,
            "confidence": 50,
            "method": "simple"
        }

    def get_trend_analysis(self, transactions):
        """Analyze spending trends"""
        if len(transactions) < 2:
            return {"trend": "stable", "insight": "Add more transactions for trend analysis"}

        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        daily = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()

        if len(daily) < 2:
            return {"trend": "stable", "insight": "Need at least 2 days of data"}

        # Calculate daily averages
        total_spent = sum(t.get('amount', 0) for t in transactions)
        days_count = len(daily)
        avg_daily = total_spent / days_count
        
        # Get recent trend
        if len(daily) >= 3:
            recent_avg = daily['amount'].iloc[-2:].mean()
            earlier_avg = daily['amount'].iloc[:2].mean()
            
            if recent_avg > earlier_avg * 1.1:
                trend = "increasing"
                insight = f"Spending up from ₹{earlier_avg:.0f} to ₹{recent_avg:.0f} per day"
            elif recent_avg < earlier_avg * 0.9:
                trend = "decreasing"
                insight = f"Spending down from ₹{earlier_avg:.0f} to ₹{recent_avg:.0f} per day"
            else:
                trend = "stable"
                insight = f"Steady spending at ₹{avg_daily:.0f} per day"
        else:
            if len(daily) == 2:
                day1 = daily['amount'].iloc[0]
                day2 = daily['amount'].iloc[1]
                if day2 > day1 * 1.2:
                    trend = "increasing"
                    insight = f"Spending increased from ₹{day1:.0f} to ₹{day2:.0f}"
                elif day2 < day1 * 0.8:
                    trend = "decreasing"
                    insight = f"Spending decreased from ₹{day1:.0f} to ₹{day2:.0f}"
                else:
                    trend = "stable"
                    insight = f"Consistent spending at ₹{avg_daily:.0f} per day"
            else:
                trend = "stable"
                insight = f"Spending ₹{avg_daily:.0f} per day"

        return {
            "trend": trend,
            "insight": insight,
            "avg_daily": avg_daily
        }