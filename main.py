import sys
import cv2
import io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

qtcreator_file = "design.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)


class DesignWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(DesignWindow, self).__init__()
        self.setupUi(self)
        self.btn_parcourir.clicked.connect(self.get_image)
        self.DisplayRedChan.clicked.connect(self.showRedChannel)
        self.DisplayGreenChan.clicked.connect(self.showGreenChannel)
        self.DisplayBlueChan.clicked.connect(self.showBlueChannel)
        self.DisplayColorHist.clicked.connect(self.show_HistColor)
        self.DisplayGrayImg.clicked.connect(self.show_UpdatedImgGray)
        self.DisplayGrayHist.clicked.connect(self.show_HistGray)

        self.img = None
        self.imgUpdated = None

    def showDimensions(self):
        if self.img is not None:
            h, w, c = self.img.shape
            self.Dimensions.setText(
                f"Hauteur : {h}\n"
                f"Largeur : {w}\n"
                f"Nombre de canaux : {c}"
            )

    def convert_cv_qt(self, cv_image):
        if len(cv_image.shape) == 2:
            display_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
        else:
            display_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        h, w, ch = display_image.shape
        bytes_per_line = ch * w

        q_img = QtGui.QImage(display_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        return QPixmap.fromImage(q_img.copy())

    def display_scaled_image(self, cv_image, label):
        qt_img = self.convert_cv_qt(cv_image)
        scaled_img = qt_img.scaled(label.width(), label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_img)

    def get_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.img = cv2.imread(file_path)
            self.display_scaled_image(self.img, self.OriginalImg)
            self.showDimensions()

    def showRedChannel(self):
        if self.img is not None:
            red_img = self.img.copy()
            red_img[:, :, 0] = 0
            red_img[:, :, 1] = 0
            self.display_scaled_image(red_img, self.RedChannel)

    def showGreenChannel(self):
        if self.img is not None:
            green_img = self.img.copy()
            green_img[:, :, 0] = 0
            green_img[:, :, 2] = 0
            self.display_scaled_image(green_img, self.GreenChannel)

    def showBlueChannel(self):
        if self.img is not None:
            blue_img = self.img.copy()
            blue_img[:, :, 1] = 0
            blue_img[:, :, 2] = 0
            self.display_scaled_image(blue_img, self.BlueChannel)

    def getContrast(self):
        try:
            text_val = self.Contrast.toPlainText().strip().replace(',', '.')
            val = float(text_val) if text_val != "" else 1.0
            return val
        except (ValueError, AttributeError):
            return 1.0

    def getBrightness(self):
        try:
            text_val = self.Brightness.toPlainText().strip().replace(',', '.')
            val = float(text_val) if text_val != "" else 0.0
            return val
        except (ValueError, AttributeError):
            return 0.0

    def show_UpdatedImgGray(self):
        if self.img is not None:
            alpha = self.getContrast()
            beta = self.getBrightness()
            self.Contrast.setPlainText(str(round(alpha, 2)))
            self.Brightness.setPlainText(str(round(beta, 2)))

            img_gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            self.imgUpdated = cv2.convertScaleAbs(img_gray, alpha=alpha, beta=beta)
            self.display_scaled_image(self.imgUpdated, self.GrayImg)

    def calc_HistGray(self):
        if self.imgUpdated is not None:
            return cv2.calcHist([self.imgUpdated], [0], None, [256], [0, 256])
        return None

    def makeFigure(self, hist_list, color_list, target_widget):
        try:
            plt.close('all')
            fig, ax = plt.subplots(figsize=(6, 2))

            for hist, col in zip(hist_list, color_list):
                ax.plot(hist, color=col)

            ax.set_xlim([0, 256])
            fig.tight_layout(pad=0.2)

            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05)
            buf.seek(0)
            plt.close(fig)

            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())

            width = max(target_widget.width(), 100)
            height = max(target_widget.height(), 50)

            scaled_pixmap = pixmap.scaled(
                width,
                height,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            target_widget.setPixmap(scaled_pixmap)

        except Exception as e:
            print(f"Erreur lors de l'affichage de l'histogramme : {e}")

    def show_HistColor(self):
        if self.img is not None:
            if len(self.img.shape) < 3 or self.img.shape[2] < 3:
                return

            hist_list = []
            colors = ('b', 'g', 'r')

            for i in range(3):
                hist = cv2.calcHist([self.img], [i], None, [256], [0, 256])
                hist_list.append(hist)

            self.makeFigure(hist_list, colors, self.ColorHist)

    def show_HistGray(self):
        hist = self.calc_HistGray()
        if hist is not None:
            self.makeFigure([hist], ['black'], self.GrayHist)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DesignWindow()
    window.show()
    sys.exit(app.exec_())