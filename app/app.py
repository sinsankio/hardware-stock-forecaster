import os
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
import logging
from lib.wrapper import StockPriceForecaster

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize forecaster
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
forecaster = StockPriceForecaster(BASE_PATH)

@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/forecast', methods=['POST'])
def forecast():
    try:
        logger.info("Processing forecast request")
        
        # Get form data
        start_date = datetime.strptime(request.form['startDate'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['endDate'], '%Y-%m-%d')
        selected_products = request.form.getlist('products[]')
        
        logger.info(f"Request params - Start: {start_date}, End: {end_date}, Products: {selected_products}")

        # Generate forecasts
        forecasts = forecaster.forecast_prices(selected_products, start_date, end_date)
        
        # Analyze results
        analysis = forecaster.analyze_forecasts()
        
        # Store results in session for PDF generation
        app.config['LATEST_ANALYSIS'] = analysis
        
        return render_template('index.html', results=analysis)
        
    except Exception as e:
        logger.error(f"Error in forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download-report')
def download_report():
    try:
        logger.info("Processing report download request")
        
        if 'LATEST_ANALYSIS' not in app.config:
            raise ValueError("No analysis results available")
            
        # Create exports directory if it doesn't exist
        exports_dir = os.path.join(BASE_PATH, 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate PDF filename
        filename = f"forecast_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(exports_dir, filename)
        
        # Generate PDF
        forecaster.generate_pdf_report(filepath)
        
        logger.info(f"Report generated: {filepath}")
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error in download_report: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
