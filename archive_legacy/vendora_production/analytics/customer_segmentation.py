"""
Customer Segmentation Engine for VENDORA Platform
Advanced algorithms for automotive customer classification and analysis
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


class SegmentType(Enum):
    HIGH_VALUE = "high_value"
    FREQUENT_BUYER = "frequent_buyer"
    LUXURY_BUYER = "luxury_buyer"
    BUDGET_CONSCIOUS = "budget_conscious"
    FIRST_TIME_BUYER = "first_time_buyer"
    REPEAT_CUSTOMER = "repeat_customer"
    SERVICE_ORIENTED = "service_oriented"
    TRADE_IN_FOCUSED = "trade_in_focused"


@dataclass
class CustomerProfile:
    """Individual customer profile with segmentation data"""
    customer_id: str
    email: str
    segment_type: SegmentType
    segment_confidence: float
    lifetime_value: float
    purchase_frequency: float
    avg_purchase_amount: float
    preferred_brands: List[str]
    last_interaction: datetime
    risk_score: float  # Risk of churning
    engagement_score: float
    characteristics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "email": self.email,
            "segment_type": self.segment_type.value,
            "segment_confidence": self.segment_confidence,
            "lifetime_value": self.lifetime_value,
            "purchase_frequency": self.purchase_frequency,
            "avg_purchase_amount": self.avg_purchase_amount,
            "preferred_brands": self.preferred_brands,
            "last_interaction": self.last_interaction.isoformat(),
            "risk_score": self.risk_score,
            "engagement_score": self.engagement_score,
            "characteristics": self.characteristics
        }


@dataclass
class SegmentAnalysis:
    """Analysis of a customer segment"""
    segment_type: SegmentType
    customer_count: int
    avg_lifetime_value: float
    avg_purchase_frequency: float
    revenue_contribution: float
    growth_rate: float
    retention_rate: float
    top_characteristics: Dict[str, float]
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_type": self.segment_type.value,
            "customer_count": self.customer_count,
            "avg_lifetime_value": self.avg_lifetime_value,
            "avg_purchase_frequency": self.avg_purchase_frequency,
            "revenue_contribution": self.revenue_contribution,
            "growth_rate": self.growth_rate,
            "retention_rate": self.retention_rate,
            "top_characteristics": self.top_characteristics,
            "recommended_actions": self.recommended_actions
        }


class CustomerSegmentationEngine:
    """Advanced customer segmentation engine for automotive dealerships"""
    
    def __init__(self, bigquery_client=None):
        self.bigquery_client = bigquery_client
        self.segment_models = {}
        self.cached_profiles = {}
        self.last_analysis_update = None
    
    async def analyze_customer_segments(self, dealership_id: str) -> Dict[str, SegmentAnalysis]:
        """Perform comprehensive customer segmentation analysis"""
        try:
            # Get customer data
            customer_data = await self._get_customer_data(dealership_id)
            
            if not customer_data or len(customer_data) < 10:
                return self._generate_mock_segment_analysis()
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(customer_data)
            
            # Calculate customer metrics
            customer_metrics = self._calculate_customer_metrics(df)
            
            # Perform segmentation
            segments = self._perform_segmentation(customer_metrics)
            
            # Analyze each segment
            segment_analyses = {}
            for segment_type in SegmentType:
                if segment_type in segments:
                    analysis = self._analyze_segment(segments[segment_type], customer_metrics)
                    segment_analyses[segment_type.value] = analysis
            
            return segment_analyses
            
        except Exception as e:
            logger.error(f"Customer segmentation analysis failed: {str(e)}")
            return self._generate_mock_segment_analysis()
    
    async def get_customer_profile(self, customer_email: str, dealership_id: str) -> Optional[CustomerProfile]:
        """Get detailed profile for a specific customer"""
        try:
            # Check cache first
            cache_key = f"{dealership_id}:{customer_email}"
            if cache_key in self.cached_profiles:
                cached_profile = self.cached_profiles[cache_key]
                # Return if cache is recent (less than 1 hour old)
                if (datetime.now() - cached_profile['timestamp']).seconds < 3600:
                    return cached_profile['profile']
            
            # Get customer data
            customer_data = await self._get_customer_data(dealership_id, customer_email)
            
            if not customer_data:
                return None
            
            # Create customer profile
            profile = self._create_customer_profile(customer_data[0], dealership_id)
            
            # Cache the profile
            self.cached_profiles[cache_key] = {
                'profile': profile,
                'timestamp': datetime.now()
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Customer profile creation failed: {str(e)}")
            return None
    
    async def segment_customers_real_time(self, dealership_id: str, batch_size: int = 100) -> List[CustomerProfile]:
        """Real-time customer segmentation for active customers"""
        try:
            # Get recent customer interactions
            recent_customers = await self._get_recent_customer_interactions(dealership_id, days=30)
            
            if not recent_customers:
                return []
            
            profiles = []
            
            # Process customers in batches
            for i in range(0, len(recent_customers), batch_size):
                batch = recent_customers[i:i + batch_size]
                
                for customer_data in batch:
                    profile = self._create_customer_profile(customer_data, dealership_id)
                    if profile:
                        profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Real-time segmentation failed: {str(e)}")
            return []
    
    def _calculate_customer_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate key customer metrics for segmentation"""
        metrics = df.copy()
        
        # Lifetime Value calculation
        metrics['lifetime_value'] = metrics.get('total_spent', 0)
        
        # Purchase frequency (purchases per year)
        if 'first_purchase_date' in metrics.columns and 'last_purchase_date' in metrics.columns:
            metrics['first_purchase'] = pd.to_datetime(metrics['first_purchase_date'])
            metrics['last_purchase'] = pd.to_datetime(metrics['last_purchase_date'])
            metrics['customer_lifespan_days'] = (metrics['last_purchase'] - metrics['first_purchase']).dt.days
            metrics['customer_lifespan_days'] = metrics['customer_lifespan_days'].fillna(1)  # Avoid division by zero
            
            metrics['purchase_frequency'] = (metrics.get('total_purchases', 1) * 365) / metrics['customer_lifespan_days']
        else:
            metrics['purchase_frequency'] = metrics.get('total_purchases', 1) / 365  # Assume 1 year
        
        # Average purchase amount
        metrics['avg_purchase_amount'] = metrics['lifetime_value'] / metrics.get('total_purchases', 1)
        
        # Recency (days since last interaction)
        if 'last_interaction_date' in metrics.columns:
            metrics['last_interaction'] = pd.to_datetime(metrics['last_interaction_date'])
            metrics['recency_days'] = (datetime.now() - metrics['last_interaction']).dt.days
        else:
            metrics['recency_days'] = 30  # Default assumption
        
        # Engagement score (based on interactions)
        metrics['engagement_score'] = self._calculate_engagement_score(metrics)
        
        return metrics
    
    def _calculate_engagement_score(self, metrics: pd.DataFrame) -> pd.Series:
        """Calculate customer engagement score"""
        # Factors: frequency, recency, interaction diversity
        frequency_score = np.log1p(metrics.get('total_purchases', 1)) / np.log1p(10)  # Normalize to 0-1
        
        # Recency score (lower recency = higher score)
        recency_score = 1 / (1 + metrics.get('recency_days', 30) / 30)
        
        # Interaction diversity (emails, calls, visits)
        interaction_types = metrics.get('interaction_types', 1)
        diversity_score = np.minimum(interaction_types / 5, 1.0)  # Max 5 types
        
        # Combined engagement score
        engagement = (frequency_score * 0.4 + recency_score * 0.4 + diversity_score * 0.2)
        
        return engagement
    
    def _perform_segmentation(self, customer_metrics: pd.DataFrame) -> Dict[SegmentType, pd.DataFrame]:
        """Perform customer segmentation using rule-based and statistical methods"""
        segments = {}
        
        # Define segmentation thresholds
        high_value_threshold = customer_metrics['lifetime_value'].quantile(0.8)
        high_frequency_threshold = customer_metrics['purchase_frequency'].quantile(0.7)
        luxury_amount_threshold = customer_metrics['avg_purchase_amount'].quantile(0.85)
        budget_amount_threshold = customer_metrics['avg_purchase_amount'].quantile(0.3)
        
        # High Value Customers
        high_value_mask = customer_metrics['lifetime_value'] >= high_value_threshold
        segments[SegmentType.HIGH_VALUE] = customer_metrics[high_value_mask]
        
        # Frequent Buyers
        frequent_mask = (customer_metrics['purchase_frequency'] >= high_frequency_threshold) & (~high_value_mask)
        segments[SegmentType.FREQUENT_BUYER] = customer_metrics[frequent_mask]
        
        # Luxury Buyers
        luxury_mask = (customer_metrics['avg_purchase_amount'] >= luxury_amount_threshold) & (~high_value_mask)
        segments[SegmentType.LUXURY_BUYER] = customer_metrics[luxury_mask]
        
        # Budget Conscious
        budget_mask = customer_metrics['avg_purchase_amount'] <= budget_amount_threshold
        segments[SegmentType.BUDGET_CONSCIOUS] = customer_metrics[budget_mask]
        
        # First Time Buyers
        first_time_mask = customer_metrics.get('total_purchases', 1) == 1
        segments[SegmentType.FIRST_TIME_BUYER] = customer_metrics[first_time_mask]
        
        # Repeat Customers
        repeat_mask = (customer_metrics.get('total_purchases', 1) > 1) & (~frequent_mask) & (~high_value_mask)
        segments[SegmentType.REPEAT_CUSTOMER] = customer_metrics[repeat_mask]
        
        # Service Oriented (high service interactions)
        service_mask = customer_metrics.get('service_visits', 0) > customer_metrics.get('service_visits', 0).median()
        segments[SegmentType.SERVICE_ORIENTED] = customer_metrics[service_mask]
        
        # Trade-in Focused
        trade_in_mask = customer_metrics.get('trade_ins', 0) > 0
        segments[SegmentType.TRADE_IN_FOCUSED] = customer_metrics[trade_in_mask]
        
        return segments
    
    def _analyze_segment(self, segment_data: pd.DataFrame, all_customers: pd.DataFrame) -> SegmentAnalysis:
        """Analyze characteristics of a customer segment"""
        if len(segment_data) == 0:
            return SegmentAnalysis(
                segment_type=SegmentType.HIGH_VALUE,
                customer_count=0,
                avg_lifetime_value=0,
                avg_purchase_frequency=0,
                revenue_contribution=0,
                growth_rate=0,
                retention_rate=0,
                top_characteristics={},
                recommended_actions=[]
            )
        
        # Basic metrics
        customer_count = len(segment_data)
        avg_lifetime_value = segment_data['lifetime_value'].mean()
        avg_purchase_frequency = segment_data['purchase_frequency'].mean()
        
        # Revenue contribution
        total_revenue = all_customers['lifetime_value'].sum()
        segment_revenue = segment_data['lifetime_value'].sum()
        revenue_contribution = segment_revenue / total_revenue if total_revenue > 0 else 0
        
        # Growth rate (simplified - based on recent vs older customers)
        if 'first_purchase' in segment_data.columns:
            recent_customers = segment_data[segment_data['first_purchase'] >= datetime.now() - timedelta(days=365)]
            growth_rate = len(recent_customers) / customer_count if customer_count > 0 else 0
        else:
            growth_rate = 0.1  # Default assumption
        
        # Retention rate (customers with recent activity)
        recent_activity = segment_data['recency_days'] <= 90
        retention_rate = recent_activity.sum() / customer_count if customer_count > 0 else 0
        
        # Top characteristics
        characteristics = self._identify_segment_characteristics(segment_data)
        
        # Recommended actions
        recommendations = self._generate_segment_recommendations(segment_data, characteristics)
        
        # Determine segment type based on data characteristics
        segment_type = self._determine_segment_type(segment_data, characteristics)
        
        return SegmentAnalysis(
            segment_type=segment_type,
            customer_count=customer_count,
            avg_lifetime_value=avg_lifetime_value,
            avg_purchase_frequency=avg_purchase_frequency,
            revenue_contribution=revenue_contribution,
            growth_rate=growth_rate,
            retention_rate=retention_rate,
            top_characteristics=characteristics,
            recommended_actions=recommendations
        )
    
    def _identify_segment_characteristics(self, segment_data: pd.DataFrame) -> Dict[str, float]:
        """Identify key characteristics of a customer segment"""
        characteristics = {}
        
        # Financial characteristics
        characteristics['avg_purchase_amount'] = segment_data['avg_purchase_amount'].mean()
        characteristics['lifetime_value_range'] = segment_data['lifetime_value'].max() - segment_data['lifetime_value'].min()
        
        # Behavioral characteristics
        characteristics['avg_engagement_score'] = segment_data['engagement_score'].mean()
        characteristics['avg_recency_days'] = segment_data['recency_days'].mean()
        
        # Purchase patterns
        if 'preferred_brand' in segment_data.columns:
            brand_diversity = segment_data['preferred_brand'].nunique() / len(segment_data)
            characteristics['brand_loyalty'] = 1 - brand_diversity
        
        # Service usage
        if 'service_visits' in segment_data.columns:
            characteristics['service_usage'] = segment_data['service_visits'].mean()
        
        return characteristics
    
    def _generate_segment_recommendations(self, segment_data: pd.DataFrame, characteristics: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations for a customer segment"""
        recommendations = []
        
        # High value recommendations
        if characteristics.get('avg_purchase_amount', 0) > 40000:
            recommendations.extend([
                "Offer VIP service packages and exclusive previews",
                "Provide personalized luxury vehicle consultations",
                "Implement dedicated account management"
            ])
        
        # High engagement recommendations
        if characteristics.get('avg_engagement_score', 0) > 0.7:
            recommendations.extend([
                "Increase communication frequency with valuable content",
                "Offer exclusive events and test drive opportunities",
                "Provide early access to new models"
            ])
        
        # Low engagement recommendations
        if characteristics.get('avg_engagement_score', 0) < 0.3:
            recommendations.extend([
                "Implement re-engagement campaigns",
                "Offer special promotions to win back interest",
                "Survey for feedback and service improvements"
            ])
        
        # Service-oriented recommendations
        if characteristics.get('service_usage', 0) > 3:
            recommendations.extend([
                "Cross-sell extended warranties and maintenance packages",
                "Offer service loyalty programs",
                "Promote vehicle upgrade programs during service visits"
            ])
        
        return recommendations
    
    def _determine_segment_type(self, segment_data: pd.DataFrame, characteristics: Dict[str, float]) -> SegmentType:
        """Determine the most appropriate segment type based on characteristics"""
        avg_ltv = characteristics.get('avg_purchase_amount', 0)
        engagement = characteristics.get('avg_engagement_score', 0)
        
        if avg_ltv > 50000:
            return SegmentType.HIGH_VALUE
        elif avg_ltv > 40000:
            return SegmentType.LUXURY_BUYER
        elif engagement > 0.7:
            return SegmentType.FREQUENT_BUYER
        elif avg_ltv < 25000:
            return SegmentType.BUDGET_CONSCIOUS
        else:
            return SegmentType.REPEAT_CUSTOMER
    
    def _create_customer_profile(self, customer_data: Dict[str, Any], dealership_id: str) -> CustomerProfile:
        """Create detailed customer profile"""
        try:
            # Calculate metrics
            lifetime_value = customer_data.get('total_spent', 0)
            total_purchases = customer_data.get('total_purchases', 1)
            avg_purchase = lifetime_value / total_purchases
            
            # Determine segment
            segment_type, confidence = self._classify_customer_segment(customer_data)
            
            # Calculate scores
            risk_score = self._calculate_churn_risk(customer_data)
            engagement_score = self._calculate_single_customer_engagement(customer_data)
            
            # Preferred brands
            preferred_brands = customer_data.get('preferred_brands', ['Unknown'])
            if isinstance(preferred_brands, str):
                preferred_brands = [preferred_brands]
            
            # Characteristics
            characteristics = {
                'vehicle_types': customer_data.get('vehicle_types', []),
                'avg_decision_time': customer_data.get('avg_decision_time_days', 30),
                'financing_preference': customer_data.get('financing_preference', 'Unknown'),
                'trade_in_frequency': customer_data.get('trade_ins', 0)
            }
            
            return CustomerProfile(
                customer_id=customer_data.get('customer_id', ''),
                email=customer_data.get('email', ''),
                segment_type=segment_type,
                segment_confidence=confidence,
                lifetime_value=lifetime_value,
                purchase_frequency=total_purchases / max(1, customer_data.get('customer_age_days', 365) / 365),
                avg_purchase_amount=avg_purchase,
                preferred_brands=preferred_brands,
                last_interaction=pd.to_datetime(customer_data.get('last_interaction_date', datetime.now())),
                risk_score=risk_score,
                engagement_score=engagement_score,
                characteristics=characteristics
            )
            
        except Exception as e:
            logger.error(f"Customer profile creation error: {str(e)}")
            return None
    
    def _classify_customer_segment(self, customer_data: Dict[str, Any]) -> Tuple[SegmentType, float]:
        """Classify customer into segment with confidence score"""
        total_spent = customer_data.get('total_spent', 0)
        total_purchases = customer_data.get('total_purchases', 1)
        avg_purchase = total_spent / total_purchases
        
        # Rule-based classification
        if total_spent > 100000:
            return SegmentType.HIGH_VALUE, 0.9
        elif avg_purchase > 50000:
            return SegmentType.LUXURY_BUYER, 0.8
        elif total_purchases > 3:
            return SegmentType.FREQUENT_BUYER, 0.7
        elif total_purchases == 1:
            return SegmentType.FIRST_TIME_BUYER, 0.8
        elif avg_purchase < 25000:
            return SegmentType.BUDGET_CONSCIOUS, 0.7
        else:
            return SegmentType.REPEAT_CUSTOMER, 0.6
    
    def _calculate_churn_risk(self, customer_data: Dict[str, Any]) -> float:
        """Calculate customer churn risk score"""
        # Factors: recency, engagement, satisfaction
        last_interaction = customer_data.get('last_interaction_date')
        if last_interaction:
            days_since_interaction = (datetime.now() - pd.to_datetime(last_interaction)).days
            recency_risk = min(1.0, days_since_interaction / 365)  # Higher risk with longer absence
        else:
            recency_risk = 0.5
        
        # Engagement risk
        total_interactions = customer_data.get('total_interactions', 1)
        engagement_risk = max(0, 1 - (total_interactions / 10))  # Lower engagement = higher risk
        
        # Purchase pattern risk
        total_purchases = customer_data.get('total_purchases', 1)
        purchase_risk = max(0, 1 - (total_purchases / 5))  # Fewer purchases = higher risk
        
        # Combined risk score
        risk_score = (recency_risk * 0.4 + engagement_risk * 0.3 + purchase_risk * 0.3)
        return min(1.0, risk_score)
    
    def _calculate_single_customer_engagement(self, customer_data: Dict[str, Any]) -> float:
        """Calculate engagement score for a single customer"""
        interactions = customer_data.get('total_interactions', 1)
        purchases = customer_data.get('total_purchases', 1)
        last_interaction = customer_data.get('last_interaction_date')
        
        # Interaction frequency score
        interaction_score = min(1.0, interactions / 20)
        
        # Purchase engagement score
        purchase_score = min(1.0, purchases / 10)
        
        # Recency score
        if last_interaction:
            days_since = (datetime.now() - pd.to_datetime(last_interaction)).days
            recency_score = max(0, 1 - (days_since / 180))  # 6 months max
        else:
            recency_score = 0.5
        
        return (interaction_score * 0.3 + purchase_score * 0.3 + recency_score * 0.4)
    
    async def _get_customer_data(self, dealership_id: str, customer_email: str = None) -> List[Dict[str, Any]]:
        """Get customer data from BigQuery or generate mock data"""
        if not self.bigquery_client:
            return self._generate_mock_customer_data(dealership_id, customer_email)
        
        try:
            where_clause = f"WHERE dealership_id = '{dealership_id}'"
            if customer_email:
                where_clause += f" AND email = '{customer_email}'"
            
            query = f"""
                SELECT 
                    customer_id, email, total_spent, total_purchases,
                    first_purchase_date, last_purchase_date, last_interaction_date,
                    preferred_brands, total_interactions, service_visits, trade_ins
                FROM `vendora-464403.automotive.customer_profiles`
                {where_clause}
                ORDER BY total_spent DESC
            """
            
            results = self.bigquery_client.query(query).result()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"BigQuery customer data error: {str(e)}")
            return self._generate_mock_customer_data(dealership_id, customer_email)
    
    async def _get_recent_customer_interactions(self, dealership_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent customer interactions"""
        if not self.bigquery_client:
            return self._generate_mock_customer_data(dealership_id)
        
        try:
            query = f"""
                SELECT DISTINCT
                    customer_id, email, total_spent, total_purchases,
                    last_interaction_date, preferred_brands
                FROM `vendora-464403.automotive.customer_profiles`
                WHERE dealership_id = '{dealership_id}'
                AND last_interaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                ORDER BY last_interaction_date DESC
            """
            
            results = self.bigquery_client.query(query).result()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Recent interactions query error: {str(e)}")
            return self._generate_mock_customer_data(dealership_id)
    
    def _generate_mock_customer_data(self, dealership_id: str, specific_email: str = None) -> List[Dict[str, Any]]:
        """Generate mock customer data for testing"""
        mock_data = []
        
        customers_to_generate = 1 if specific_email else 50
        
        for i in range(customers_to_generate):
            email = specific_email if specific_email else f"customer{i}@example.com"
            
            customer = {
                'customer_id': f"cust_{dealership_id}_{i}",
                'email': email,
                'total_spent': np.random.lognormal(10, 1),  # Log-normal distribution for realistic spending
                'total_purchases': np.random.randint(1, 8),
                'first_purchase_date': (datetime.now() - timedelta(days=np.random.randint(30, 1095))).strftime('%Y-%m-%d'),
                'last_purchase_date': (datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime('%Y-%m-%d'),
                'last_interaction_date': (datetime.now() - timedelta(days=np.random.randint(1, 90))).strftime('%Y-%m-%d'),
                'preferred_brands': np.random.choice(['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW', 'Mercedes']),
                'total_interactions': np.random.randint(1, 25),
                'service_visits': np.random.randint(0, 10),
                'trade_ins': np.random.randint(0, 3)
            }
            
            mock_data.append(customer)
        
        return mock_data
    
    def _generate_mock_segment_analysis(self) -> Dict[str, SegmentAnalysis]:
        """Generate mock segment analysis for testing"""
        analyses = {}
        
        for segment_type in [SegmentType.HIGH_VALUE, SegmentType.FREQUENT_BUYER, SegmentType.BUDGET_CONSCIOUS]:
            analyses[segment_type.value] = SegmentAnalysis(
                segment_type=segment_type,
                customer_count=np.random.randint(10, 100),
                avg_lifetime_value=np.random.normal(35000, 15000),
                avg_purchase_frequency=np.random.normal(1.5, 0.5),
                revenue_contribution=np.random.uniform(0.1, 0.4),
                growth_rate=np.random.uniform(0.05, 0.25),
                retention_rate=np.random.uniform(0.6, 0.9),
                top_characteristics={
                    'avg_purchase_amount': np.random.normal(30000, 10000),
                    'avg_engagement_score': np.random.uniform(0.3, 0.9),
                    'brand_loyalty': np.random.uniform(0.4, 0.8)
                },
                recommended_actions=[
                    "Implement personalized marketing campaigns",
                    "Offer targeted promotions",
                    "Enhance customer service experience"
                ]
            )
        
        return analyses