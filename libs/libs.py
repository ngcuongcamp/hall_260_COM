import sys
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QDesktopWidget,
    QGraphicsOpacityEffect,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import (
    QThread,
    pyqtSignal,
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
)
import logging
import serial
import datetime
import shutil
import cv2
import time
import os
import numpy as np

# from pyzbar.pyzbar import decode, ZBarSymbol
from pylibdmtx.pylibdmtx import decode
import zxingcpp
import configparser

GUI = sys.path.append("./GUI/")
from GUI.Ui_singel_camera import Ui_MainWindow
from pygrabber.dshow_graph import FilterGraph
from pywinauto.application import Application
import pywinauto
from pywinauto import Desktop
from src.Worker import *
import json
from colorama import Fore, init, AnsiToWin32
