from flask import Flask, render_template_string, jsonify
import threading
import sqlite3
from sense_emu import SenseHat
import time
import os

# Khởi tạo SenseHAT và Flask
sense = SenseHat()
app = Flask(__name__)

# Đường dẫn file SQLite
DB_FILE = "sensor_data.db"

# Biến toàn cục
previous_T = 0  # Giá trị T trước đó
temperature_change_threshold = 0.3  # Ngưỡng thay đổi nhiệt độ
current_data = {"T_cap_nhat": 0, "humidity": 0, "joystick_state": "", "pressure": 0}

# Tạo database và bảng SQLite nếu chưa tồn tại
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                temperature REAL,
                humidity REAL,
                pressure REAL
            )
        ''')
        conn.commit()
        conn.close()

# Hàm lưu dữ liệu vào SQLite
def save_to_sqlite(temperature, humidity, pressure):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, temperature, humidity, pressure)
        VALUES (?, ?, ?, ?)
    ''', (time.strftime("%Y-%m-%d %H:%M:%S"), temperature, humidity, pressure))
    conn.commit()
    conn.close()

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
                save_to_sqlite(T_cap_nhat, humidity, pressure)  # Lưu vào SQLite
                print("Đã lưu dữ liệu vào SQLite")

                previous_T = T_cap_nhat

            # Cập nhật dữ liệu hiện tại
            current_data["t_hien_tai"] = current_temp
            current_data["T_cap_nhat"] = previous_T
            current_data["humidity"] = humidity
            current_data["joystick_state"] = joystick_state
            current_data["pressure"] = pressure

            time.sleep(5)

        except Exception as e:
            print("Lỗi xảy ra:", e)

# Hàm đọc dữ liệu lịch sử từ SQLite
def get_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route('/')
def display_data():
    history_data = get_history()  # Lấy dữ liệu lịch sử từ SQLite
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
            table { width: 100%; border-collapse: collapse; margin: 20px auto; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Giám sát cảm biến</h1>
        <h2>LSB-163</h2>
        <div class="container">
            <div class="box"><h2>Nhiệt độ hiện tại</h2><p>{{ t_hien_tai }} °C</p></div>
            <div class="box"><h2>Nhiệt độ cập nhật</h2><p>{{ T_cap_nhat }} °C</p></div>
            <div class="box"><h2>Độ ẩm</h2><p>{{ humidity }} %</p></div>
            <div class="box"><h2>Áp suất</h2><p>{{ pressure }} hPa</p></div>
            <div class="box"><h2>Trạng thái Joystick</h2><p>{{ joystick_state }}</p></div>
        </div>
        <h2 style="text-align:center;">Lịch sử Dữ liệu (10 bản ghi gần nhất)</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Nhiệt độ</th>
                <th>Độ ẩm</th>
                <th>Áp suất</th>
            </tr>
            {% for row in history_data %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }} °C</td>
                <td>{{ row[3] }} %</td>
                <td>{{ row[4] }} hPa</td>
            </tr>
            {% endfor %}
        </table>
        <script> setInterval(() => location.reload(), 2000); </script>
    </body>
    </html>
    """
    return render_template_string(html_template, **current_data, history_data=history_data)

if __name__ == '__main__':
    init_db()  # Tạo database nếu chưa tồn tại
    threading.Thread(target=push_optimized_data, daemon=True).start()
    app.run(debug=True)
