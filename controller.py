from flask import Flask, request, jsonify
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://admin:admin@cluster0.k4wda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

mongodb_client = MongoClient(MONGODB_URI)
db = mongodb_client['sensor_data']
collection = db['readings']

def send_to_ubidots(data):
    url = "https://industrial.api.ubidots.com/api/v1.6/devices/esp32-devkit-v1"
    headers = {
        "X-Auth-Token": "BBUS-xZP4uuqxXFHy6n7PLGz30DcHN8EPyK",
        "Content-Type": "application/json"
    }
    
    payload = {
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "soil-moisture": data["soil-moisture"]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f'Error sending to Ubidots: {e}')
        return False

@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    
    required_fields = ['temperature', 'humidity', 'soil-moisture']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    UTC_OFFSET = timedelta(hours=7)
    timezone_wib = timezone(UTC_OFFSET)
    timestamp = datetime.now(timezone.utc).astimezone(timezone_wib)

    
    mongodb_data = {
        'timestamp': timestamp,
        'temperature': data['temperature'],
        'humidity': data['humidity'],
        'soil-moisture': data['soil-moisture']
    }
    
    try:
        collection.insert_one(mongodb_data)
    except Exception as e:
        return jsonify({'error': f'MongoDB error: {str(e)}'}), 500
        
    ubidots_success = send_to_ubidots(data)
    
    response = {
        'status': 'success',
        'mongodb_saved': True,
        'ubidots_saved': ubidots_success,
        'timestamp': timestamp.isoformat()
    }
    
    return jsonify(response), 200

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    try:
        limit = int(request.args.get('limit', 10))
        data = list(collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(limit))
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching data: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)