# Log Analyzer

A web application for analyzing log files. This application allows you to upload log files, process them, and visualize the results through various metrics and graphs.

## Features

- Upload log files through a user-friendly interface
- Parse and process logs by timestamp, log level, and message
- Generate statistics and visualizations
- Store parsed data for future reference
- Responsive design that works on all devices

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Click the "Upload" button to select a log file
2. The application will automatically process the file and display:
   - Summary statistics
   - Log level distribution graph
   - Logs per hour graph
3. The processed data is stored locally and can be accessed later

## Log Format

The application currently supports log files in the following format:
```
[timestamp] [level] message
```
Example:
```
[2025-06-01 14:30:00] [INFO] Application started
[2025-06-01 14:30:01] [ERROR] Failed to connect to database
```

## Technologies Used

- Backend: Flask (Python)
- Frontend: HTML5, CSS3, JavaScript
- Visualization: Plotly.js
- UI Framework: Bootstrap 5
