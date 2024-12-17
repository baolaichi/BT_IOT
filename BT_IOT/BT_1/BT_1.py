from sense_emu import SenseHat  # Sử dụng sense_emu cho giả lập
import time

# Khởi tạo Sense HAT
sense = SenseHat()

# Đặt màu sắc cho chữ
text_color = [0, 255, 0]  # Màu xanh lá cây
bg_color = [0, 0, 0]  # Màu đen (nền)

print("Bắt đầu hiển thị tên...")
sense.show_message("LẠI CHÍ BẢO", scroll_speed=0.1, text_colour=text_color, back_colour=bg_color)
print("Hiển thị hoàn tất!")
