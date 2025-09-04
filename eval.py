#!/usr/bin/env python
import os
import argparse
from datetime import datetime, timedelta
from lib.wrapper import StockPriceForecaster

class StockPriceForecasterCLI:
    """Command-line interface for StockPriceForecaster"""
    
    def __init__(self, base_path: str):
        """Initialize the CLI with the forecaster"""
        self.forecaster = StockPriceForecaster(base_path)
        self.products = self.forecaster.available_products
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                "Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-06-18)"
            )
    
    def _get_product_selection(self) -> list:
        """Interactive product selection"""
        print("\nAvailable products:")
        for i, product in enumerate(self.products, 1):
            print(f"{i}. {product}")
        
        while True:
            try:
                selection = input("\nEnter product numbers (comma-separated) or 'all': ").strip()
                if selection.lower() == 'all':
                    return self.products
                
                indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
                selected_products = [self.products[i] for i in indices]
                
                # Validate selection
                self.forecaster._validate_products(selected_products)
                return selected_products
                
            except (ValueError, IndexError):
                print("Invalid selection. Please try again.")
    
    def _get_date_range(self) -> tuple:
        """Interactive date range selection"""
        default_start = self.forecaster.default_start_date
        print(f"\nDefault start date is: {default_start.strftime('%Y-%m-%d')}")
        
        while True:
            try:
                start_str = input("Enter start date (YYYY-MM-DD) or press enter for default: ").strip()
                start_date = default_start if not start_str else self._parse_date(start_str)
                
                end_str = input("Enter end date (YYYY-MM-DD): ").strip()
                end_date = self._parse_date(end_str)
                
                # Validate date range
                self.forecaster._validate_dates(start_date, end_date)
                return start_date, end_date
                
            except ValueError as e:
                print(f"Error: {str(e)}")
                print("Please try again.")
    
    def _display_menu(self) -> int:
        """Display main menu and get user choice"""
        print("\n=== Stock Price Forecaster Menu ===")
        print("1. Generate new forecast")
        print("2. View current forecast summary")
        print("3. Generate PDF report")
        print("4. Exit")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (1-4): "))
                if 1 <= choice <= 4:
                    return choice
                print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    
    def _display_forecast_summary(self):
        """Display a summary of the current forecast results"""
        if not self.forecaster.analysis_results:
            print("\nNo forecast results available. Generate a forecast first.")
            return
        
        analysis = self.forecaster.analysis_results
        
        print("\n=== Forecast Summary ===")
        print("\nCumulative Results:")
        cumulative = analysis['cumulative']
        print(f"Total Sales: LKR. {cumulative['total_sales']:,.2f}")
        print(f"Total Sales (Excl. Lost): LKR. {cumulative['total_sales_excluding_lost']:,.2f}")
        print(f"Total Costs: LKR. {cumulative['total_costs']:,.2f}")
        print(f"Total Profit: {cumulative['total_profit']:.2f}%")
        
        print("\nProduct Rankings:")
        rankings = analysis['rankings']
        print(f"Highest Selling: {rankings['highest_selling']}")
        print(f"Most Profitable: {rankings['highest_profit']}")
        print(f"Highest Loss: {rankings['highest_loss']}")
    
    def run(self):
        """Main CLI loop"""
        print("\nWelcome to Stock Price Forecaster!")
        
        while True:
            choice = self._display_menu()
            
            if choice == 1:  # Generate new forecast
                # Get user inputs
                selected_products = self._get_product_selection()
                start_date, end_date = self._get_date_range()
                
                print("\nGenerating forecast...")
                try:
                    # Generate and analyze forecast
                    self.forecaster.forecast_prices(selected_products, start_date, end_date)
                    self.forecaster.analyze_forecasts()
                    print("Forecast generated successfully!")
                    self._display_forecast_summary()
                except Exception as e:
                    print(f"Error generating forecast: {str(e)}")
            
            elif choice == 2:  # View forecast summary
                self._display_forecast_summary()
            
            elif choice == 3:  # Generate PDF report
                if not self.forecaster.analysis_results:
                    print("\nNo forecast results available. Generate a forecast first.")
                    continue
                
                try:
                    output_path = input("\nEnter output path for PDF report: ").strip()
                    if not output_path.endswith('.pdf'):
                        output_path += '.pdf'
                    
                    self.forecaster.generate_pdf_report(output_path)
                    print(f"\nPDF report generated successfully: {output_path}")
                except Exception as e:
                    print(f"Error generating PDF report: {str(e)}")
            
            else:  # Exit
                print("\nThank you for using Stock Price Forecaster!")
                break

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Stock Price Forecaster - Command Line Interface"
    )
    parser.add_argument(
        '--base-path', '-b',
        type=str,
        default=os.path.dirname(os.path.abspath(__file__)),
        help='Base path to the project directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    try:
        cli = StockPriceForecasterCLI(args.base_path)
        cli.run()
    except Exception as e:
        print(f"Error initializing application: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
