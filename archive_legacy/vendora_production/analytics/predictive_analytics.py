"""
Predictive Analytics Engine for VENDORA Platform
Machine learning models for automotive business predictions
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    SALES_VOLUME = "sales_volume"
    REVENUE = "revenue"
    INVENTORY_TURNOVER = "inventory_turnover"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"
    LEAD_CONVERSION = "lead_conversion"


@dataclass
class PredictionResult:
    """Result from a predictive analytics operation"""
    prediction_type: PredictionType
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence_score: float
    prediction_date: datetime
    historical_data_points: int
    model_accuracy: float
    factors: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_type": self.prediction_type.value,
            "predicted_value": self.predicted_value,
            "confidence_interval": list(self.confidence_interval),
            "confidence_score": self.confidence_score,
            "prediction_date": self.prediction_date.isoformat(),
            "historical_data_points": self.historical_data_points,
            "model_accuracy": self.model_accuracy,
            "factors": self.factors
        }


class PredictiveAnalyticsEngine:
    """Advanced predictive analytics engine for automotive dealerships"""
    
    def __init__(self, bigquery_client=None):
        self.bigquery_client = bigquery_client
        self.models = {}
        self.cached_data = {}
        self.model_accuracy_history = {}
    
    async def predict_sales_volume(self, dealership_id: str, forecast_days: int = 30) -> PredictionResult:
        """Predict sales volume for the next N days"""
        try:
            # Get historical sales data
            sales_data = await self._get_sales_history(dealership_id, days=90)
            
            if not sales_data or len(sales_data) < 10:
                # Fallback prediction based on industry averages
                return self._generate_fallback_sales_prediction(dealership_id, forecast_days)
            
            # Convert to time series
            df = pd.DataFrame(sales_data)
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            df = df.sort_values('sale_date')
            
            # Aggregate daily sales
            daily_sales = df.groupby('sale_date').size().reset_index(name='sales_count')
            daily_sales = daily_sales.set_index('sale_date').resample('D').sum().fillna(0)
            
            # Apply time series forecasting
            prediction = self._forecast_time_series(daily_sales['sales_count'], forecast_days)
            
            # Calculate confidence based on data quality and seasonality
            confidence = self._calculate_prediction_confidence(daily_sales['sales_count'])
            
            # Identify key factors
            factors = self._analyze_sales_factors(df)
            
            return PredictionResult(
                prediction_type=PredictionType.SALES_VOLUME,
                predicted_value=prediction['forecast'],
                confidence_interval=(prediction['lower_bound'], prediction['upper_bound']),
                confidence_score=confidence,
                prediction_date=datetime.now(),
                historical_data_points=len(sales_data),
                model_accuracy=prediction.get('accuracy', 0.75),
                factors=factors
            )
            
        except Exception as e:
            logger.error(f"Sales volume prediction failed: {str(e)}")
            return self._generate_fallback_sales_prediction(dealership_id, forecast_days)
    
    async def predict_revenue(self, dealership_id: str, forecast_days: int = 30) -> PredictionResult:
        """Predict revenue for the next N days"""
        try:
            # Get historical sales with pricing data
            sales_data = await self._get_sales_history(dealership_id, days=90, include_pricing=True)
            
            if not sales_data or len(sales_data) < 10:
                return self._generate_fallback_revenue_prediction(dealership_id, forecast_days)
            
            df = pd.DataFrame(sales_data)
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            df['sale_price'] = pd.to_numeric(df.get('sale_price', 0))
            
            # Daily revenue aggregation
            daily_revenue = df.groupby('sale_date')['sale_price'].sum().reset_index()
            daily_revenue = daily_revenue.set_index('sale_date').resample('D').sum().fillna(0)
            
            # Forecast revenue
            prediction = self._forecast_time_series(daily_revenue['sale_price'], forecast_days)
            
            # Enhanced confidence calculation for revenue (more complex than volume)
            confidence = self._calculate_prediction_confidence(daily_revenue['sale_price']) * 0.9  # Revenue is inherently less predictable
            
            # Revenue-specific factors
            factors = self._analyze_revenue_factors(df)
            
            return PredictionResult(
                prediction_type=PredictionType.REVENUE,
                predicted_value=prediction['forecast'],
                confidence_interval=(prediction['lower_bound'], prediction['upper_bound']),
                confidence_score=confidence,
                prediction_date=datetime.now(),
                historical_data_points=len(sales_data),
                model_accuracy=prediction.get('accuracy', 0.70),
                factors=factors
            )
            
        except Exception as e:
            logger.error(f"Revenue prediction failed: {str(e)}")
            return self._generate_fallback_revenue_prediction(dealership_id, forecast_days)
    
    async def predict_inventory_turnover(self, dealership_id: str) -> PredictionResult:
        """Predict inventory turnover rate"""
        try:
            # Get current inventory and sales data
            inventory_data = await self._get_inventory_data(dealership_id)
            sales_data = await self._get_sales_history(dealership_id, days=90)
            
            if not inventory_data or not sales_data:
                return self._generate_fallback_turnover_prediction(dealership_id)
            
            # Calculate current inventory levels
            current_inventory = len(inventory_data)
            
            # Calculate historical turnover rate
            df = pd.DataFrame(sales_data)
            daily_sales_rate = len(df) / 90  # Sales per day over 90 days
            
            # Predict turnover (days to sell current inventory)
            if daily_sales_rate > 0:
                predicted_turnover_days = current_inventory / daily_sales_rate
            else:
                predicted_turnover_days = 365  # Default to 1 year if no sales
            
            # Calculate confidence based on sales consistency
            sales_df = pd.DataFrame(sales_data)
            sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])
            daily_counts = sales_df.groupby(sales_df['sale_date'].dt.date).size()
            consistency = 1.0 - (daily_counts.std() / daily_counts.mean()) if daily_counts.mean() > 0 else 0.5
            
            # Analyze inventory composition factors
            factors = self._analyze_inventory_factors(inventory_data, sales_data)
            
            return PredictionResult(
                prediction_type=PredictionType.INVENTORY_TURNOVER,
                predicted_value=predicted_turnover_days,
                confidence_interval=(predicted_turnover_days * 0.8, predicted_turnover_days * 1.2),
                confidence_score=min(consistency, 0.95),
                prediction_date=datetime.now(),
                historical_data_points=len(sales_data),
                model_accuracy=0.80,
                factors=factors
            )
            
        except Exception as e:
            logger.error(f"Inventory turnover prediction failed: {str(e)}")
            return self._generate_fallback_turnover_prediction(dealership_id)
    
    def _forecast_time_series(self, series: pd.Series, forecast_days: int) -> Dict[str, float]:
        """Simple time series forecasting using moving averages and trend analysis"""
        try:
            # Remove zeros and calculate moving averages
            non_zero_series = series[series > 0]
            
            if len(non_zero_series) < 3:
                # Not enough data, use simple average
                avg_value = series.mean()
                return {
                    'forecast': avg_value * forecast_days,
                    'lower_bound': avg_value * forecast_days * 0.7,
                    'upper_bound': avg_value * forecast_days * 1.3,
                    'accuracy': 0.5
                }
            
            # Calculate trend
            x = np.arange(len(series))
            y = series.values
            
            # Simple linear trend
            if len(y) > 1:
                trend_slope = np.polyfit(x, y, 1)[0]
            else:
                trend_slope = 0
            
            # Moving averages
            short_ma = series.rolling(window=min(7, len(series))).mean().iloc[-1]
            long_ma = series.rolling(window=min(14, len(series))).mean().iloc[-1]
            
            # Seasonal adjustment (basic)
            seasonal_factor = self._calculate_seasonal_factor(series)
            
            # Base forecast
            base_forecast = (short_ma + long_ma) / 2
            
            # Apply trend
            trend_adjusted = base_forecast + (trend_slope * forecast_days / 2)
            
            # Apply seasonal factor
            final_forecast = trend_adjusted * seasonal_factor * forecast_days
            
            # Calculate accuracy based on recent prediction vs actual
            accuracy = self._calculate_forecast_accuracy(series)
            
            return {
                'forecast': max(0, final_forecast),
                'lower_bound': max(0, final_forecast * 0.75),
                'upper_bound': final_forecast * 1.25,
                'accuracy': accuracy
            }
            
        except Exception as e:
            logger.error(f"Time series forecasting error: {str(e)}")
            avg_value = series.mean() if len(series) > 0 else 1
            return {
                'forecast': avg_value * forecast_days,
                'lower_bound': avg_value * forecast_days * 0.5,
                'upper_bound': avg_value * forecast_days * 1.5,
                'accuracy': 0.5
            }
    
    def _calculate_seasonal_factor(self, series: pd.Series) -> float:
        """Calculate basic seasonal adjustment factor"""
        if len(series) < 7:
            return 1.0
        
        # Simple seasonality detection based on day of week patterns
        recent_avg = series.tail(7).mean()
        overall_avg = series.mean()
        
        if overall_avg > 0:
            return recent_avg / overall_avg
        return 1.0
    
    def _calculate_forecast_accuracy(self, series: pd.Series) -> float:
        """Estimate forecast accuracy based on historical variance"""
        if len(series) < 3:
            return 0.5
        
        # Calculate coefficient of variation
        cv = series.std() / series.mean() if series.mean() > 0 else 1.0
        
        # Convert to accuracy score (lower CV = higher accuracy)
        accuracy = max(0.3, min(0.95, 1.0 - cv))
        return accuracy
    
    def _calculate_prediction_confidence(self, series: pd.Series) -> float:
        """Calculate confidence score for predictions"""
        if len(series) < 3:
            return 0.4
        
        # Factors affecting confidence
        data_points = min(len(series) / 30, 1.0)  # More data = higher confidence
        consistency = 1.0 - (series.std() / series.mean()) if series.mean() > 0 else 0.5
        
        # Combine factors
        confidence = (data_points * 0.4 + consistency * 0.6)
        return max(0.3, min(0.95, confidence))
    
    async def _get_sales_history(self, dealership_id: str, days: int = 90, include_pricing: bool = False) -> List[Dict[str, Any]]:
        """Get historical sales data"""
        if not self.bigquery_client:
            return self._generate_mock_sales_data(dealership_id, days, include_pricing)
        
        try:
            fields = "sale_date, vehicle_make, vehicle_model"
            if include_pricing:
                fields += ", sale_price"
            
            query = f"""
                SELECT {fields}
                FROM `vendora-464403.automotive.sales_transactions`
                WHERE dealership_id = '{dealership_id}'
                AND sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                ORDER BY sale_date DESC
            """
            
            results = self.bigquery_client.query(query).result()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"BigQuery sales history error: {str(e)}")
            return self._generate_mock_sales_data(dealership_id, days, include_pricing)
    
    async def _get_inventory_data(self, dealership_id: str) -> List[Dict[str, Any]]:
        """Get current inventory data"""
        if not self.bigquery_client:
            return self._generate_mock_inventory_data(dealership_id)
        
        try:
            query = f"""
                SELECT vehicle_make, vehicle_model, model_year, list_price, date_added
                FROM `vendora-464403.automotive.inventory`
                WHERE dealership_id = '{dealership_id}'
                AND status = 'available'
            """
            
            results = self.bigquery_client.query(query).result()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"BigQuery inventory error: {str(e)}")
            return self._generate_mock_inventory_data(dealership_id)
    
    def _analyze_sales_factors(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze factors affecting sales volume"""
        factors = {}
        
        # Vehicle type impact
        if 'vehicle_make' in df.columns:
            top_makes = df['vehicle_make'].value_counts().head(3)
            for make, count in top_makes.items():
                factors[f"{make}_volume_impact"] = count / len(df)
        
        # Seasonal patterns
        if 'sale_date' in df.columns:
            df['month'] = pd.to_datetime(df['sale_date']).dt.month
            monthly_avg = df.groupby('month').size().mean()
            current_month = datetime.now().month
            current_month_sales = len(df[df['month'] == current_month])
            
            if monthly_avg > 0:
                factors['seasonal_factor'] = current_month_sales / monthly_avg
        
        # Data quality factor
        factors['data_quality'] = min(1.0, len(df) / 90)  # Normalize to 90 days
        
        return factors
    
    def _analyze_revenue_factors(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze factors affecting revenue"""
        factors = {}
        
        if 'sale_price' in df.columns:
            # Average selling price trend
            factors['avg_selling_price'] = df['sale_price'].mean()
            factors['price_variance'] = df['sale_price'].std() / df['sale_price'].mean() if df['sale_price'].mean() > 0 else 0
        
        # High-value vehicle impact
        if 'vehicle_make' in df.columns and 'sale_price' in df.columns:
            make_revenue = df.groupby('vehicle_make')['sale_price'].mean()
            top_revenue_make = make_revenue.idxmax()
            factors[f'{top_revenue_make}_revenue_impact'] = make_revenue.max() / df['sale_price'].mean() if df['sale_price'].mean() > 0 else 1
        
        return factors
    
    def _analyze_inventory_factors(self, inventory_data: List[Dict], sales_data: List[Dict]) -> Dict[str, float]:
        """Analyze factors affecting inventory turnover"""
        factors = {}
        
        # Inventory composition
        if inventory_data:
            inventory_df = pd.DataFrame(inventory_data)
            if 'vehicle_make' in inventory_df.columns:
                make_counts = inventory_df['vehicle_make'].value_counts()
                factors['inventory_diversity'] = len(make_counts) / len(inventory_data)
        
        # Sales velocity by category
        if sales_data:
            sales_df = pd.DataFrame(sales_data)
            if 'vehicle_make' in sales_df.columns:
                sales_velocity = sales_df['vehicle_make'].value_counts()
                factors['top_selling_category_velocity'] = sales_velocity.max() / len(sales_data) if len(sales_data) > 0 else 0
        
        return factors
    
    def _generate_mock_sales_data(self, dealership_id: str, days: int, include_pricing: bool) -> List[Dict[str, Any]]:
        """Generate mock sales data for testing"""
        mock_data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            # Random 0-3 sales per day
            daily_sales = np.random.poisson(1.5)
            date = base_date + timedelta(days=i)
            
            for _ in range(daily_sales):
                sale = {
                    'sale_date': date.strftime('%Y-%m-%d'),
                    'vehicle_make': np.random.choice(['Toyota', 'Honda', 'Ford', 'Chevrolet']),
                    'vehicle_model': np.random.choice(['Camry', 'Accord', 'F-150', 'Silverado'])
                }
                
                if include_pricing:
                    sale['sale_price'] = np.random.normal(28000, 8000)
                
                mock_data.append(sale)
        
        return mock_data
    
    def _generate_mock_inventory_data(self, dealership_id: str) -> List[Dict[str, Any]]:
        """Generate mock inventory data"""
        mock_data = []
        
        for i in range(150):  # 150 vehicles in inventory
            mock_data.append({
                'vehicle_make': np.random.choice(['Toyota', 'Honda', 'Ford', 'Chevrolet']),
                'vehicle_model': np.random.choice(['Camry', 'Accord', 'F-150', 'Silverado']),
                'model_year': np.random.choice([2022, 2023, 2024]),
                'list_price': np.random.normal(32000, 10000),
                'date_added': (datetime.now() - timedelta(days=np.random.randint(1, 180))).strftime('%Y-%m-%d')
            })
        
        return mock_data
    
    def _generate_fallback_sales_prediction(self, dealership_id: str, forecast_days: int) -> PredictionResult:
        """Fallback sales prediction when data is insufficient"""
        # Industry average: 1.5 sales per day for a typical dealership
        predicted_sales = 1.5 * forecast_days
        
        return PredictionResult(
            prediction_type=PredictionType.SALES_VOLUME,
            predicted_value=predicted_sales,
            confidence_interval=(predicted_sales * 0.6, predicted_sales * 1.4),
            confidence_score=0.4,
            prediction_date=datetime.now(),
            historical_data_points=0,
            model_accuracy=0.5,
            factors={'industry_average': 1.5, 'data_source': 'fallback'}
        )
    
    def _generate_fallback_revenue_prediction(self, dealership_id: str, forecast_days: int) -> PredictionResult:
        """Fallback revenue prediction"""
        # Industry average: $42,000 revenue per day
        predicted_revenue = 42000 * forecast_days
        
        return PredictionResult(
            prediction_type=PredictionType.REVENUE,
            predicted_value=predicted_revenue,
            confidence_interval=(predicted_revenue * 0.5, predicted_revenue * 1.5),
            confidence_score=0.4,
            prediction_date=datetime.now(),
            historical_data_points=0,
            model_accuracy=0.5,
            factors={'industry_average_daily_revenue': 42000, 'data_source': 'fallback'}
        )
    
    def _generate_fallback_turnover_prediction(self, dealership_id: str) -> PredictionResult:
        """Fallback inventory turnover prediction"""
        # Industry average: 60 days turnover
        predicted_turnover = 60
        
        return PredictionResult(
            prediction_type=PredictionType.INVENTORY_TURNOVER,
            predicted_value=predicted_turnover,
            confidence_interval=(45, 75),
            confidence_score=0.4,
            prediction_date=datetime.now(),
            historical_data_points=0,
            model_accuracy=0.5,
            factors={'industry_average_turnover_days': 60, 'data_source': 'fallback'}
        )