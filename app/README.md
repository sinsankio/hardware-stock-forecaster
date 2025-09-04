# Stock Price Forecasting using ARIMA Models

A Flask-based web application for forecasting stock prices using ARIMA (AutoRegressive Integrated Moving Average) models.

## Project Structure

```
app/
├── scripts/
│   ├── templates/
│   │   └── index.html
│   ├── app.py
│   └── lib/
│       └── wrapper.py
├── models/
│   └── fitted_models.joblib
├── data/
│   └── preprocessed/
├── exports/
└── README.md
```

## Features

- Interactive web interface for configuring forecasting parameters
- Support for multiple product analysis
- Comprehensive forecasting results including:
  - Individual product analysis
  - Cumulative analysis
  - Product rankings
- Exportable PDF reports
- Currency in LKR format
- Detailed logging system

## Setup & Installation

1. Clone the repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure all model files are present in the `models` directory

## Running the Application

1. Navigate to the app directory:
   ```bash
   cd app/scripts
   ```
2. Run the Flask application:
   ```bash
   python app.py
   ```
3. Access the application at: http://localhost:5000

## Usage

1. Select date range for forecasting
2. Choose products to analyze
3. Click "Generate Forecast" to process
4. View results in the web interface
5. Download PDF report if needed

## Logging

Logs are stored in `app.log` with the following levels:
- INFO: General application flow
- ERROR: Application errors
- WARNING: Important warnings

## Currency Format

All monetary values are displayed in LKR (Sri Lankan Rupee) format.

## Export Directory

PDF reports are generated in the `exports` directory and automatically downloaded to the user's download folder.
