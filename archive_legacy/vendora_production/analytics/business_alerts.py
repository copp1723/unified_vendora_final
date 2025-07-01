"""
Business Alerts System for VENDORA Platform
Automated monitoring and alerting for automotive business metrics
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import json
import asyncio

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    CRITICAL = "critical"      # Immediate action required
    HIGH = "high"             # Action needed within hours
    MEDIUM = "medium"         # Action needed within days
    LOW = "low"              # Information only
    INFO = "info"            # General information


class AlertType(Enum):
    SALES_DECLINE = "sales_decline"
    REVENUE_DROP = "revenue_drop"
    INVENTORY_SHORTAGE = "inventory_shortage"
    INVENTORY_EXCESS = "inventory_excess"
    CUSTOMER_CHURN = "customer_churn"
    ANOMALY_DETECTION = "anomaly_detection"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    SEASONAL_DEVIATION = "seasonal_deviation"
    FORECAST_ACCURACY = "forecast_accuracy"
    CUSTOMER_SATISFACTION = "customer_satisfaction"


class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Configuration for an alert rule"""
    rule_id: str
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    condition: str  # Description of the condition
    threshold_value: float
    comparison_operator: str  # "gt", "lt", "eq", "gte", "lte"
    evaluation_period: int  # Days to look back
    enabled: bool = True
    suppression_duration: int = 24  # Hours to suppress similar alerts
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["email", "dashboard"]


@dataclass
class BusinessAlert:
    """Business alert instance"""
    alert_id: str
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    dealership_id: str
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
            "dealership_id": self.dealership_id,
            "status": self.status.value,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata
        }


@dataclass
class AlertSummary:
    """Summary of alerts for a time period"""
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    active_alerts: int
    resolved_alerts: int
    top_alert_types: List[Dict[str, Any]]
    recent_alerts: List[BusinessAlert]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_alerts": self.total_alerts,
            "critical_alerts": self.critical_alerts,
            "high_alerts": self.high_alerts,
            "medium_alerts": self.medium_alerts,
            "low_alerts": self.low_alerts,
            "active_alerts": self.active_alerts,
            "resolved_alerts": self.resolved_alerts,
            "top_alert_types": self.top_alert_types,
            "recent_alerts": [alert.to_dict() for alert in self.recent_alerts]
        }


class BusinessAlertsEngine:
    """Automated business alerts and monitoring system"""
    
    def __init__(self, bigquery_client=None):
        self.bigquery_client = bigquery_client
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, BusinessAlert] = {}
        self.alert_history: List[BusinessAlert] = []
        self.suppressed_alerts: Dict[str, datetime] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules for automotive dealerships"""
        default_rules = [
            AlertRule(
                rule_id="sales_decline_critical",
                name="Critical Sales Decline",
                alert_type=AlertType.SALES_DECLINE,
                severity=AlertSeverity.CRITICAL,
                condition="Daily sales dropped by 50% or more compared to 30-day average",
                threshold_value=-0.5,  # 50% decline
                comparison_operator="lte",
                evaluation_period=1,
                notification_channels=["email", "sms", "dashboard"]
            ),
            AlertRule(
                rule_id="revenue_drop_high",
                name="Significant Revenue Drop",
                alert_type=AlertType.REVENUE_DROP,
                severity=AlertSeverity.HIGH,
                condition="Daily revenue dropped by 30% or more compared to weekly average",
                threshold_value=-0.3,  # 30% decline
                comparison_operator="lte",
                evaluation_period=7
            ),
            AlertRule(
                rule_id="inventory_shortage",
                name="Low Inventory Alert",
                alert_type=AlertType.INVENTORY_SHORTAGE,
                severity=AlertSeverity.MEDIUM,
                condition="Inventory levels below 30 days of average sales",
                threshold_value=30,  # days
                comparison_operator="lt",
                evaluation_period=7
            ),
            AlertRule(
                rule_id="inventory_excess",
                name="Excess Inventory Alert",
                alert_type=AlertType.INVENTORY_EXCESS,
                severity=AlertSeverity.MEDIUM,
                condition="Inventory levels above 120 days of average sales",
                threshold_value=120,  # days
                comparison_operator="gt",
                evaluation_period=30
            ),
            AlertRule(
                rule_id="customer_churn_warning",
                name="Customer Churn Risk",
                alert_type=AlertType.CUSTOMER_CHURN,
                severity=AlertSeverity.HIGH,
                condition="Customer churn rate above 25%",
                threshold_value=0.25,  # 25%
                comparison_operator="gt",
                evaluation_period=30
            ),
            AlertRule(
                rule_id="performance_threshold",
                name="Performance Below Target",
                alert_type=AlertType.PERFORMANCE_THRESHOLD,
                severity=AlertSeverity.MEDIUM,
                condition="Sales performance below 80% of monthly target",
                threshold_value=0.8,  # 80%
                comparison_operator="lt",
                evaluation_period=30
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    async def evaluate_all_alerts(self, dealership_id: str) -> List[BusinessAlert]:
        """Evaluate all alert rules for a dealership"""
        new_alerts = []
        
        try:
            # Get current business metrics
            metrics = await self._get_business_metrics(dealership_id)
            
            # Evaluate each active rule
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                alert = await self._evaluate_rule(rule, dealership_id, metrics)
                if alert:
                    # Check if alert should be suppressed
                    if not self._is_alert_suppressed(alert):
                        new_alerts.append(alert)
                        self.active_alerts[alert.alert_id] = alert
                        self.alert_history.append(alert)
                        
                        # Send notifications
                        await self._send_alert_notifications(alert)
            
            return new_alerts
            
        except Exception as e:
            logger.error(f"Alert evaluation failed for dealership {dealership_id}: {str(e)}")
            return []
    
    async def _evaluate_rule(self, rule: AlertRule, dealership_id: str, 
                           metrics: Dict[str, Any]) -> Optional[BusinessAlert]:
        """Evaluate a specific alert rule"""
        try:
            # Get the relevant metric value
            current_value = await self._get_metric_value(rule, dealership_id, metrics)
            
            if current_value is None:
                return None
            
            # Compare with threshold
            threshold_met = self._check_threshold(current_value, rule.threshold_value, rule.comparison_operator)
            
            if threshold_met:
                # Create alert
                alert_id = f"{rule.rule_id}_{dealership_id}_{int(datetime.now().timestamp())}"
                
                alert = BusinessAlert(
                    alert_id=alert_id,
                    rule_id=rule.rule_id,
                    alert_type=rule.alert_type,
                    severity=rule.severity,
                    title=rule.name,
                    message=self._generate_alert_message(rule, current_value),
                    metric_name=self._get_metric_name_for_rule(rule),
                    current_value=current_value,
                    threshold_value=rule.threshold_value,
                    timestamp=datetime.now(),
                    dealership_id=dealership_id,
                    metadata=self._generate_alert_metadata(rule, current_value, metrics)
                )
                
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Rule evaluation failed for {rule.rule_id}: {str(e)}")
            return None
    
    async def _get_metric_value(self, rule: AlertRule, dealership_id: str, 
                              metrics: Dict[str, Any]) -> Optional[float]:
        """Get the current value for a metric based on the alert rule"""
        try:
            if rule.alert_type == AlertType.SALES_DECLINE:
                return await self._calculate_sales_change_percentage(dealership_id, rule.evaluation_period)
            
            elif rule.alert_type == AlertType.REVENUE_DROP:
                return await self._calculate_revenue_change_percentage(dealership_id, rule.evaluation_period)
            
            elif rule.alert_type == AlertType.INVENTORY_SHORTAGE or rule.alert_type == AlertType.INVENTORY_EXCESS:
                return await self._calculate_inventory_days_supply(dealership_id)
            
            elif rule.alert_type == AlertType.CUSTOMER_CHURN:
                return await self._calculate_churn_rate(dealership_id, rule.evaluation_period)
            
            elif rule.alert_type == AlertType.PERFORMANCE_THRESHOLD:
                return await self._calculate_performance_ratio(dealership_id, rule.evaluation_period)
            
            elif rule.alert_type == AlertType.ANOMALY_DETECTION:
                return await self._detect_anomaly_score(dealership_id, rule.evaluation_period)
            
            else:
                # Generic metric lookup
                metric_name = self._get_metric_name_for_rule(rule)
                return metrics.get(metric_name, 0.0)
            
        except Exception as e:
            logger.error(f"Metric value calculation failed for {rule.alert_type}: {str(e)}")
            return None
    
    def _check_threshold(self, current_value: float, threshold: float, operator: str) -> bool:
        """Check if current value meets threshold condition"""
        if operator == "gt":
            return current_value > threshold
        elif operator == "gte":
            return current_value >= threshold
        elif operator == "lt":
            return current_value < threshold
        elif operator == "lte":
            return current_value <= threshold
        elif operator == "eq":
            return abs(current_value - threshold) < 0.001  # Float comparison
        else:
            logger.warning(f"Unknown comparison operator: {operator}")
            return False
    
    def _generate_alert_message(self, rule: AlertRule, current_value: float) -> str:
        """Generate a descriptive alert message"""
        if rule.alert_type == AlertType.SALES_DECLINE:
            percentage = abs(current_value * 100)
            return f"Sales have declined by {percentage:.1f}% compared to the recent average. Immediate attention required."
        
        elif rule.alert_type == AlertType.REVENUE_DROP:
            percentage = abs(current_value * 100)
            return f"Revenue has dropped by {percentage:.1f}% below expected levels. Review pricing and promotion strategies."
        
        elif rule.alert_type == AlertType.INVENTORY_SHORTAGE:
            return f"Current inventory will last only {current_value:.0f} days at current sales rate. Consider restocking."
        
        elif rule.alert_type == AlertType.INVENTORY_EXCESS:
            return f"Current inventory will last {current_value:.0f} days at current sales rate. Consider promotional activities."
        
        elif rule.alert_type == AlertType.CUSTOMER_CHURN:
            percentage = current_value * 100
            return f"Customer churn rate is {percentage:.1f}%, above acceptable levels. Review customer retention strategies."
        
        elif rule.alert_type == AlertType.PERFORMANCE_THRESHOLD:
            percentage = current_value * 100
            return f"Sales performance is at {percentage:.1f}% of target. Action needed to meet monthly goals."
        
        else:
            return f"{rule.condition}. Current value: {current_value:.2f}, Threshold: {rule.threshold_value:.2f}"
    
    def _get_metric_name_for_rule(self, rule: AlertRule) -> str:
        """Get the metric name associated with an alert rule"""
        metric_mapping = {
            AlertType.SALES_DECLINE: "sales_change_percentage",
            AlertType.REVENUE_DROP: "revenue_change_percentage",
            AlertType.INVENTORY_SHORTAGE: "inventory_days_supply",
            AlertType.INVENTORY_EXCESS: "inventory_days_supply",
            AlertType.CUSTOMER_CHURN: "churn_rate",
            AlertType.PERFORMANCE_THRESHOLD: "performance_ratio",
            AlertType.ANOMALY_DETECTION: "anomaly_score"
        }
        
        return metric_mapping.get(rule.alert_type, "unknown_metric")
    
    def _generate_alert_metadata(self, rule: AlertRule, current_value: float, 
                                metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for the alert"""
        return {
            "rule_condition": rule.condition,
            "evaluation_period_days": rule.evaluation_period,
            "comparison_operator": rule.comparison_operator,
            "related_metrics": {
                key: value for key, value in metrics.items()
                if key.startswith(rule.alert_type.value.split('_')[0])
            },
            "timestamp_generated": datetime.now().isoformat()
        }
    
    def _is_alert_suppressed(self, alert: BusinessAlert) -> bool:
        """Check if an alert should be suppressed due to recent similar alerts"""
        suppression_key = f"{alert.rule_id}_{alert.dealership_id}"
        
        if suppression_key in self.suppressed_alerts:
            last_alert_time = self.suppressed_alerts[suppression_key]
            rule = self.alert_rules.get(alert.rule_id)
            
            if rule and rule.suppression_duration > 0:
                time_since_last = datetime.now() - last_alert_time
                if time_since_last.total_seconds() < rule.suppression_duration * 3600:
                    return True
        
        # Update suppression tracking
        self.suppressed_alerts[suppression_key] = datetime.now()
        return False
    
    async def _send_alert_notifications(self, alert: BusinessAlert):
        """Send alert notifications through configured channels"""
        rule = self.alert_rules.get(alert.rule_id)
        if not rule:
            return
        
        for channel in rule.notification_channels:
            try:
                if channel in self.notification_handlers:
                    await self.notification_handlers[channel](alert)
                else:
                    # Log notification (default behavior)
                    logger.warning(f"Alert notification [{channel}]: {alert.title} - {alert.message}")
            
            except Exception as e:
                logger.error(f"Failed to send {channel} notification for alert {alert.alert_id}: {str(e)}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            return True
        return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.metadata["resolved_by"] = resolved_by
            return True
        return False
    
    async def get_alert_summary(self, dealership_id: str, days: int = 7) -> AlertSummary:
        """Get alert summary for a dealership"""
        try:
            # Filter alerts for the dealership and time period
            cutoff_date = datetime.now() - timedelta(days=days)
            relevant_alerts = [
                alert for alert in self.alert_history
                if alert.dealership_id == dealership_id and alert.timestamp >= cutoff_date
            ]
            
            # Count by severity
            severity_counts = {severity: 0 for severity in AlertSeverity}
            for alert in relevant_alerts:
                severity_counts[alert.severity] += 1
            
            # Count by status
            active_count = len([a for a in relevant_alerts if a.status == AlertStatus.ACTIVE])
            resolved_count = len([a for a in relevant_alerts if a.status == AlertStatus.RESOLVED])
            
            # Top alert types
            alert_type_counts = {}
            for alert in relevant_alerts:
                alert_type_counts[alert.alert_type.value] = alert_type_counts.get(alert.alert_type.value, 0) + 1
            
            top_alert_types = [
                {"alert_type": alert_type, "count": count}
                for alert_type, count in sorted(alert_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
            
            # Recent alerts (last 5)
            recent_alerts = sorted(relevant_alerts, key=lambda x: x.timestamp, reverse=True)[:5]
            
            return AlertSummary(
                total_alerts=len(relevant_alerts),
                critical_alerts=severity_counts[AlertSeverity.CRITICAL],
                high_alerts=severity_counts[AlertSeverity.HIGH],
                medium_alerts=severity_counts[AlertSeverity.MEDIUM],
                low_alerts=severity_counts[AlertSeverity.LOW],
                active_alerts=active_count,
                resolved_alerts=resolved_count,
                top_alert_types=top_alert_types,
                recent_alerts=recent_alerts
            )
            
        except Exception as e:
            logger.error(f"Alert summary generation failed: {str(e)}")
            return self._generate_empty_alert_summary()
    
    async def _calculate_sales_change_percentage(self, dealership_id: str, evaluation_period: int) -> float:
        """Calculate percentage change in sales"""
        try:
            # Get recent sales data
            recent_sales = await self._get_recent_sales_count(dealership_id, evaluation_period)
            baseline_sales = await self._get_baseline_sales_count(dealership_id, evaluation_period)
            
            if baseline_sales == 0:
                return 0.0
            
            return (recent_sales - baseline_sales) / baseline_sales
            
        except Exception as e:
            logger.error(f"Sales change calculation failed: {str(e)}")
            return 0.0
    
    async def _calculate_revenue_change_percentage(self, dealership_id: str, evaluation_period: int) -> float:
        """Calculate percentage change in revenue"""
        try:
            recent_revenue = await self._get_recent_revenue(dealership_id, evaluation_period)
            baseline_revenue = await self._get_baseline_revenue(dealership_id, evaluation_period)
            
            if baseline_revenue == 0:
                return 0.0
            
            return (recent_revenue - baseline_revenue) / baseline_revenue
            
        except Exception as e:
            logger.error(f"Revenue change calculation failed: {str(e)}")
            return 0.0
    
    async def _calculate_inventory_days_supply(self, dealership_id: str) -> float:
        """Calculate days of inventory supply at current sales rate"""
        try:
            current_inventory = await self._get_current_inventory_count(dealership_id)
            daily_sales_rate = await self._get_daily_sales_rate(dealership_id, 30)
            
            if daily_sales_rate == 0:
                return 365  # If no sales, inventory will last a year (default)
            
            return current_inventory / daily_sales_rate
            
        except Exception as e:
            logger.error(f"Inventory days supply calculation failed: {str(e)}")
            return 60  # Default assumption
    
    async def _calculate_churn_rate(self, dealership_id: str, evaluation_period: int) -> float:
        """Calculate customer churn rate"""
        try:
            # This is a simplified churn calculation
            # In practice, this would involve more sophisticated customer lifecycle analysis
            
            customers_at_start = await self._get_customer_count_at_period_start(dealership_id, evaluation_period)
            customers_lost = await self._get_lost_customers_count(dealership_id, evaluation_period)
            
            if customers_at_start == 0:
                return 0.0
            
            return customers_lost / customers_at_start
            
        except Exception as e:
            logger.error(f"Churn rate calculation failed: {str(e)}")
            return 0.1  # Default 10% churn
    
    async def _calculate_performance_ratio(self, dealership_id: str, evaluation_period: int) -> float:
        """Calculate performance ratio against target"""
        try:
            actual_sales = await self._get_recent_sales_count(dealership_id, evaluation_period)
            target_sales = await self._get_sales_target(dealership_id, evaluation_period)
            
            if target_sales == 0:
                return 1.0  # No target set
            
            return actual_sales / target_sales
            
        except Exception as e:
            logger.error(f"Performance ratio calculation failed: {str(e)}")
            return 0.8  # Default 80% performance
    
    async def _detect_anomaly_score(self, dealership_id: str, evaluation_period: int) -> float:
        """Detect anomalies in business metrics"""
        try:
            # Simplified anomaly detection based on sales variance
            recent_sales = await self._get_daily_sales_for_period(dealership_id, evaluation_period)
            
            if len(recent_sales) < 3:
                return 0.0
            
            mean_sales = np.mean(recent_sales)
            std_sales = np.std(recent_sales)
            
            if std_sales == 0:
                return 0.0
            
            # Z-score of the most recent day
            latest_sales = recent_sales[-1]
            z_score = abs((latest_sales - mean_sales) / std_sales)
            
            # Convert to 0-1 anomaly score
            return min(1.0, z_score / 3.0)  # 3 standard deviations = 1.0 score
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return 0.0
    
    async def _get_business_metrics(self, dealership_id: str) -> Dict[str, Any]:
        """Get current business metrics for evaluation"""
        # This would typically fetch from BigQuery or other data sources
        # For now, return mock data structure
        return {
            "daily_sales": 2.5,
            "daily_revenue": 75000,
            "inventory_count": 150,
            "customer_count": 500,
            "last_updated": datetime.now().isoformat()
        }
    
    # Mock data methods (replace with actual BigQuery implementations)
    async def _get_recent_sales_count(self, dealership_id: str, days: int) -> int:
        """Get recent sales count"""
        return np.random.poisson(2.0 * days)  # Mock: 2 sales per day average
    
    async def _get_baseline_sales_count(self, dealership_id: str, days: int) -> int:
        """Get baseline sales count for comparison"""
        return np.random.poisson(2.5 * days)  # Mock: slightly higher baseline
    
    async def _get_recent_revenue(self, dealership_id: str, days: int) -> float:
        """Get recent revenue"""
        return np.random.normal(60000 * days, 10000)  # Mock revenue
    
    async def _get_baseline_revenue(self, dealership_id: str, days: int) -> float:
        """Get baseline revenue for comparison"""
        return np.random.normal(65000 * days, 8000)  # Mock baseline revenue
    
    async def _get_current_inventory_count(self, dealership_id: str) -> int:
        """Get current inventory count"""
        return np.random.randint(100, 200)  # Mock inventory
    
    async def _get_daily_sales_rate(self, dealership_id: str, days: int) -> float:
        """Get daily sales rate"""
        total_sales = await self._get_recent_sales_count(dealership_id, days)
        return total_sales / days
    
    async def _get_customer_count_at_period_start(self, dealership_id: str, days: int) -> int:
        """Get customer count at start of period"""
        return np.random.randint(400, 600)  # Mock customer count
    
    async def _get_lost_customers_count(self, dealership_id: str, days: int) -> int:
        """Get count of lost customers"""
        return np.random.randint(5, 25)  # Mock churn
    
    async def _get_sales_target(self, dealership_id: str, days: int) -> int:
        """Get sales target for period"""
        return int(2.8 * days)  # Mock target: 2.8 sales per day
    
    async def _get_daily_sales_for_period(self, dealership_id: str, days: int) -> List[float]:
        """Get daily sales data for anomaly detection"""
        return [np.random.poisson(2.5) for _ in range(days)]  # Mock daily sales
    
    def _generate_empty_alert_summary(self) -> AlertSummary:
        """Generate empty alert summary for error cases"""
        return AlertSummary(
            total_alerts=0,
            critical_alerts=0,
            high_alerts=0,
            medium_alerts=0,
            low_alerts=0,
            active_alerts=0,
            resolved_alerts=0,
            top_alert_types=[],
            recent_alerts=[]
        )
    
    def add_custom_rule(self, rule: AlertRule):
        """Add a custom alert rule"""
        self.alert_rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule"""
        if rule_id in self.alert_rules:
            self.alert_rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule"""
        if rule_id in self.alert_rules:
            self.alert_rules[rule_id].enabled = False
            return True
        return False
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """Register a notification handler for a specific channel"""
        self.notification_handlers[channel] = handler
    
    async def test_alert_system(self, dealership_id: str) -> Dict[str, Any]:
        """Test the alert system with mock conditions"""
        test_results = {
            "system_status": "operational",
            "rules_evaluated": len(self.alert_rules),
            "test_alerts_generated": 0,
            "notification_channels_tested": list(self.notification_handlers.keys()),
            "test_timestamp": datetime.now().isoformat()
        }
        
        # Generate a test alert
        test_alert = BusinessAlert(
            alert_id=f"test_{dealership_id}_{int(datetime.now().timestamp())}",
            rule_id="test_rule",
            alert_type=AlertType.PERFORMANCE_THRESHOLD,
            severity=AlertSeverity.LOW,
            title="Alert System Test",
            message="This is a test alert to verify the alert system is functioning correctly.",
            metric_name="test_metric",
            current_value=0.5,
            threshold_value=0.8,
            timestamp=datetime.now(),
            dealership_id=dealership_id,
            metadata={"test": True}
        )
        
        # Send test notifications
        await self._send_alert_notifications(test_alert)
        test_results["test_alerts_generated"] = 1
        
        return test_results


# Convenience functions for creating common alert rules
def create_sales_decline_rule(threshold_percentage: float = 0.3, 
                            severity: AlertSeverity = AlertSeverity.HIGH) -> AlertRule:
    """Create a sales decline alert rule"""
    return AlertRule(
        rule_id=f"sales_decline_{int(threshold_percentage * 100)}",
        name=f"Sales Decline {int(threshold_percentage * 100)}%",
        alert_type=AlertType.SALES_DECLINE,
        severity=severity,
        condition=f"Sales declined by {int(threshold_percentage * 100)}% or more",
        threshold_value=-threshold_percentage,
        comparison_operator="lte",
        evaluation_period=7
    )


def create_inventory_shortage_rule(days_supply: int = 30, 
                                 severity: AlertSeverity = AlertSeverity.MEDIUM) -> AlertRule:
    """Create an inventory shortage alert rule"""
    return AlertRule(
        rule_id=f"inventory_shortage_{days_supply}d",
        name=f"Inventory Below {days_supply} Days",
        alert_type=AlertType.INVENTORY_SHORTAGE,
        severity=severity,
        condition=f"Inventory below {days_supply} days of supply",
        threshold_value=days_supply,
        comparison_operator="lt",
        evaluation_period=7
    )


def create_customer_churn_rule(churn_threshold: float = 0.25, 
                             severity: AlertSeverity = AlertSeverity.HIGH) -> AlertRule:
    """Create a customer churn alert rule"""
    return AlertRule(
        rule_id=f"churn_{int(churn_threshold * 100)}",
        name=f"Customer Churn {int(churn_threshold * 100)}%",
        alert_type=AlertType.CUSTOMER_CHURN,
        severity=severity,
        condition=f"Customer churn rate above {int(churn_threshold * 100)}%",
        threshold_value=churn_threshold,
        comparison_operator="gt",
        evaluation_period=30
    )