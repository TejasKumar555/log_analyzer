from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
import re
from datetime import datetime
import plotly
import plotly.express as px

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'log'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

LOG_PATTERN = re.compile(r'^\[(.*?)\] \[(.*?)\] (.*)$')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_log_file(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            match = LOG_PATTERN.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    timestamp = None
                data.append({
                    'timestamp': timestamp,
                    'level': level,
                    'message': message
                })
    df = pd.DataFrame(data)
    # Remove rows with invalid timestamp
    df = df.dropna(subset=['timestamp'])
    return df if not df.empty else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print('--- Upload route called ---')
        if 'file' not in request.files:
            print('No file part in request.files')
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        print(f'Received file: {file.filename}')
        if file.filename == '':
            print('No selected file')
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            print('File is allowed type')
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            print(f'Saving file to: {filename}')
            file.save(filename)
            print('Parsing the file...')
            df = parse_log_file(filename)
            if df is not None:
                print('Parsing successful!')
                print(f'Parsed DataFrame columns: {df.columns}')
                if not all(col in df.columns for col in ['timestamp', 'level', 'message']):
                    print('Parsed DataFrame missing required columns!')
                    return jsonify({'error': f"Parsed DataFrame missing columns: {df.columns.tolist()}"}), 400
                parsed_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'parsed_' + file.filename + '.csv')
                df.to_csv(parsed_filename, index=False)
                print(f'Parsed CSV saved to: {parsed_filename}')
                stats = {
                    'total_logs': len(df),
                    'log_levels': df['level'].value_counts().to_dict(),
                    'time_range': {
                        'start': df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                        'end': df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                print(f'Stats: {stats}')
                return jsonify({
                    'success': True,
                    'stats': stats,
                    'filename': file.filename
                })
            else:
                print('Failed to parse log file (DataFrame is None)')
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    print('File content:')
                    for l in lines:
                        print(l.strip())
                return jsonify({'error': 'Failed to parse log file. Please check the log format.'}), 400
        else:
            print('Invalid file type')
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        import traceback
        print(f"Error in upload: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/get_stats/<filename>')
def get_stats(filename):
    try:
        parsed_file = os.path.join(app.config['UPLOAD_FOLDER'], 'parsed_' + filename + '.csv')
        if not os.path.exists(parsed_file):
            return jsonify({'error': 'File not found'}), 404

        df = pd.read_csv(parsed_file)
        print("Loaded DataFrame columns:", df.columns)
        # Ensure timestamp is parsed as datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        else:
            return jsonify({'error': 'No timestamp column in parsed CSV'}), 400
        df = df.dropna(subset=['timestamp'])

        # 1. Log Level Distribution (histogram)
        fig1 = px.histogram(df, x='level', title='Log Level Distribution', color='level')

        # 2. Logs per Hour (line)
        df['hour'] = df['timestamp'].dt.floor('H')
        logs_per_hour = df.groupby('hour').size().reset_index(name='count')
        fig2 = px.line(logs_per_hour, x='hour', y='count', title='Logs per Hour', markers=True)

        # 3. Log Level Pie Chart
        fig_pie = px.pie(df, names='level', title='Log Level Proportion', hole=0.4)

        # 4. Top Error/Warning Messages Table
        errors = df[df['level'].isin(['ERROR', 'CRITICAL', 'WARNING'])]
        top_errors = errors['message'].value_counts().head(5)
        top_errors_table = [[msg, count] for msg, count in top_errors.items()]

        # 5. Unique Messages
        unique_messages = df['message'].drop_duplicates().head(10).tolist()

        # 6. Active Users (if present in message)
        import re
        user_regex = re.compile(r'User login: (\w+)|User logout: (\w+)')
        users = []
        for msg in df['message']:
            match = user_regex.search(msg)
            if match:
                users.append(match.group(1) or match.group(2))
        from collections import Counter
        user_counts = Counter(users)
        active_users = [f"{user} ({count})" for user, count in user_counts.most_common(5)] if users else []

        # 7. Idle Periods (longest gaps between logs)
        df_sorted = df.sort_values('timestamp')
        time_gaps = df_sorted['timestamp'].diff().dropna()
        idle_periods = []
        if not time_gaps.empty:
            top_gaps = time_gaps.sort_values(ascending=False).head(5)
            for idx, gap in top_gaps.items():
                end = df_sorted.loc[idx, 'timestamp']
                start = end - gap
                idle_periods.append([start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'), int(gap.total_seconds()//60)])

        plots = {
            'level_distribution': json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
            'logs_per_hour': json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
            'level_pie': json.dumps(fig_pie, cls=plotly.utils.PlotlyJSONEncoder),
            'top_errors': top_errors_table,
            'unique_messages': unique_messages,
            'active_users': active_users,
            'idle_periods': idle_periods
        }
        return jsonify(plots)
    except Exception as e:
        import traceback
        print("Error in get_stats:", str(e))
        traceback.print_exc()
        return jsonify({'error': f'Error generating plots: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
