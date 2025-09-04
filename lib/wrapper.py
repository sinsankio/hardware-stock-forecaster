import os
import joblib
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class StockPriceForecaster:
    """
    A wrapper class for stock price forecasting using pre-trained ARIMA/ARIMAX models.
    Provides comprehensive analysis and reporting capabilities.
    """
    
    def __init__(self, base_path: str):
        """
        Initialize the forecaster with model paths and data.
        
        Args:
            base_path (str): Base path to the project directory
        """
        self.base_path = base_path
        self.default_start_date = datetime(2025, 6, 18)
        self.available_products = ['P001', 'P002', 'P003', 'P004', 'P007', 'P012']
        
        # Product losses dictionary
        self.product_losses = {
            'P001': 2.0, 'P002': 6.0, 'P003': 0.0,
            'P004': 8.0, 'P007': 6.0, 'P012': 5.0
        }
        
        # Load fitted models and statistics
        self._load_models_and_stats()
        
        # Initialize forecast results storage
        self.forecast_results = {}
        self.analysis_results = {}
        
    def _load_models_and_stats(self):
        """Load pre-trained models and product statistics"""
        models_path = os.path.join(self.base_path, 'models', 'fitted_models.joblib')
        stats_path = os.path.join(self.base_path, 'data', 'preprocessed', 'final-phase', 
                                'product_statistics.joblib')
        
        self.fitted_models = joblib.load(models_path)
        self.product_stats = joblib.load(stats_path)
        
    def _validate_dates(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Validate the start and end dates for analysis.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            bool: True if dates are valid, False otherwise
        """
        if start_date < self.default_start_date:
            raise ValueError(f"Start date cannot be before {self.default_start_date}")
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
        return True
    
    def _validate_products(self, products: List[str]) -> bool:
        """
        Validate the selected products.
        
        Args:
            products: List of product IDs to validate
            
        Returns:
            bool: True if products are valid, False otherwise
        """
        if not products:
            raise ValueError("At least one product must be selected")
        
        invalid_products = set(products) - set(self.available_products)
        if invalid_products:
            raise ValueError(f"Invalid products: {invalid_products}")
        
        return True
    
    # def _denormalize_value(self, value: float, product_id: str, price_type: str) -> float:
    #     """
    #     Denormalize a model prediction to real-world value.
        
    #     Args:
    #         value: Normalized value from model prediction
    #         product_id: Product identifier
    #         price_type: Type of price ('cost' or 'selling')
            
    #     Returns:
    #         float: Denormalized value
    #     """
    #     stats = self.product_stats[product_id][price_type]
    #     return (value * stats['std']) + stats['mean']

    def _reverse_differencing(self, forecast: np.ndarray, last_original_value: float) -> np.ndarray:
        """
        Reverse first differencing transformation.
        
        Args:
            forecast: ARIMA predictions on differenced data
            last_original_value: last value from original series before differencing
            
        Returns:
            np.ndarray: Forecast in original scale
        """
        original_scale_forecast = []
        current_value = last_original_value
        
        for diff_forecast in forecast:
            next_value = current_value + diff_forecast
            original_scale_forecast.append(next_value)
            current_value = next_value
        
        return np.array(original_scale_forecast)

    def forecast_prices(self, products: List[str], start_date: datetime, 
                       end_date: datetime) -> Dict:
        """
        Forecast prices for selected products within the specified date range.
        
        Args:
            products: List of product IDs to forecast
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dict: Forecasting results for each product
        """
        # Validate inputs
        self._validate_dates(start_date, end_date)
        self._validate_products(products)
        
        # Calculate forecast period
        forecast_days = (end_date - self.default_start_date).days + 1
        
        # Store results for each product
        self.forecast_results = {}
        
        for product_id in products:
            # Get models for the product
            cost_model = self.fitted_models['cost'][product_id]
            selling_model = self.fitted_models['selling'][product_id]
            
            # Get last values from original series
            stats = self.product_stats[product_id]
            last_cost_value = stats['cost']['last_value']
            last_selling_value = stats['selling']['last_value']
            
            # Generate cost price forecasts and reverse transformations
            cost_forecast = cost_model.forecast(steps=forecast_days)
            cost_forecast_copy = cost_forecast.copy()

            # First denormalize
            # cost_forecast = np.array([self._denormalize_value(v, product_id, 'cost') for v in cost_forecast])
            # Then reverse differencing
            cost_forecast = self._reverse_differencing(cost_forecast, last_cost_value)
            
            cost_forecast = pd.Series(
                cost_forecast,
                index=pd.date_range(self.default_start_date, periods=forecast_days)
            )
            
            # Generate selling price forecasts using cost as exogenous variable
            selling_forecast = selling_model.forecast(
                steps=forecast_days,
                exog=cost_forecast_copy.reshape(-1, 1)
            )
            # First denormalize
            # selling_forecast = np.array([self._denormalize_value(v, product_id, 'selling') for v in selling_forecast])
            # Then reverse differencing
            selling_forecast = self._reverse_differencing(selling_forecast, last_selling_value)
            
            selling_forecast = pd.Series(
                selling_forecast,
                index=pd.date_range(self.default_start_date, periods=forecast_days)
            )
            
            # Filter forecasts to user-specified date range
            mask = (selling_forecast.index >= start_date) & (selling_forecast.index <= end_date)
            
            self.forecast_results[product_id] = {
                'cost': cost_forecast[mask],
                'selling': selling_forecast[mask]
            }
        
        return self.forecast_results
    
    def analyze_forecasts(self) -> Dict:
        """
        Analyze forecasted data and calculate various metrics.
        
        Returns:
            Dict: Analysis results including all required metrics
        """
        if not self.forecast_results:
            raise ValueError("No forecast results available. Run forecast_prices first.")
            
        analysis = {
            'individual_products': {},
            'cumulative': {
                'total_sales': 0,
                'total_sales_excluding_lost': 0,
                'total_costs': 0,
                'total_profit': 0
            },
            'rankings': {}
        }
        
        # Analyze each product
        for product_id, forecasts in self.forecast_results.items():
            cost_series = forecasts['cost']
            selling_series = forecasts['selling']
            days = len(selling_series)
            
            # Calculate metrics
            total_sales = selling_series.sum()
            total_costs = cost_series.sum()
            loss_percentage = self.product_losses[product_id]
            sales_excluding_lost = total_sales * ((100 - loss_percentage) / 100)
            
            product_analysis = {
                'end_selling_price': selling_series.iloc[-1],
                'end_cost_price': cost_series.iloc[-1],
                'avg_selling_price': selling_series.mean(),
                'avg_cost_price': cost_series.mean(),
                'total_sales': total_sales,
                'total_costs': total_costs,
                'profit_percentage': ((total_sales - total_costs) / total_sales) * 100,
                'sales_excluding_lost': sales_excluding_lost,
                'profit_excluding_lost': ((sales_excluding_lost - total_costs) / sales_excluding_lost) * 100
            }
            
            analysis['individual_products'][product_id] = product_analysis
            
            # Update cumulative metrics
            analysis['cumulative']['total_sales'] += total_sales
            analysis['cumulative']['total_sales_excluding_lost'] += sales_excluding_lost
            analysis['cumulative']['total_costs'] += total_costs
            
        # Calculate cumulative profit
        analysis['cumulative']['total_profit'] = (
            (analysis['cumulative']['total_sales'] - analysis['cumulative']['total_costs']) /
            analysis['cumulative']['total_sales'] * 100
        )
        
        # Find rankings
        products_data = analysis['individual_products']
        analysis['rankings'] = {
            'highest_selling': max(products_data.items(), 
                                 key=lambda x: x[1]['total_sales'])[0],
            'highest_profit': max(products_data.items(), 
                                key=lambda x: x[1]['profit_percentage'])[0],
            'highest_loss': min(products_data.items(), 
                              key=lambda x: x[1]['profit_percentage'])[0]
        }
        
        self.analysis_results = analysis
        return analysis
    
    def generate_pdf_report(self, output_path: str):
        """
        Generate a comprehensive PDF report of the analysis.
        
        Args:
            output_path: Path where the PDF report should be saved
        """
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run analyze_forecasts first.")
        
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 15)
                self.cell(0, 10, 'Stock Price Forecast Analysis Report', 0, 1, 'C')
                self.ln(10)
            
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        pdf = PDF()
        pdf.add_page()
        
        # Add report generation date
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        pdf.ln(5)
        
        # Individual Product Analysis
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Individual Product Analysis', 0, 1)
        
        for product_id, analysis in self.analysis_results['individual_products'].items():
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, f'Product: {product_id}', 0, 1)
            
            pdf.set_font('Arial', '', 10)
            metrics = [
                f"End Selling Price: LKR. {analysis['end_selling_price']:.2f}",
                f"End Cost Price: LKR. {analysis['end_cost_price']:.2f}",
                f"Average Selling Price: LKR. {analysis['avg_selling_price']:.2f}",
                f"Average Cost Price: LKR. {analysis['avg_cost_price']:.2f}",
                f"Total Sales: LKR. {analysis['total_sales']:.2f}",
                f"Total Costs: LKR. {analysis['total_costs']:.2f}",
                f"Profit Percentage: {analysis['profit_percentage']:.2f}%",
                f"Sales Excluding Lost: LKR. {analysis['sales_excluding_lost']:.2f}",
                f"Profit Excluding Lost: {analysis['profit_excluding_lost']:.2f}%"
            ]
            
            for metric in metrics:
                pdf.cell(0, 7, metric, 0, 1)
            pdf.ln(5)
        
        # Cumulative Analysis
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Cumulative Analysis', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        cumulative = self.analysis_results['cumulative']
        pdf.cell(0, 7, f"Total Sales: LKR. {cumulative['total_sales']:.2f}", 0, 1)
        pdf.cell(0, 7, f"Total Sales (Excluding Lost): LKR. {cumulative['total_sales_excluding_lost']:.2f}", 0, 1)
        pdf.cell(0, 7, f"Total Costs: LKR. {cumulative['total_costs']:.2f}", 0, 1)
        pdf.cell(0, 7, f"Total Profit Percentage: {cumulative['total_profit']:.2f}%", 0, 1)
        
        # Rankings
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Product Rankings', 0, 1)
        
        pdf.set_font('Arial', '', 10)
        rankings = self.analysis_results['rankings']
        pdf.cell(0, 7, f"Highest Selling Product: {rankings['highest_selling']}", 0, 1)
        pdf.cell(0, 7, f"Most Profitable Product: {rankings['highest_profit']}", 0, 1)
        pdf.cell(0, 7, f"Highest Loss Product: {rankings['highest_loss']}", 0, 1)
        
        # Save the PDF
        pdf.output(output_path)
