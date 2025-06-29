"""
Enhanced Data Processor for VENDORA automotive data platform.
Handles real automotive datasets with improved column mapping and insights.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAutomotiveDataProcessor:
    """Enhanced processor for real automotive dealership data."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_storage_path = config.get('DATA_STORAGE_PATH', '/tmp/vendora_data')
        
        # Enhanced column mapping for real automotive data
        self.column_mappings = {
            # Sales data columns
            'lead_source': ['lead_source', 'leadsource', 'source', 'Lead Source', 'Lead Source Group'],
            'listing_price': ['listing_price', 'listprice', 'list_price', 'asking_price'],
            'sold_price': ['sold_price', 'saleprice', 'sale_price', 'final_price', 'selling_price'],
            'profit': ['profit', 'gross_profit', 'total_gross', 'gross', 'front_gross', 'Total Front Gross'],
            'expense': ['expense', 'cost', 'expenses', 'total_cost'],
            'sales_rep_name': ['sales_rep_name', 'salesperson', 'rep_name', 'sales_rep', 'User'],
            'vehicle_year': ['vehicle_year', 'year', 'model_year'],
            'vehicle_make': ['vehicle_make', 'make', 'manufacturer'],
            'vehicle_model': ['vehicle_model', 'model'],
            'days_to_close': ['days_to_close', 'days_to_sale', 'sale_days', 'Avg Days to Sale'],
            
            # Performance metrics
            'total_leads': ['Total Leads', 'total_leads', 'leads'],
            'good_leads': ['Good Leads', 'good_leads', 'qualified_leads'],
            'sold_count': ['Total Sold', 'sold_count', 'units_sold', 'sales_count'],
            'conversion_rate': ['Sold from Leads %', 'conversion_rate', 'close_rate'],
            'avg_gross': ['Avg Gross', 'average_gross', 'avg_profit'],
            'total_gross': ['Total Gross', 'total_gross_profit', 'total_profit'],
            
            # Lead performance
            'contact_rate': ['Internet Actual Contact %', 'contact_rate', 'contacted %'],
            'appt_set_rate': ['Appts Set %', 'appointment_rate', 'appt_rate'],
            'appt_shown_rate': ['Appts Shown %', 'show_rate', 'appointment_show_rate'],
            'response_time': ['Response Time - Adjusted (Mins)', 'response_time', 'avg_response_time'],
            
            # Financial metrics
            'cost_per_lead': ['Cost Per Good Lead', 'cost_per_lead', 'lead_cost'],
            'cost_per_sold': ['Cost Per Sold', 'cost_per_sale', 'acquisition_cost'],
            'roi': ['Profit', 'roi', 'return_on_investment'],
        }
        
        # Ensure processed data directory exists
        os.makedirs(f"{self.data_storage_path}/processed", exist_ok=True)
    
    def detect_dataset_type(self, df: pd.DataFrame) -> str:
        """Detect the type of automotive dataset based on columns."""
        columns_lower = [col.lower() for col in df.columns]
        
        if any('leaderboard' in col.lower() or 'rank' in col.lower() for col in df.columns):
            return 'leaderboard'
        elif any('lead source' in col.lower() for col in df.columns):
            return 'lead_source_roi'
        elif 'lead_source' in columns_lower and 'sold_price' in columns_lower:
            return 'sales_transactions'
        elif any('profit' in col.lower() and 'expense' in col.lower() for col in df.columns):
            return 'sales_performance'
        else:
            return 'general_automotive'
    
    def normalize_column_name(self, column: str) -> str:
        """Normalize a column name to standard format."""
        # Clean the column name
        clean_col = str(column).strip().replace('﻿', '')  # Remove BOM
        
        # Check against our mappings
        for standard_name, aliases in self.column_mappings.items():
            if clean_col in aliases or clean_col.lower() in [alias.lower() for alias in aliases]:
                return standard_name
        
        # If no mapping found, return cleaned version
        return clean_col.lower().replace(' ', '_').replace('%', '_pct').replace('(', '').replace(')', '')
    
    def load_csv_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load and validate CSV file with enhanced error handling."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Successfully loaded CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                logger.error(f"Could not read CSV file with any encoding: {file_path}")
                return None
            
            logger.info(f"Loaded CSV file: {file_path} with {len(df)} rows and {len(df.columns)} columns")
            
            # Basic validation
            if df.empty:
                logger.warning(f"CSV file is empty: {file_path}")
                return None
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return None
    
    def normalize_automotive_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced normalization for real automotive data."""
        try:
            # Detect dataset type
            dataset_type = self.detect_dataset_type(df)
            logger.info(f"Detected dataset type: {dataset_type}")
            
            # Normalize column names
            column_mapping = {}
            for col in df.columns:
                normalized = self.normalize_column_name(col)
                if normalized != col:
                    column_mapping[col] = normalized
            
            if column_mapping:
                df = df.rename(columns=column_mapping)
                logger.info(f"Normalized columns: {column_mapping}")
            
            # Clean and convert data based on dataset type
            df = self._clean_data_by_type(df, dataset_type)
            
            return df
            
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            return df
    
    def _clean_data_by_type(self, df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
        """Clean data based on detected dataset type."""
        try:
            # Clean currency and percentage columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Handle currency values
                    if any(df[col].astype(str).str.contains(r'\$', na=False)):
                        df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        logger.info(f"Converted currency column: {col}")
                    
                    # Handle percentage values
                    elif any(df[col].astype(str).str.contains(r'%', na=False)):
                        df[col] = df[col].astype(str).str.replace('%', '').str.replace(' ', '')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        logger.info(f"Converted percentage column: {col}")
                    
                    # Handle numeric values in parentheses (rankings)
                    elif any(df[col].astype(str).str.contains(r'\(\d+\)', na=False)):
                        # Extract numbers from parentheses for rankings
                        df[col + '_rank'] = df[col].astype(str).str.extract(r'\((\d+)\)').astype(float)
                        # Extract the main value
                        df[col] = df[col].astype(str).str.replace(r'\(\d+\)\s*', '', regex=True)
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert date columns if present
            date_columns = [col for col in df.columns if 'date' in col.lower()]
            for col in date_columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    logger.info(f"Converted date column: {col}")
                except:
                    logger.warning(f"Could not convert date column: {col}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return df
    
    def calculate_automotive_metrics(self, df: pd.DataFrame, dataset_type: str) -> Dict[str, Any]:
        """Calculate metrics based on dataset type."""
        metrics = {'dataset_type': dataset_type}
        
        try:
            if dataset_type == 'sales_transactions':
                metrics.update(self._calculate_sales_metrics(df))
            elif dataset_type == 'leaderboard':
                metrics.update(self._calculate_leaderboard_metrics(df))
            elif dataset_type == 'lead_source_roi':
                metrics.update(self._calculate_lead_source_metrics(df))
            else:
                metrics.update(self._calculate_general_metrics(df))
            
            logger.info(f"Calculated metrics for {dataset_type}: {list(metrics.keys())}")
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
        
        return metrics
    
    def _calculate_sales_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate metrics for sales transaction data."""
        metrics = {}
        
        # Basic sales metrics
        if 'sold_price' in df.columns:
            metrics['total_revenue'] = float(df['sold_price'].sum())
            metrics['average_sale_price'] = float(df['sold_price'].mean())
            metrics['total_units_sold'] = len(df)
        
        # Profit metrics
        if 'profit' in df.columns:
            metrics['total_profit'] = float(df['profit'].sum())
            metrics['average_profit'] = float(df['profit'].mean())
            
            if 'sold_price' in df.columns:
                df['profit_margin'] = (df['profit'] / df['sold_price']) * 100
                metrics['average_profit_margin'] = float(df['profit_margin'].mean())
        
        # Lead source analysis
        if 'lead_source' in df.columns:
            lead_stats = df.groupby('lead_source').agg({
                'sold_price': ['count', 'mean', 'sum'],
                'profit': ['mean', 'sum'] if 'profit' in df.columns else ['count']
            }).round(2)
            
            # Convert to simple dictionary structure
            lead_performance = {}
            for source in lead_stats.index:
                lead_performance[source] = {
                    'count': int(lead_stats.loc[source, ('sold_price', 'count')]),
                    'avg_price': float(lead_stats.loc[source, ('sold_price', 'mean')]),
                    'total_revenue': float(lead_stats.loc[source, ('sold_price', 'sum')])
                }
                if 'profit' in df.columns:
                    lead_performance[source]['avg_profit'] = float(lead_stats.loc[source, ('profit', 'mean')])
                    lead_performance[source]['total_profit'] = float(lead_stats.loc[source, ('profit', 'sum')])
            
            metrics['lead_source_performance'] = lead_performance
            
            # Best performing lead source
            if 'profit' in df.columns:
                best_source = df.groupby('lead_source')['profit'].mean().idxmax()
                metrics['best_lead_source'] = {
                    'source': best_source,
                    'avg_profit': float(df[df['lead_source'] == best_source]['profit'].mean())
                }
        
        # Sales rep performance
        if 'sales_rep_name' in df.columns:
            rep_stats = df.groupby('sales_rep_name').agg({
                'sold_price': ['count', 'mean', 'sum'],
                'profit': ['mean', 'sum'] if 'profit' in df.columns else ['count']
            }).round(2)
            
            # Convert to simple dictionary structure
            rep_performance = {}
            for rep in rep_stats.index:
                rep_performance[rep] = {
                    'count': int(rep_stats.loc[rep, ('sold_price', 'count')]),
                    'avg_price': float(rep_stats.loc[rep, ('sold_price', 'mean')]),
                    'total_revenue': float(rep_stats.loc[rep, ('sold_price', 'sum')])
                }
                if 'profit' in df.columns:
                    rep_performance[rep]['avg_profit'] = float(rep_stats.loc[rep, ('profit', 'mean')])
                    rep_performance[rep]['total_profit'] = float(rep_stats.loc[rep, ('profit', 'sum')])
            
            metrics['sales_rep_performance'] = rep_performance
            
            # Top performer
            if 'profit' in df.columns:
                top_rep = df.groupby('sales_rep_name')['profit'].sum().idxmax()
                metrics['top_sales_rep'] = {
                    'name': top_rep,
                    'total_profit': float(df[df['sales_rep_name'] == top_rep]['profit'].sum())
                }
        
        return metrics
    
    def _calculate_leaderboard_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate metrics for leaderboard data."""
        metrics = {}
        
        # Overall rankings
        if 'overall_rank' in df.columns:
            metrics['total_reps'] = len(df)
            metrics['top_performer'] = df[df['overall_rank'] == 1]['user'].iloc[0] if len(df) > 0 else None
        
        # Performance metrics
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if 'pct' in col or 'rate' in col:
                metrics[f'avg_{col}'] = float(df[col].mean())
                metrics[f'top_{col}'] = float(df[col].max())
        
        return metrics
    
    def _calculate_lead_source_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate metrics for lead source ROI data."""
        metrics = {}
        
        if 'total_leads' in df.columns:
            metrics['total_leads_all_sources'] = int(df['total_leads'].sum())
        
        if 'sold_from_leads_pct' in df.columns:
            metrics['overall_conversion_rate'] = float(df['sold_from_leads_pct'].mean())
        
        if 'total_gross' in df.columns:
            metrics['total_gross_all_sources'] = float(df['total_gross'].sum())
            
            # Best ROI source
            if 'lead_source_group' in df.columns:
                best_roi_source = df.loc[df['total_gross'].idxmax(), 'lead_source_group']
                metrics['best_roi_source'] = {
                    'source': best_roi_source,
                    'gross': float(df.loc[df['total_gross'].idxmax(), 'total_gross'])
                }
        
        return metrics
    
    def _calculate_general_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate general metrics for unknown dataset types."""
        metrics = {}
        
        # Basic statistics
        metrics['record_count'] = len(df)
        metrics['column_count'] = len(df.columns)
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            metrics['numeric_summary'] = df[numeric_cols].describe().to_dict()
        
        return metrics
    
    def generate_insights(self, df: pd.DataFrame, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced insights based on dataset type and metrics."""
        dataset_type = metrics.get('dataset_type', 'general')
        
        insights = {
            'summary': self._generate_summary(df, metrics, dataset_type),
            'value_insights': self._extract_value_insights(df, metrics, dataset_type),
            'actionable_flags': self._generate_actionable_flags(df, metrics, dataset_type),
            'confidence': self._assess_confidence(df, metrics)
        }
        
        return insights
    
    def _generate_summary(self, df: pd.DataFrame, metrics: Dict[str, Any], dataset_type: str) -> str:
        """Generate dataset-specific summary."""
        if dataset_type == 'sales_transactions':
            units = metrics.get('total_units_sold', len(df))
            revenue = metrics.get('total_revenue', 0)
            profit = metrics.get('total_profit', 0)
            return f"Analyzed {units} vehicle sales generating ${revenue:,.0f} in revenue and ${profit:,.0f} in profit."
        
        elif dataset_type == 'leaderboard':
            reps = metrics.get('total_reps', len(df))
            top_performer = metrics.get('top_performer', 'Unknown')
            return f"Performance analysis of {reps} sales representatives. Top performer: {top_performer}."
        
        elif dataset_type == 'lead_source_roi':
            total_leads = metrics.get('total_leads_all_sources', 0)
            total_gross = metrics.get('total_gross_all_sources', 0)
            return f"Lead source analysis covering {total_leads:,} leads generating ${total_gross:,.0f} in gross profit."
        
        else:
            return f"Analysis completed on {len(df)} records with {len(df.columns)} data points."
    
    def _extract_value_insights(self, df: pd.DataFrame, metrics: Dict[str, Any], dataset_type: str) -> List[str]:
        """Extract dataset-specific value insights."""
        insights = []
        
        if dataset_type == 'sales_transactions':
            if 'average_sale_price' in metrics:
                insights.append(f"Average vehicle sale price: ${metrics['average_sale_price']:,.0f}")
            
            if 'average_profit_margin' in metrics:
                insights.append(f"Average profit margin: {metrics['average_profit_margin']:.1f}%")
            
            if 'best_lead_source' in metrics:
                source_data = metrics['best_lead_source']
                insights.append(f"Most profitable lead source: {source_data['source']} (${source_data['avg_profit']:,.0f} avg profit)")
            
            if 'top_sales_rep' in metrics:
                rep_data = metrics['top_sales_rep']
                insights.append(f"Top sales representative: {rep_data['name']} (${rep_data['total_profit']:,.0f} total profit)")
        
        elif dataset_type == 'leaderboard':
            if 'top_performer' in metrics:
                insights.append(f"Overall top performer: {metrics['top_performer']}")
            
            # Add performance metric insights
            for key, value in metrics.items():
                if 'avg_' in key and isinstance(value, (int, float)):
                    metric_name = key.replace('avg_', '').replace('_', ' ').title()
                    insights.append(f"Average {metric_name}: {value:.1f}")
        
        elif dataset_type == 'lead_source_roi':
            if 'overall_conversion_rate' in metrics:
                insights.append(f"Overall lead conversion rate: {metrics['overall_conversion_rate']:.1f}%")
            
            if 'best_roi_source' in metrics:
                source_data = metrics['best_roi_source']
                insights.append(f"Highest ROI lead source: {source_data['source']} (${source_data['gross']:,.0f} gross)")
        
        return insights
    
    def _generate_actionable_flags(self, df: pd.DataFrame, metrics: Dict[str, Any], dataset_type: str) -> List[str]:
        """Generate dataset-specific actionable recommendations."""
        flags = []
        
        if dataset_type == 'sales_transactions':
            if 'average_profit_margin' in metrics:
                margin = metrics['average_profit_margin']
                if margin < 10:
                    flags.append("Profit margins below 10% - review pricing strategy and cost management")
                elif margin > 25:
                    flags.append("Strong profit margins - consider expanding successful strategies")
            
            # Lead source recommendations
            if 'lead_source_performance' in metrics:
                flags.append("Analyze lead source performance data to optimize marketing budget allocation")
        
        elif dataset_type == 'leaderboard':
            flags.append("Review bottom performers for coaching opportunities")
            flags.append("Document and replicate top performer strategies across the team")
        
        elif dataset_type == 'lead_source_roi':
            if 'best_roi_source' in metrics:
                flags.append(f"Increase investment in {metrics['best_roi_source']['source']} - highest ROI lead source")
            
            if 'overall_conversion_rate' in metrics and metrics['overall_conversion_rate'] < 20:
                flags.append("Overall conversion rate below 20% - review lead qualification and follow-up processes")
        
        # Data quality flags
        missing_data_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_data_pct > 20:
            flags.append("High percentage of missing data - review data collection and entry processes")
        
        return flags
    
    def _assess_confidence(self, df: pd.DataFrame, metrics: Dict[str, Any]) -> str:
        """Assess confidence level of the analysis."""
        try:
            data_points = len(df)
            missing_data_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            
            if data_points >= 100 and missing_data_pct < 10:
                return 'high'
            elif data_points >= 20 and missing_data_pct < 20:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            return 'medium'
    
    def process_file(self, file_path: str, dealer_id: str) -> Dict[str, Any]:
        """Process a single CSV file and generate insights."""
        try:
            # Load the CSV file
            df = self.load_csv_file(file_path)
            if df is None:
                return {'error': 'Failed to load CSV file', 'status': 'failed'}
            
            # Normalize the data
            df = self.normalize_automotive_data(df)
            
            # Detect dataset type and calculate metrics
            dataset_type = self.detect_dataset_type(df)
            metrics = self.calculate_automotive_metrics(df, dataset_type)
            
            # Generate insights
            insights = self.generate_insights(df, metrics)
            
            # Create processed data record
            processed_data = {
                'dealer_id': dealer_id,
                'file_path': file_path,
                'processed_timestamp': datetime.now().isoformat(),
                'dataset_type': dataset_type,
                'record_count': len(df),
                'columns': list(df.columns),
                'metrics': metrics,
                'insights': insights
            }
            
            # Save processed data
            processed_filename = f"{dealer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_processed.json"
            processed_path = os.path.join(self.data_storage_path, 'processed', processed_filename)
            
            with open(processed_path, 'w') as f:
                json.dump(processed_data, f, indent=2, default=str)
            
            logger.info(f"Processed {dataset_type} file {file_path} for dealer {dealer_id}")
            
            return {
                'status': 'success',
                'processed_data': processed_data,
                'processed_file_path': processed_path
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {'error': str(e), 'status': 'failed'}


if __name__ == '__main__':
    # Test the enhanced processor
    config = {
        'DATA_STORAGE_PATH': '/home/ubuntu/vendora/data'
    }
    
    processor = EnhancedAutomotiveDataProcessor(config)
    print("Enhanced data processor initialized successfully")

