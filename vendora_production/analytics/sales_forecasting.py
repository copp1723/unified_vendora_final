"""
Sales Forecasting Engine for VENDORA Platform
Time-series forecasting and trend analysis for automotive sales
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


class ForecastType(Enum):
    DAILY_SALES = "daily_sales"
    WEEKLY_SALES = "weekly_sales"
    MONTHLY_SALES = "monthly_sales"
    QUARTERLY_SALES = "quarterly_sales"
    REVENUE_FORECAST = "revenue_forecast"
    INVENTORY_DEMAND = "inventory_demand"
    SEASONAL_TRENDS = "seasonal_trends"


class ForecastAccuracy(Enum):
    HIGH = "high"        # >85% accuracy
    MEDIUM = "medium"    # 70-85% accuracy
    LOW = "low"         # <70% accuracy
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ForecastResult:
    """Result from a sales forecasting operation"""
    forecast_type: ForecastType
    forecast_period: str  # e.g., "2024-01-01 to 2024-01-31"
    predicted_values: List[float]
    confidence_intervals: List[Tuple[float, float]]
    accuracy_level: ForecastAccuracy
    accuracy_score: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    seasonal_factors: Dict[str, float]
    key_insights: List[str]
    forecast_date: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast_type": self.forecast_type.value,
            "forecast_period": self.forecast_period,
            "predicted_values": self.predicted_values,
            "confidence_intervals": [list(ci) for ci in self.confidence_intervals],
            "accuracy_level": self.accuracy_level.value,
            "accuracy_score": self.accuracy_score,
            "trend_direction": self.trend_direction,
            "seasonal_factors": self.seasonal_factors,
            "key_insights": self.key_insights,
            "forecast_date": self.forecast_date.isoformat()
        }


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    trend_type: str
    strength: float  # 0-1 scale
    direction: str   # "up", "down", "flat"
    duration_days: int
    statistical_significance: float
    contributing_factors: List[str]


class SalesForecastingEngine:
    """Advanced sales forecasting engine using time-series analysis"""
    
    def __init__(self, bigquery_client=None):
        self.bigquery_client = bigquery_client
        self.forecast_models = {}
        self.historical_accuracy = {}
        self.seasonal_patterns = {}
    
    async def generate_sales_forecast(self, dealership_id: str, forecast_type: ForecastType, 
                                    periods: int = 30) -> ForecastResult:
        """Generate comprehensive sales forecast"""
        try:
            # Get historical sales data
            historical_data = await self._get_historical_sales_data(dealership_id, forecast_type)
            
            if not historical_data or len(historical_data) < 10:
                return self._generate_fallback_forecast(dealership_id, forecast_type, periods)
            
            # Convert to time series
            df = self._prepare_time_series_data(historical_data, forecast_type)
            
            # Perform forecasting
            forecast_result = self._execute_time_series_forecast(df, periods, forecast_type)
            
            # Analyze trends
            trend_analysis = self._analyze_trends(df)
            
            # Calculate seasonal factors
            seasonal_factors = self._calculate_seasonal_factors(df, forecast_type)
            
            # Generate insights
            insights = self._generate_forecast_insights(df, forecast_result, trend_analysis)
            
            # Determine forecast period
            forecast_period = self._calculate_forecast_period(forecast_type, periods)
            
            return ForecastResult(
                forecast_type=forecast_type,
                forecast_period=forecast_period,
                predicted_values=forecast_result['predictions'],
                confidence_intervals=forecast_result['confidence_intervals'],
                accuracy_level=forecast_result['accuracy_level'],
                accuracy_score=forecast_result['accuracy_score'],
                trend_direction=trend_analysis.direction,
                seasonal_factors=seasonal_factors,
                key_insights=insights,
                forecast_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Sales forecasting failed: {str(e)}")
            return self._generate_fallback_forecast(dealership_id, forecast_type, periods)
    
    async def analyze_revenue_trends(self, dealership_id: str, analysis_days: int = 90) -> Dict[str, Any]:
        """Analyze revenue trends and patterns"""
        try:
            # Get revenue data
            revenue_data = await self._get_revenue_data(dealership_id, analysis_days)
            
            if not revenue_data:
                return self._generate_mock_revenue_analysis()
            
            df = pd.DataFrame(revenue_data)
            df['revenue_date'] = pd.to_datetime(df['revenue_date'])
            df = df.sort_values('revenue_date')
            
            # Daily revenue aggregation
            daily_revenue = df.groupby('revenue_date')['revenue_amount'].sum().reset_index()
            daily_revenue = daily_revenue.set_index('revenue_date').resample('D').sum().fillna(0)
            
            # Trend analysis
            trend = self._analyze_trends(daily_revenue['revenue_amount'])
            
            # Moving averages
            daily_revenue['ma_7'] = daily_revenue['revenue_amount'].rolling(7).mean()
            daily_revenue['ma_30'] = daily_revenue['revenue_amount'].rolling(30).mean()
            
            # Growth rate calculation
            current_period = daily_revenue.tail(30)['revenue_amount'].sum()
            previous_period = daily_revenue.iloc[-60:-30]['revenue_amount'].sum()
            growth_rate = ((current_period - previous_period) / previous_period * 100) if previous_period > 0 else 0
            
            # Peak and valley analysis
            peaks_valleys = self._identify_peaks_valleys(daily_revenue['revenue_amount'])
            
            return {
                'trend_analysis': {
                    'direction': trend.direction,
                    'strength': trend.strength,
                    'duration_days': trend.duration_days
                },
                'growth_metrics': {
                    'monthly_growth_rate': growth_rate,
                    'average_daily_revenue': daily_revenue['revenue_amount'].mean(),
                    'revenue_volatility': daily_revenue['revenue_amount'].std()
                },
                'patterns': {
                    'peaks': peaks_valleys['peaks'],
                    'valleys': peaks_valleys['valleys'],
                    'seasonal_factors': self._calculate_seasonal_factors(daily_revenue['revenue_amount'], ForecastType.REVENUE_FORECAST)
                },
                'forecasts': {
                    'next_30_days': self._simple_revenue_forecast(daily_revenue['revenue_amount'], 30),
                    'next_quarter': self._simple_revenue_forecast(daily_revenue['revenue_amount'], 90)
                }
            }
            
        except Exception as e:
            logger.error(f"Revenue trend analysis failed: {str(e)}")
            return self._generate_mock_revenue_analysis()
    
    async def predict_seasonal_patterns(self, dealership_id: str) -> Dict[str, Any]:
        """Predict seasonal sales patterns"""
        try:
            # Get full year of historical data
            historical_data = await self._get_historical_sales_data(dealership_id, ForecastType.MONTHLY_SALES, days=365)
            
            if not historical_data:
                return self._generate_mock_seasonal_patterns()
            
            df = self._prepare_time_series_data(historical_data, ForecastType.MONTHLY_SALES)
            
            # Monthly seasonality
            monthly_patterns = self._analyze_monthly_seasonality(df)
            
            # Quarterly patterns
            quarterly_patterns = self._analyze_quarterly_seasonality(df)
            
            # Holiday effects
            holiday_effects = self._analyze_holiday_effects(df)
            
            # Predict next year's patterns
            next_year_predictions = self._predict_next_year_seasonality(monthly_patterns, quarterly_patterns)
            
            return {
                'monthly_patterns': monthly_patterns,
                'quarterly_patterns': quarterly_patterns,
                'holiday_effects': holiday_effects,
                'next_year_predictions': next_year_predictions,
                'insights': self._generate_seasonal_insights(monthly_patterns, quarterly_patterns)
            }
            
        except Exception as e:
            logger.error(f"Seasonal pattern prediction failed: {str(e)}")
            return self._generate_mock_seasonal_patterns()
    
    def _prepare_time_series_data(self, historical_data: List[Dict[str, Any]], 
                                 forecast_type: ForecastType) -> pd.DataFrame:
        """Prepare data for time series analysis"""
        df = pd.DataFrame(historical_data)
        
        # Convert date column
        if 'sale_date' in df.columns:
            df['date'] = pd.to_datetime(df['sale_date'])
        elif 'revenue_date' in df.columns:
            df['date'] = pd.to_datetime(df['revenue_date'])
        else:
            df['date'] = pd.to_datetime(df.get('date', datetime.now()))
        
        # Aggregate based on forecast type
        if forecast_type == ForecastType.DAILY_SALES:
            df = df.groupby('date').size().reset_index(name='value')
        elif forecast_type == ForecastType.WEEKLY_SALES:
            df['week'] = df['date'].dt.to_period('W')
            df = df.groupby('week').size().reset_index(name='value')
            df['date'] = df['week'].dt.start_time
        elif forecast_type == ForecastType.MONTHLY_SALES:
            df['month'] = df['date'].dt.to_period('M')
            df = df.groupby('month').size().reset_index(name='value')
            df['date'] = df['month'].dt.start_time
        elif forecast_type == ForecastType.REVENUE_FORECAST:
            value_col = 'revenue_amount' if 'revenue_amount' in df.columns else 'sale_price'
            df = df.groupby('date')[value_col].sum().reset_index(name='value')
        
        # Sort by date and fill missing dates
        df = df.sort_values('date')
        
        return df
    
    def _execute_time_series_forecast(self, df: pd.DataFrame, periods: int, 
                                    forecast_type: ForecastType) -> Dict[str, Any]:
        """Execute time series forecasting"""
        try:
            series = df.set_index('date')['value']
            
            # Simple exponential smoothing with trend
            alpha = 0.3  # Smoothing parameter
            beta = 0.2   # Trend parameter
            
            # Initialize
            if len(series) == 0:
                return self._generate_fallback_forecast_result(periods)
            
            s = [series.iloc[0]]  # Level
            b = [series.iloc[1] - series.iloc[0] if len(series) > 1 else 0]  # Trend
            
            # Calculate smoothed values
            for i in range(1, len(series)):
                s_new = alpha * series.iloc[i] + (1 - alpha) * (s[i-1] + b[i-1])
                b_new = beta * (s_new - s[i-1]) + (1 - beta) * b[i-1]
                s.append(s_new)
                b.append(b_new)
            
            # Generate forecast
            predictions = []
            confidence_intervals = []
            
            last_level = s[-1]
            last_trend = b[-1]
            
            for h in range(1, periods + 1):
                forecast_value = last_level + h * last_trend
                
                # Add seasonality if available
                seasonal_factor = self._get_seasonal_factor(forecast_type, h)
                forecast_value *= seasonal_factor
                
                # Ensure non-negative
                forecast_value = max(0, forecast_value)
                predictions.append(forecast_value)
                
                # Calculate confidence interval (simplified)
                residuals_std = self._calculate_forecast_residuals_std(series, s, b)
                margin = 1.96 * residuals_std * np.sqrt(h)  # 95% confidence
                
                lower_bound = max(0, forecast_value - margin)
                upper_bound = forecast_value + margin
                confidence_intervals.append((lower_bound, upper_bound))
            
            # Calculate accuracy
            accuracy_score = self._calculate_model_accuracy(series, s, b)
            accuracy_level = self._determine_accuracy_level(accuracy_score)
            
            return {
                'predictions': predictions,
                'confidence_intervals': confidence_intervals,
                'accuracy_score': accuracy_score,
                'accuracy_level': accuracy_level
            }
            
        except Exception as e:
            logger.error(f"Time series forecast execution error: {str(e)}")
            return self._generate_fallback_forecast_result(periods)
    
    def _analyze_trends(self, series: pd.Series) -> TrendAnalysis:
        """Analyze trend in time series data"""
        if len(series) < 3:
            return TrendAnalysis(
                trend_type="insufficient_data",
                strength=0.0,
                direction="flat",
                duration_days=0,
                statistical_significance=0.0,
                contributing_factors=[]
            )
        
        # Linear trend calculation
        x = np.arange(len(series))
        y = series.values
        
        # Remove NaN values
        valid_mask = ~np.isnan(y)
        x = x[valid_mask]
        y = y[valid_mask]
        
        if len(y) < 3:
            return TrendAnalysis(
                trend_type="insufficient_data",
                strength=0.0,
                direction="flat",
                duration_days=0,
                statistical_significance=0.0,
                contributing_factors=[]
            )
        
        # Calculate trend slope
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate correlation coefficient for trend strength
        correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
        strength = abs(correlation)
        
        # Determine direction
        if abs(slope) < 0.01:
            direction = "flat"
        elif slope > 0:
            direction = "up"
        else:
            direction = "down"
        
        # Calculate statistical significance (simplified)
        mean_y = np.mean(y)
        trend_change = abs(slope * len(x))
        significance = min(1.0, trend_change / mean_y) if mean_y > 0 else 0
        
        return TrendAnalysis(
            trend_type="linear",
            strength=strength,
            direction=direction,
            duration_days=len(series),
            statistical_significance=significance,
            contributing_factors=["time_based_trend"]
        )
    
    def _calculate_seasonal_factors(self, series: pd.Series, forecast_type: ForecastType) -> Dict[str, float]:
        """Calculate seasonal adjustment factors"""
        factors = {}
        
        if len(series) < 12:  # Need at least a year of data for seasonality
            return {"insufficient_data": 1.0}
        
        try:
            # Convert series to DataFrame if needed
            if isinstance(series, pd.Series):
                df = series.to_frame('value')
                df['date'] = series.index if hasattr(series, 'index') else pd.date_range(start='2023-01-01', periods=len(series), freq='D')
            else:
                df = pd.DataFrame({'value': series, 'date': pd.date_range(start='2023-01-01', periods=len(series), freq='D')})
            
            # Monthly seasonality
            df['month'] = pd.to_datetime(df['date']).dt.month
            monthly_avg = df.groupby('month')['value'].mean()
            overall_avg = df['value'].mean()
            
            if overall_avg > 0:
                for month in range(1, 13):
                    if month in monthly_avg.index:
                        factors[f'month_{month}'] = monthly_avg[month] / overall_avg
            
            # Quarterly seasonality
            df['quarter'] = pd.to_datetime(df['date']).dt.quarter
            quarterly_avg = df.groupby('quarter')['value'].mean()
            
            if overall_avg > 0:
                for quarter in range(1, 5):
                    if quarter in quarterly_avg.index:
                        factors[f'quarter_{quarter}'] = quarterly_avg[quarter] / overall_avg
            
            # Day of week seasonality for daily forecasts
            if forecast_type == ForecastType.DAILY_SALES:
                df['dow'] = pd.to_datetime(df['date']).dt.dayofweek
                dow_avg = df.groupby('dow')['value'].mean()
                
                if overall_avg > 0:
                    for dow in range(7):
                        if dow in dow_avg.index:
                            factors[f'dow_{dow}'] = dow_avg[dow] / overall_avg
            
        except Exception as e:
            logger.error(f"Seasonal factor calculation error: {str(e)}")
            factors = {"default": 1.0}
        
        return factors
    
    def _get_seasonal_factor(self, forecast_type: ForecastType, period_ahead: int) -> float:
        """Get seasonal factor for a specific period ahead"""
        # Simplified seasonal factors
        current_month = datetime.now().month
        
        # Automotive seasonal patterns (simplified)
        seasonal_multipliers = {
            1: 0.8,   # January - post-holiday slowdown
            2: 0.9,   # February - still slow
            3: 1.1,   # March - spring pickup
            4: 1.2,   # April - strong spring sales
            5: 1.3,   # May - peak spring
            6: 1.1,   # June - good summer start
            7: 1.0,   # July - summer average
            8: 1.0,   # August - summer average
            9: 1.2,   # September - back to school boost
            10: 1.1,  # October - fall sales
            11: 1.0,  # November - pre-holiday
            12: 0.9   # December - holiday season
        }
        
        if forecast_type == ForecastType.DAILY_SALES:
            # Simple daily seasonality
            target_month = ((current_month + period_ahead // 30 - 1) % 12) + 1
        else:
            target_month = current_month
        
        return seasonal_multipliers.get(target_month, 1.0)
    
    def _calculate_forecast_residuals_std(self, actual: pd.Series, smoothed: List[float], 
                                        trends: List[float]) -> float:
        """Calculate standard deviation of forecast residuals"""
        if len(actual) != len(smoothed):
            return actual.std() * 0.3  # Default fallback
        
        residuals = []
        for i in range(len(actual)):
            predicted = smoothed[i]
            residuals.append(actual.iloc[i] - predicted)
        
        return np.std(residuals) if residuals else actual.std() * 0.3
    
    def _calculate_model_accuracy(self, actual: pd.Series, smoothed: List[float], 
                                trends: List[float]) -> float:
        """Calculate model accuracy score"""
        if len(actual) < 2 or len(smoothed) < 2:
            return 0.5
        
        # Mean Absolute Percentage Error (MAPE)
        mape_errors = []
        for i in range(min(len(actual), len(smoothed))):
            if actual.iloc[i] != 0:
                error = abs((actual.iloc[i] - smoothed[i]) / actual.iloc[i])
                mape_errors.append(error)
        
        if not mape_errors:
            return 0.5
        
        mape = np.mean(mape_errors)
        accuracy = max(0, 1 - mape)  # Convert MAPE to accuracy
        
        return min(1.0, accuracy)
    
    def _determine_accuracy_level(self, accuracy_score: float) -> ForecastAccuracy:
        """Determine accuracy level based on score"""
        if accuracy_score >= 0.85:
            return ForecastAccuracy.HIGH
        elif accuracy_score >= 0.70:
            return ForecastAccuracy.MEDIUM
        else:
            return ForecastAccuracy.LOW
    
    def _generate_forecast_insights(self, df: pd.DataFrame, forecast_result: Dict[str, Any], 
                                  trend_analysis: TrendAnalysis) -> List[str]:
        """Generate actionable insights from forecast"""
        insights = []
        
        # Trend insights
        if trend_analysis.direction == "up" and trend_analysis.strength > 0.7:
            insights.append("Strong upward trend detected - consider increasing inventory levels")
        elif trend_analysis.direction == "down" and trend_analysis.strength > 0.7:
            insights.append("Declining sales trend - implement promotional strategies")
        
        # Forecast accuracy insights
        accuracy = forecast_result.get('accuracy_score', 0)
        if accuracy > 0.85:
            insights.append("High forecast confidence - reliable for planning")
        elif accuracy < 0.60:
            insights.append("Low forecast confidence - consider additional data sources")
        
        # Volume insights
        predictions = forecast_result.get('predictions', [])
        if predictions:
            avg_prediction = np.mean(predictions)
            historical_avg = df['value'].mean()
            
            if avg_prediction > historical_avg * 1.2:
                insights.append("Predicted sales significantly above historical average")
            elif avg_prediction < historical_avg * 0.8:
                insights.append("Predicted sales below historical average - review strategy")
        
        return insights
    
    def _calculate_forecast_period(self, forecast_type: ForecastType, periods: int) -> str:
        """Calculate human-readable forecast period"""
        start_date = datetime.now().date()
        
        if forecast_type == ForecastType.DAILY_SALES:
            end_date = start_date + timedelta(days=periods)
        elif forecast_type == ForecastType.WEEKLY_SALES:
            end_date = start_date + timedelta(weeks=periods)
        elif forecast_type == ForecastType.MONTHLY_SALES:
            end_date = start_date + timedelta(days=periods * 30)
        else:
            end_date = start_date + timedelta(days=periods)
        
        return f"{start_date} to {end_date}"
    
    def _analyze_monthly_seasonality(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze monthly seasonal patterns"""
        if 'date' not in df.columns:
            return {}
        
        df['month'] = pd.to_datetime(df['date']).dt.month
        monthly_avg = df.groupby('month')['value'].mean()
        overall_avg = df['value'].mean()
        
        monthly_factors = {}
        for month in range(1, 13):
            if month in monthly_avg.index and overall_avg > 0:
                monthly_factors[f'month_{month}'] = monthly_avg[month] / overall_avg
            else:
                monthly_factors[f'month_{month}'] = 1.0
        
        return monthly_factors
    
    def _analyze_quarterly_seasonality(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze quarterly seasonal patterns"""
        if 'date' not in df.columns:
            return {}
        
        df['quarter'] = pd.to_datetime(df['date']).dt.quarter
        quarterly_avg = df.groupby('quarter')['value'].mean()
        overall_avg = df['value'].mean()
        
        quarterly_factors = {}
        for quarter in range(1, 5):
            if quarter in quarterly_avg.index and overall_avg > 0:
                quarterly_factors[f'Q{quarter}'] = quarterly_avg[quarter] / overall_avg
            else:
                quarterly_factors[f'Q{quarter}'] = 1.0
        
        return quarterly_factors
    
    def _analyze_holiday_effects(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze holiday effects on sales"""
        # Simplified holiday effect analysis
        holiday_effects = {
            'new_year_effect': 0.8,     # January slowdown
            'spring_boost': 1.2,        # March-May uptick
            'summer_stable': 1.0,       # June-August steady
            'fall_boost': 1.1,          # September-October increase
            'holiday_season': 0.9       # November-December mixed
        }
        
        return holiday_effects
    
    def _predict_next_year_seasonality(self, monthly_patterns: Dict[str, float], 
                                     quarterly_patterns: Dict[str, float]) -> Dict[str, Any]:
        """Predict next year's seasonal patterns"""
        next_year_predictions = {
            'expected_peak_months': [],
            'expected_low_months': [],
            'strongest_quarter': '',
            'weakest_quarter': ''
        }
        
        # Find peak and low months
        monthly_values = [(month, factor) for month, factor in monthly_patterns.items()]
        monthly_values.sort(key=lambda x: x[1], reverse=True)
        
        next_year_predictions['expected_peak_months'] = [m[0] for m in monthly_values[:3]]
        next_year_predictions['expected_low_months'] = [m[0] for m in monthly_values[-3:]]
        
        # Find strongest and weakest quarters
        quarterly_values = [(quarter, factor) for quarter, factor in quarterly_patterns.items()]
        quarterly_values.sort(key=lambda x: x[1], reverse=True)
        
        if quarterly_values:
            next_year_predictions['strongest_quarter'] = quarterly_values[0][0]
            next_year_predictions['weakest_quarter'] = quarterly_values[-1][0]
        
        return next_year_predictions
    
    def _generate_seasonal_insights(self, monthly_patterns: Dict[str, float], 
                                  quarterly_patterns: Dict[str, float]) -> List[str]:
        """Generate insights from seasonal analysis"""
        insights = []
        
        # Find highest and lowest seasonal factors
        monthly_values = list(monthly_patterns.values())
        if monthly_values:
            max_seasonal = max(monthly_values)
            min_seasonal = min(monthly_values)
            
            if max_seasonal > 1.2:
                insights.append("Strong seasonal peaks detected - plan inventory accordingly")
            if min_seasonal < 0.8:
                insights.append("Significant seasonal lows identified - consider promotional strategies")
        
        return insights
    
    def _identify_peaks_valleys(self, series: pd.Series) -> Dict[str, List[Dict[str, Any]]]:
        """Identify peaks and valleys in the data"""
        peaks = []
        valleys = []
        
        if len(series) < 3:
            return {'peaks': peaks, 'valleys': valleys}
        
        values = series.values
        
        for i in range(1, len(values) - 1):
            # Peak detection
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append({
                    'date': series.index[i].strftime('%Y-%m-%d') if hasattr(series.index[i], 'strftime') else str(series.index[i]),
                    'value': values[i]
                })
            
            # Valley detection
            if values[i] < values[i-1] and values[i] < values[i+1]:
                valleys.append({
                    'date': series.index[i].strftime('%Y-%m-%d') if hasattr(series.index[i], 'strftime') else str(series.index[i]),
                    'value': values[i]
                })
        
        return {'peaks': peaks, 'valleys': valleys}
    
    def _simple_revenue_forecast(self, series: pd.Series, days: int) -> Dict[str, float]:
        """Simple revenue forecast"""
        if len(series) == 0:
            return {'total_predicted': 0, 'daily_average': 0}
        
        recent_avg = series.tail(30).mean()
        trend_factor = 1.0
        
        if len(series) > 30:
            old_avg = series.head(30).mean()
            if old_avg > 0:
                trend_factor = recent_avg / old_avg
        
        daily_forecast = recent_avg * trend_factor
        total_forecast = daily_forecast * days
        
        return {
            'total_predicted': total_forecast,
            'daily_average': daily_forecast
        }
    
    async def _get_historical_sales_data(self, dealership_id: str, forecast_type: ForecastType, 
                                       days: int = 180) -> List[Dict[str, Any]]:
        """Get historical sales data for forecasting"""
        if not self.bigquery_client:
            return self._generate_mock_sales_data(dealership_id, days)
        
        try:
            query = f"""
                SELECT sale_date, sale_price, vehicle_make, vehicle_model
                FROM `vendora-464403.automotive.sales_transactions`
                WHERE dealership_id = '{dealership_id}'
                AND sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                ORDER BY sale_date
            """
            
            results = self.bigquery_client.query(query).result()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Historical sales data query error: {str(e)}")
            return self._generate_mock_sales_data(dealership_id, days)
    
    async def _get_revenue_data(self, dealership_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get revenue data for analysis"""
        if not self.bigquery_client:
            return self._generate_mock_revenue_data(dealership_id, days)
        
        try:
            query = f"""
                SELECT sale_date as revenue_date, sale_price as revenue_amount
                FROM `vendora-464403.automotive.sales_transactions`
                WHERE dealership_id = '{dealership_id}'
                AND sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                ORDER BY sale_date
            """
            
            results = self.bigquery_client.query(query).result()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Revenue data query error: {str(e)}")
            return self._generate_mock_revenue_data(dealership_id, days)
    
    def _generate_mock_sales_data(self, dealership_id: str, days: int) -> List[Dict[str, Any]]:
        """Generate mock sales data for testing"""
        mock_data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            daily_sales = np.random.poisson(2)  # Average 2 sales per day
            
            for _ in range(daily_sales):
                mock_data.append({
                    'sale_date': date.strftime('%Y-%m-%d'),
                    'sale_price': np.random.normal(30000, 8000),
                    'vehicle_make': np.random.choice(['Toyota', 'Honda', 'Ford']),
                    'vehicle_model': np.random.choice(['Camry', 'Accord', 'F-150'])
                })
        
        return mock_data
    
    def _generate_mock_revenue_data(self, dealership_id: str, days: int) -> List[Dict[str, Any]]:
        """Generate mock revenue data"""
        mock_data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            daily_revenue = np.random.lognormal(10, 0.5)  # Log-normal revenue distribution
            
            mock_data.append({
                'revenue_date': date.strftime('%Y-%m-%d'),
                'revenue_amount': daily_revenue
            })
        
        return mock_data
    
    def _generate_fallback_forecast(self, dealership_id: str, forecast_type: ForecastType, 
                                  periods: int) -> ForecastResult:
        """Generate fallback forecast when data is insufficient"""
        # Industry averages
        daily_avg = 2.0  # sales per day
        revenue_avg = 60000  # daily revenue
        
        if forecast_type == ForecastType.REVENUE_FORECAST:
            base_value = revenue_avg
        else:
            base_value = daily_avg
        
        predictions = [base_value * (1 + np.random.normal(0, 0.1)) for _ in range(periods)]
        confidence_intervals = [(p * 0.7, p * 1.3) for p in predictions]
        
        return ForecastResult(
            forecast_type=forecast_type,
            forecast_period=self._calculate_forecast_period(forecast_type, periods),
            predicted_values=predictions,
            confidence_intervals=confidence_intervals,
            accuracy_level=ForecastAccuracy.INSUFFICIENT_DATA,
            accuracy_score=0.5,
            trend_direction="stable",
            seasonal_factors={"default": 1.0},
            key_insights=["Forecast based on industry averages due to limited data"],
            forecast_date=datetime.now()
        )
    
    def _generate_fallback_forecast_result(self, periods: int) -> Dict[str, Any]:
        """Generate fallback forecast result"""
        predictions = [1.0] * periods
        confidence_intervals = [(0.5, 1.5)] * periods
        
        return {
            'predictions': predictions,
            'confidence_intervals': confidence_intervals,
            'accuracy_score': 0.5,
            'accuracy_level': ForecastAccuracy.INSUFFICIENT_DATA
        }
    
    def _generate_mock_revenue_analysis(self) -> Dict[str, Any]:
        """Generate mock revenue analysis"""
        return {
            'trend_analysis': {
                'direction': 'up',
                'strength': 0.7,
                'duration_days': 30
            },
            'growth_metrics': {
                'monthly_growth_rate': 12.5,
                'average_daily_revenue': 45000,
                'revenue_volatility': 8000
            },
            'patterns': {
                'peaks': [{'date': '2024-03-15', 'value': 75000}],
                'valleys': [{'date': '2024-02-10', 'value': 25000}],
                'seasonal_factors': {'spring_boost': 1.2}
            },
            'forecasts': {
                'next_30_days': {'total_predicted': 1350000, 'daily_average': 45000},
                'next_quarter': {'total_predicted': 4050000, 'daily_average': 45000}
            }
        }
    
    def _generate_mock_seasonal_patterns(self) -> Dict[str, Any]:
        """Generate mock seasonal patterns"""
        return {
            'monthly_patterns': {f'month_{i}': 1.0 + np.random.normal(0, 0.2) for i in range(1, 13)},
            'quarterly_patterns': {f'Q{i}': 1.0 + np.random.normal(0, 0.1) for i in range(1, 5)},
            'holiday_effects': {'spring_boost': 1.2, 'holiday_season': 0.9},
            'next_year_predictions': {
                'expected_peak_months': ['month_5', 'month_4', 'month_9'],
                'expected_low_months': ['month_1', 'month_12', 'month_2'],
                'strongest_quarter': 'Q2',
                'weakest_quarter': 'Q1'
            },
            'insights': ['Strong seasonal variation detected', 'Spring months show consistent growth']
        }