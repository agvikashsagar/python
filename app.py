from flask import Flask, render_template, jsonify
import pandas as pd
import openpyxl

app = Flask(__name__)

# Read Excel data into DataFrame
df = pd.read_excel('data.xlsx')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    # Convert DataFrame to JSON
    data = df.to_json(orient='records')
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
