from flask import Flask, request, render_template_string
from pathlib import Path
import os
import base64
from cryptography.fernet import Fernet
import json

app = Flask(__name__)

# Generate encryption key first run
SETUP_KEY = Fernet.generate_key() if not Path(".setupkey").exists() else open(".setupkey","rb").read()
cipher = Fernet(SETUP_KEY)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>VA Setup Wizard</title>
    <style>
        .container { max-width: 800px; margin: 2rem auto; padding: 2rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; }
        input { width: 100%; padding: 0.5rem; }
        .profit-calc { background: #f5f5f5; padding: 1rem; margin: 1rem 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Virtual Assistant Setup</h1>
        
        <div class="profit-calc">
            <h3>Profit Target: ${{ target_weekly | default('2000') }}/week</h3>
            <label>Desired Weekly Profit:
                <input type="number" name="target_profit" value="2500" min="2000" max="10000">
            </label>
        </div>

        <form method="POST">
            <div class="form-group">
                <label>OpenAI API Key:</label>
                <input type="password" name="openai_key" required>
            </div>

            <div class="form-group">
                <label>Printify API Key:</label>
                <input type="password" name="printify_key" required>
            </div>

            <div class="form-group">
                <label>Etsy API Key:</label>
                <input type="password" name="etsy_key" required>
            </div>

            <div class="form-group">
                <label>Notification Email:</label>
                <input type="email" name="alert_email" required>
            </div>

            <h3>Profit Optimization</h3>
            <div class="form-group">
                <label>Minimum Margin:
                    <input type="number" name="min_margin" value="65" min="50" max="100" step="5">%
                </label>
            </div>

            <div class="form-group">
                <label>Daily Product Limit:
                    <input type="number" name="daily_products" value="15" min="5" max="50">
                </label>
            </div>

            <button type="submit">Save & Initialize System</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        config = {
            'OPENAI_KEY': cipher.encrypt(request.form['openai_key'].encode()).decode(),
            'PRINTIFY_KEY': cipher.encrypt(request.form['printify_key'].encode()).decode(),
            'ETSY_KEY': cipher.encrypt(request.form['etsy_key'].encode()).decode(),
            'ALERT_EMAIL': request.form['alert_email'],
            'TARGET_PROFIT': int(request.form['target_profit']),
            'MIN_MARGIN': float(request.form['min_margin']) / 100,
            'DAILY_PRODUCTS': int(request.form['daily_products'])
        }
        
        # Save encrypted config
        with open('config.va', 'w') as f:
            json.dump(config, f)
            
        # Initialize environment
        Path(".setupkey").write_bytes(SETUP_KEY)
        os.makedirs('data', exist_ok=True)
        
        return '''
            <h2>Setup Complete!</h2>
            <p>System initialized with:</p>
            <ul>
                <li>Weekly Target: ${}</li>
                <li>Daily Products: {}</li>
                <li>Margin Floor: {}%</li>
            </ul>
            <p>Run the system: <code>docker-compose up --build</code></p>
        '''.format(config['TARGET_PROFIT'], config['DAILY_PRODUCTS'], config['MIN_MARGIN']*100)
    
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')