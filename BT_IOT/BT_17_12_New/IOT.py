from flask import Flask, render_template_string, jsonify
import threading
import pyrebase
from sense_emu import SenseHat
import time
import numpy as np

# Cấu hình Firebase (đã cập nhật)
config = {
    "apiKey": "AIzaSyC8HfhBqnuSBA-VPsulsoMeoEGAqFI-TYA",
    "authDomain": "iot-kmt-2024.firebaseapp.com",
    "databaseURL": "https://iot-kmt-2024-default-rtdb.firebaseio.com",
    "projectId": "iot-kmt-2024",
    "storageBucket": "iot-kmt-2024.firebasestorage.app",
    "messagingSenderId": "923866319316",
    "appId": "1:923866319316:web:c1176e9e18314f66076e41",
    "measurementId": "G-Y3XFFFYHHV"
}

# Khởi tạo Firebase và SenseHAT
firebase = pyrebase.initialize_app(config)
database = firebase.database()
sense = SenseHat()
app = Flask(__name__)

# Biến toàn cục
previous_T = 0  # Giá trị T trước đó
temperature_change_threshold = 0.3  # Ngưỡng thay đổi nhiệt độ
current_data = {"T_cap_nhat": 0, "humidity": 0, "joystick_state": "", "pressure": 0}

# Hàm đọc dữ liệu và tối ưu gửi
def push_optimized_data():
    global previous_T, current_data
    while True:
        try:
            current_temp = round(sense.get_temperature(), 2)
            humidity = round(sense.get_humidity(), 2)
            pressure = round(sense.get_pressure(), 2)

            # Lấy trạng thái joystick
            joystick_events = sense.stick.get_events()
            joystick_state = "Không có sự kiện"
            if joystick_events:
                last_event = joystick_events[-1]
                joystick_state = f"{last_event.direction} - {last_event.action}"

            if abs(current_temp - previous_T) > temperature_change_threshold:
                T_cap_nhat = round((current_temp + previous_T) / 2, 2)
                sensor_data = {
                    "temperature": T_cap_nhat,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                database.child("OptimizedSensorData").set(sensor_data)
                print("Đã gửi dữ liệu lên Firebase:", sensor_data)

                previous_T = T_cap_nhat

            current_data["t_hien_tai"] = current_temp
            current_data["T_cap_nhat"] = T_cap_nhat
            current_data["humidity"] = humidity
            current_data["joystick_state"] = joystick_state
            current_data["pressure"] = pressure

            time.sleep(5)

        except Exception as e:
            print("Lỗi xảy ra:", e)

@app.route('/')
def display_data():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LSB-163</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f7fc; }
            h1 { text-align: center; }
            .container { display: flex; justify-content: space-around; }
            .box { background-color: #fff; padding: 20px; margin: 10px; text-align: center; }
        </style>
    </head>
    <body>
        <h1>Giám sát cảm biến</h1>
        <h1>LSB-163</h1>
        <div class="container">
            <div class="box"><h2>Nhiệt độ hiện tại</h2><p>{{ t_hien_tai }} °C</p></div>
            <div class="box"><h2>Nhiệt độ cập nhật</h2><p>{{ T_cap_nhat }} °C</p></div>
            <div class="box"><h2>Độ ẩm</h2><p>{{ humidity }} %</p></div>
            <div class="box"><h2>Áp suất</h2><p>{{ pressure }} hPa</p></div>
            <div class="box"><h2>Trạng thái Joystick</h2><p>{{ joystick_state }}</p></div>
        </div>
        <script> setInterval(() => location.reload(), 2000); </script>
    </body>
    </html>
    """
    return render_template_string(html_template, **current_data)

if __name__ == '__main__':
    threading.Thread(target=push_optimized_data, daemon=True).start()
    app.run(debug=True)
