from machine import Pin, ADC
from dht import DHT11
import time
import network
import urequests
import json

dht_sensor = DHT11(Pin(32))
soil_sensor = ADC(Pin(34))

soil_sensor.atten(ADC.ATTN_11DB)
soil_sensor.width(ADC.WIDTH_12BIT)

WIFI_SSID = "Lab Komp 3"
WIFI_PASSWORD = "kom12345"
API_URL = "http://192.168.1.7:5000/sensor-data"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    return wlan.ifconfig()[0]

def read_dht11():
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        return temperature, humidity
    except Exception as e:
        print('Error reading DHT11:', e)
        return None, None

def read_soil_moisture():
    try:
        raw_value = soil_sensor.read()
        moisture_percentage = ((4095 - raw_value) / (4095 - 1800)) * 100
        moisture_percentage = max(0, min(100, moisture_percentage))
        return moisture_percentage
    except Exception as e:
        print('Error reading soil moisture:', e)
        return None

def send_data_to_api(temperature, humidity, soil_moisture):
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "soil-moisture": soil_moisture
    }
    
    try:
        response = urequests.post(
            API_URL,
            headers={'content-type': 'application/json'},
            data=json.dumps(data)
        )
        response.close()
        return True
    except Exception as e:
        print('Error sending data:', e)
        return False

def main():
    ip = connect_wifi()
    print('Connected to WiFi, IP:', ip)
    
    while True:
        temperature, humidity = read_dht11()
        moisture = read_soil_moisture()
        
        if all(value is not None for value in [temperature, humidity, moisture]):
            print(f'Temperature: {temperature}°C')
            print(f'Humidity: {humidity}%')
            print(f'Soil Moisture: {moisture:.1f}%')
            
            if send_data_to_api(temperature, humidity, moisture):
                print('Data sent successfully')
            else:
                print('Failed to send data')
                
        print('-------------------')
        time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Program terminated by user')
    except Exception as e:
        print('An error occurred:', e)
