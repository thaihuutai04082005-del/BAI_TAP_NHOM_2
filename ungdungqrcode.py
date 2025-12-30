# source code chính nhóm 2
import sys
import qrcode
import cv2
import webbrowser

from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QMainWindow
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

from pyzbar import pyzbar

from gdchinh import Ui_MainWindow_ManHinhChinh

from gdtaoqr import Ui_MainWindow_GiaoDienTaoQR
from gdcamera import Ui_MainWindow_GiaoDienCamera


class UngDungQRCode:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # ===== MÀN HÌNH CHÍNH =====
        self.window_chinh = QMainWindow()
        self.ui_chinh = Ui_MainWindow_ManHinhChinh()
        self.ui_chinh.setupUi(self.window_chinh)

        # ===== GIAO DIỆN TẠO QR =====
        self.window_taoqr = QMainWindow()
        self.ui_taoqr = Ui_MainWindow_GiaoDienTaoQR()
        self.ui_taoqr.setupUi(self.window_taoqr)

        # ===== GIAO DIỆN CAMERA =====
        self.window_camera = QMainWindow()
        self.ui_camera = Ui_MainWindow_GiaoDienCamera()
        self.ui_camera.setupUi(self.window_camera)

        # QR tạm
        self.qr_temp_path = None

        # Camera
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)

        # ===== KẾT NỐI NÚT =====
        self.ui_chinh.tao_btt.clicked.connect(self.mo_gd_taoqr)
        self.ui_chinh.camera_btt.clicked.connect(self.mo_gd_camera)

        self.ui_taoqr.quaylai_btt.clicked.connect(self.quay_lai)
        self.ui_taoqr.taoqr_btt.clicked.connect(self.tao_qr)
        self.ui_taoqr.luuqr_btt.clicked.connect(self.luu_qr)

        self.ui_camera.batcamera_btt.clicked.connect(self.bat_camera)
        self.ui_camera.tatcamera_btt.clicked.connect(self.tat_camera)
        self.ui_camera.quaylai1_btt.clicked.connect(self.quay_lai_camera)

        # click link
        self.ui_camera.noidungcamera_line.setReadOnly(True)
        self.ui_camera.noidungcamera_line.mousePressEvent = self.mo_link

    # ========================
    # CHUYỂN GIAO DIỆN
    # ========================
    def mo_gd_taoqr(self):
        self.window_chinh.hide()
        self.window_taoqr.show()

    def mo_gd_camera(self):
        self.window_chinh.hide()
        self.window_camera.show()
        self.ui_camera.trangthai_lb.setText("Chưa bật camera")

    def quay_lai(self):
        self.window_taoqr.hide()
        self.window_chinh.show()

    def quay_lai_camera(self):
        self.tat_camera()
        self.window_camera.hide()
        self.window_chinh.show()

    # ========================
    # TẠO QR
    # ========================
    def tao_qr(self):
        noi_dung = self.ui_taoqr.noidungqr_line.text().strip()

        if not noi_dung:
            QMessageBox.warning(self.window_taoqr, "Lỗi", "Vui lòng nhập nội dung")
            return

        qr = qrcode.make(noi_dung)
        self.qr_temp_path = "qr_temp.png"
        qr.save(self.qr_temp_path)

        pixmap = QPixmap(self.qr_temp_path).scaled(
            self.ui_taoqr.anhqr_lb.width(),
            self.ui_taoqr.anhqr_lb.height(),
            Qt.KeepAspectRatio
        )
        self.ui_taoqr.anhqr_lb.setPixmap(pixmap)

    def luu_qr(self):
        if not self.qr_temp_path:
            QMessageBox.warning(self.window_taoqr, "Lỗi", "Chưa có QR")
            return

        path, _ = QFileDialog.getSaveFileName(
            self.window_taoqr, "Lưu QR", "", "PNG (*.png)"
        )
        if path:
            with open(self.qr_temp_path, "rb") as src:
                with open(path, "wb") as dst:
                    dst.write(src.read())
            QMessageBox.information(self.window_taoqr, "OK", "Đã lưu")

    # ========================
    # CAMERA
    # ========================
    def bat_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self.window_camera, "Lỗi", "Không mở được camera")
            return

        self.timer.start(30)
        self.ui_camera.trangthai_lb.setText("Đang quét...")

    def tat_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.ui_camera.mayanh_lb.clear()
        self.ui_camera.trangthai_lb.setText("Camera đã tắt")

    def update_camera(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        for barcode in pyzbar.decode(frame):
            data = barcode.data.decode("utf-8")
            self.ui_camera.noidungcamera_line.setText(data)
            self.ui_camera.trangthai_lb.setText("Đã nhận QR")
            self.timer.stop()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            self.ui_camera.mayanh_lb.width(),
            self.ui_camera.mayanh_lb.height(),
            Qt.KeepAspectRatio
        )
        self.ui_camera.mayanh_lb.setPixmap(pix)

    # ========================
    # MỞ LINK
    # ========================
    def mo_link(self, event):
        text = self.ui_camera.noidungcamera_line.text()
        if text.startswith("http://") or text.startswith("https://"):
            webbrowser.open(text)

    # ========================
    # CHẠY APP
    # ========================
    def run(self):
        self.window_chinh.show()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = UngDungQRCode()
    app.run()
