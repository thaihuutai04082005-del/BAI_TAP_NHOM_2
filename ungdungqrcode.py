import sys
import cv2
import qrcode
import webbrowser
import numpy as np
from io import BytesIO

from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

from pyzbar import pyzbar

# Import các file giao diện của bạn
from gdchinh import Ui_MainWindow_ManHinhChinh
from gdtaoqr import Ui_mainWindow_GiaoDienTaoQR
from gdcamera import Ui_MainWindow_GiaoDienCamera
from gdquetanh import Ui_MainWindow_GiaoDienQuetAnh
from gdhd import Ui_MainWindow_GiaoDienHuongDan

class UngDungQRCode:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # ========================
        # KHỞI TẠO CÁC MÀN HÌNH
        # ========================
        self.window_chinh = QMainWindow()
        self.ui_chinh = Ui_MainWindow_ManHinhChinh()
        self.ui_chinh.setupUi(self.window_chinh)
        self.window_chinh.setWindowTitle("Ứng Dụng QR & Barcode Studio")

        self.window_taoqr = QMainWindow()
        self.ui_taoqr = Ui_mainWindow_GiaoDienTaoQR()
        self.ui_taoqr.setupUi(self.window_taoqr)
        self.window_taoqr.setWindowTitle("Ứng Dụng QR & Barcode Studio")

        self.window_camera = QMainWindow()
        self.ui_camera = Ui_MainWindow_GiaoDienCamera()
        self.ui_camera.setupUi(self.window_camera)
        
        self.window_camera.setWindowTitle("Ứng Dụng QR & Barcode Studio")

        self.window_quetanh = QMainWindow()
        self.ui_quetanh = Ui_MainWindow_GiaoDienQuetAnh()
        self.ui_quetanh.setupUi(self.window_quetanh)
        self.window_quetanh.setWindowTitle("Ứng Dụng QR & Barcode Studio")

        self.window_hd = QMainWindow()
        self.ui_hd = Ui_MainWindow_GiaoDienHuongDan()
        self.ui_hd.setupUi(self.window_hd)
        self.window_hd.setWindowTitle("Ứng Dụng QR & Barcode Studio")

        # ========================
        # ĐỊNH NGHĨA CÁC STYLE CSS (FIX BO TRÒN & TRẠNG THÁI)
        # ========================
        # Style cho LineEdit (Giữ bo tròn 12px)
        self.khung_style_goc = """
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #BDBDBD;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 14px;
                color: #333333;
            }
        """
        self.khung_style_link = """
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #BDBDBD;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 14px;
                color: blue;
                text-decoration: underline;
            }
        """
        # Style cho khung Trạng thái Camera (Viền xanh neon, chữ trắng đậm)
        self.css_trang_thai = """
            QLabel {
                background-color: rgba(255, 255, 255, 20); 
                border: 2px solid rgba(120, 200, 255, 180); 
                border-radius: 8px;
                color: #ffffff;
                font-weight: bold;
                padding-left: 10px;
            }
        """

        # ========================
        # BIẾN HỖ TRỢ
        # ========================
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.quet_qr_tu_camera)
        self.qr_image = None 

        # ========================
        # KẾT NỐI SỰ KIỆN NÚT BẤM
        # ========================
        self.ui_chinh.tao_btt.clicked.connect(self.mo_gd_taoqr)
        self.ui_chinh.camera_btt.clicked.connect(self.mo_gd_camera)
        self.ui_chinh.anh_btt.clicked.connect(self.mo_gd_quetanh)
        self.ui_chinh.huongdan_btt.clicked.connect(self.mo_gd_hd)
        self.ui_chinh.thoat_btt.clicked.connect(self.window_chinh.close)

        self.ui_taoqr.taoqr_btt.clicked.connect(self.tao_qr)
        self.ui_taoqr.luuqr_btt.clicked.connect(self.luu_qr)
        self.ui_taoqr.quaylai_btt.clicked.connect(self.ve_chinh)
        self.ui_taoqr.xoa1_btt.clicked.connect(self.xoa_taoqr)

        self.ui_camera.batcamera_btt.clicked.connect(self.bat_camera)
        self.ui_camera.tatcamera_btt.clicked.connect(self.tat_camera)
        self.ui_camera.quaylai1_btt.clicked.connect(self.ve_chinh_camera)
        self.ui_camera.xoa2_btt.clicked.connect(self.xoa_camera)

        self.ui_quetanh.chonanh_btt.clicked.connect(self.quet_tu_anh)
        self.ui_quetanh.quaylai2_btt.clicked.connect(self.ve_chinh_quetanh)
        self.ui_quetanh.xoa3_btt.clicked.connect(self.xoa_quetanh)

        self.ui_hd.ql_btt.clicked.connect(self.ve_chinh_hd)

        # ========================
        # THIẾT LẬP MẶC ĐỊNH (CĂN GIỮA & CSS)
        # ========================
        self.ui_camera.noidungcamera_line.setReadOnly(True)
        self.ui_quetanh.noidunganh_line.setReadOnly(True)

        # Căn giữa ảnh tuyệt đối (Fix lỗi lệch khung trang trí)
        self.ui_quetanh.qrbarcode1_lb.setAlignment(Qt.AlignCenter)
        self.ui_quetanh.qrbarcode2_lb.setAlignment(Qt.AlignCenter)
        self.ui_camera.mayanh_lb.setAlignment(Qt.AlignCenter)
        self.ui_taoqr.anhqr_lb.setAlignment(Qt.AlignCenter)

        # Áp dụng CSS ban đầu
        self.ui_camera.trangthai_lb.setStyleSheet(self.css_trang_thai)
        self.ui_camera.noidungcamera_line.setStyleSheet(self.khung_style_goc)
        self.ui_quetanh.noidunganh_line.setStyleSheet(self.khung_style_goc)

    def mo_web_an_toan(self, url):
        """Mở trình duyệt mà không làm tắt ứng dụng"""
        if url:
            webbrowser.open(url, new=2)

    # ========================
    # ĐIỀU HƯỚNG GIAO DIỆN
    # ========================
    def mo_gd_hd(self): 
        self.window_chinh.hide() 
        self.window_hd.show()

    def ve_chinh_hd(self): 
        self.window_hd.hide() 
        self.window_chinh.show()
    
    def mo_gd_taoqr(self): 
        self.xoa_taoqr()
        self.window_chinh.hide() 
        self.window_taoqr.show()
    
    def ve_chinh(self): 
        self.xoa_taoqr()
        self.window_taoqr.hide() 
        self.window_chinh.show()
    
    def mo_gd_camera(self): 
        self.xoa_camera()
        self.window_chinh.hide()
        self.window_camera.show()
        self.ui_camera.trangthai_lb.setText("Chưa bật camera")

    def ve_chinh_camera(self): 
        self.tat_camera() 
        self.xoa_camera()
        self.window_camera.hide() 
        self.window_chinh.show()
    
    def mo_gd_quetanh(self): 
        self.xoa_quetanh() 
        self.window_chinh.hide()
        self.window_quetanh.show()
    
    def ve_chinh_quetanh(self): 
        self.xoa_quetanh() 
        self.window_quetanh.hide() 
        self.window_chinh.show()

    # ========================
    # CHỨC NĂNG XÓA
    # ========================
    def xoa_taoqr(self):
        self.ui_taoqr.noidungqr_line.clear()
        self.ui_taoqr.anhqr_lb.clear()
        self.qr_image = None

    def xoa_camera(self):
        self.ui_camera.noidungcamera_line.clear()
        self.ui_camera.noidungcamera_line.setStyleSheet(self.khung_style_goc)
        self.ui_camera.noidungcamera_line.setCursor(Qt.IBeamCursor)
        self.ui_camera.noidungcamera_line.mousePressEvent = None
        if self.cap and self.cap.isOpened():
            self.ui_camera.trangthai_lb.setText("Đang quét...")
            self.timer.start(30)
        else:
            self.ui_camera.trangthai_lb.setText("Chưa bật camera")
            self.ui_camera.mayanh_lb.clear()

    def xoa_quetanh(self):
        self.ui_quetanh.noidunganh_line.clear()
        self.ui_quetanh.noidunganh_line.setStyleSheet(self.khung_style_goc)
        self.ui_quetanh.noidunganh_line.setCursor(Qt.IBeamCursor)
        self.ui_quetanh.noidunganh_line.mousePressEvent = None
        self.ui_quetanh.loaima_lb.setText("...")
        self.ui_quetanh.qrbarcode1_lb.clear()
        self.ui_quetanh.qrbarcode2_lb.clear()

    # ========================
    # LOGIC CHÍNH
    # ========================
    def tao_qr(self):
        try:
            text = self.ui_taoqr.noidungqr_line.text().strip()
            if not text:
                QMessageBox.warning(self.window_taoqr, "Lỗi", "Vui lòng nhập nội dung")
                return
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(text); qr.make(fit=True)
            self.qr_image = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            self.qr_image.save(buffer, format="PNG")
            qimage = QImage.fromData(buffer.getvalue())
            self.ui_taoqr.anhqr_lb.setPixmap(QPixmap.fromImage(qimage).scaled(self.ui_taoqr.anhqr_lb.width(), self.ui_taoqr.anhqr_lb.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.critical(self.window_taoqr, "Lỗi", str(e))

    def luu_qr(self):
        if self.qr_image:
            path, _ = QFileDialog.getSaveFileName(self.window_taoqr, "Lưu QR", "", "PNG (*.png)")
            if path: self.qr_image.save(path); QMessageBox.information(self.window_taoqr, "OK", "Đã lưu!")

    def bat_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self.window_camera, "Lỗi", "Không mở được camera")
            return
        self.timer.start(30)
        self.ui_camera.trangthai_lb.setText("Đang quét...")

    def tat_camera(self):
        self.timer.stop()
        self.ui_camera.noidungcamera_line.clear()
        if self.cap: self.cap.release(); self.cap = None
        self.ui_camera.mayanh_lb.clear()
        self.ui_camera.trangthai_lb.setText("Chưa bật camera")

    def quet_qr_tu_camera(self):
        ret, frame = self.cap.read()
        if not ret: return
        codes = pyzbar.decode(frame)
        if codes:
            for code in codes:
                if code.type == 'QRCODE':
                    pts = np.array([[p.x, p.y] for p in code.polygon], np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 4)
                    
                    data = code.data.decode("utf-8")
                    self.ui_camera.noidungcamera_line.setText(data)
                    self.ui_camera.trangthai_lb.setText("Đã nhận QR Code")
                    
                    if data.startswith("http"):
                        self.ui_camera.noidungcamera_line.setStyleSheet(self.khung_style_link)
                        self.ui_camera.noidungcamera_line.setCursor(Qt.PointingHandCursor)
                        self.ui_camera.noidungcamera_line.mousePressEvent = lambda e, url=data: self.mo_web_an_toan(url)
                    else:
                        self.ui_camera.noidungcamera_line.setStyleSheet(self.khung_style_goc)
                    
                    self.timer.stop(); break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.ui_camera.mayanh_lb.setPixmap(QPixmap.fromImage(qimg).scaled(self.ui_camera.mayanh_lb.width(), self.ui_camera.mayanh_lb.height(), Qt.KeepAspectRatio))

    def quet_tu_anh(self):
        path, _ = QFileDialog.getOpenFileName(self.window_quetanh, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path: return
        img = cv2.imread(path)
        if img is None: return

        self.xoa_quetanh()
                
        self.ui_quetanh.qrbarcode1_lb.setPixmap(QPixmap(path).scaled(self.ui_quetanh.qrbarcode1_lb.width(), self.ui_quetanh.qrbarcode1_lb.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        codes = pyzbar.decode(img)
        if not codes: codes = pyzbar.decode(cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5))
        
        if codes:
            code = codes[0]
            data = code.data.decode("utf-8")
            (x, y, w, h) = code.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 6)
            self.hien_thi_ket_qua_anh(img, data, code.type)
        else:
            QMessageBox.warning(self.window_quetanh, "Thất bại", "Không tìm thấy mã")

    def hien_thi_ket_qua_anh(self, img_result, data, ctype):
        self.ui_quetanh.loaima_lb.setText(f"{ctype}")
        self.ui_quetanh.noidunganh_line.setText(data)
        if data.startswith("http"):
            self.ui_quetanh.noidunganh_line.setStyleSheet(self.khung_style_link)
            self.ui_quetanh.noidunganh_line.setCursor(Qt.PointingHandCursor)
            self.ui_quetanh.noidunganh_line.mousePressEvent = lambda e, url=data: self.mo_web_an_toan(url)
        else:
            self.ui_quetanh.noidunganh_line.setStyleSheet(self.khung_style_goc)
            self.ui_quetanh.noidunganh_line.mousePressEvent = None
            
        rgb = cv2.cvtColor(img_result, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.shape[1]*3, QImage.Format_RGB888)
        self.ui_quetanh.qrbarcode2_lb.setPixmap(QPixmap.fromImage(qimg).scaled(self.ui_quetanh.qrbarcode2_lb.width(), self.ui_quetanh.qrbarcode2_lb.height(), Qt.KeepAspectRatio))

    def run(self): self.window_chinh.show(); sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = UngDungQRCode(); app.run()