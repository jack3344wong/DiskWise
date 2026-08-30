from PyQt5.QtGui import QImage, QPainter, QColor, QPolygon
from PyQt5.QtCore import Qt, QPoint
import os

def make_arrow(filepath, direction, color="#52606d", size=16):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)  # transparent
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    cx = size // 2
    if direction == "up":
        points = [QPoint(cx, 3), QPoint(3, size - 3), QPoint(size - 3, size - 3)]
    else:
        points = [QPoint(3, 3), QPoint(size - 3, 3), QPoint(cx, size - 3)]
    poly = QPolygon(points)
    p.drawPolygon(poly)
    p.end()
    img.save(filepath, "PNG")
    print(f"Saved {filepath}")

assets = r"C:\Users\JackA\Desktop\电脑运行监测工具\assets"
make_arrow(os.path.join(assets, "arrow_up.png"), "up")
make_arrow(os.path.join(assets, "arrow_down.png"), "down")
print("Done")
