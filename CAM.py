from libs.libs import *
from utilities import *
from Thread_PLC import PLCThread
from Thread_Camera import CameraThread
from Thread_SFC import SFCThread
from connect_mes import *
from reader import *
from UI_handler import *


class MyApplication(QMainWindow):
    frame1 = None
    data_scan1 = None
    graph = FilterGraph()
    thread_pool = QThreadPool()

    def __init__(self):
        super().__init__()
        self.is_update_cam_error = True
        self.is_processing = False
        initial_UI_MainWindow(self)  # initialize UI
        read_config(self)  # read config

        # thread CAMERA
        self.open_camera_thread()
        self.check_error_camera = QTimer()
        self.check_error_camera.timeout.connect(self.reconnect_camera_thread)
        self.check_error_camera.start(1000)

        # thread PLC
        self.THREAD_PLC = PLCThread(
            self.COM_PLC, self.BAUDRATE_PLC, timeout=0.009, ref=self
        )
        self.THREAD_PLC.start()
        self.THREAD_PLC.data_received.connect(self.handle_signal_plc)

        # thread SFC
        self.THREAD_SFC = SFCThread(
            self.COM_SFC, self.BAUDRATE_SFC, timeout=0.009, ref=self
        )
        self.THREAD_SFC.start()

        # SFC RC
        self.THREAD_SFC_RC = SFCThread(
            self.COM_SFC_RC, self.BAUDRATE_SFC, timeout=0.009, ref=self
        )
        self.THREAD_SFC_RC.start()
        self.THREAD_SFC_RC.data_received.connect(self.handle_signal_sfc)

    def handle_click_update(self, event):
        req = QMessageBox.question(
            self,
            "Confirm Update",
            "Do you want to update latest version?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if req == QMessageBox.Yes:
            print("Handler update function here...")
            req3 = QMessageBox.warning(
                self, "Infomation", "Not found latest version!", QMessageBox.Cancel
            )
        else:
            print("Ignore update")

    # handle plc signal
    def handle_signal_plc(self, data):
        if self.THREAD_CAMERA_1.is_running:
            if data == b"1":
                print("\n\n------ SCAN SIGNAL -------")
                logger.info("\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                logger.info("--> Received scan signal from PLC")
                logger.info("--> ------ SCAN SIGNAL -------")
                try:
                    self.worker = Worker(self.scan_product_code)
                    MyApplication.thread_pool.start(self.worker)
                except Exception as E:
                    print(E)
            if data == b"2":
                print("---------------\nRESET")
                set_reset_state(self)
                self.set_default_variables()
                self.is_processing = False
        else:
            print(f"Error: Received signal when the camera is not connected")
            print(f"Signal PLC: {data}")

    def handle_signal_sfc(self, data):
        if self.THREAD_CAMERA_1.is_running:
            print("------ SFC RESPONSE -------")
            print("\n\n")
            logger.info("------ SFC RESPONSE -------")
            if data == b"1":
                self.is_processing = False
                logger.info("--> Received pass signal from SFC")
                cmd_printer("SUCCESS", "--> Received pass signal from SFC")
                self.THREAD_PLC.send_signal_to_plc(b"1")
                print("Send pass reponse to PLC")
                set_state_pass(self)
            if data == b"2":
                self.is_processing = False
                cmd_printer("ERROR", "--> Received pass signal from SFC")
                logger.error("--> Received fail signal from SFC")

                self.THREAD_PLC.send_signal_to_plc(b"2")
                print("Send fail reponse to PLC")
                set_fail_state(self)

        else:
            print(f"Error: Received signal when the camera is not connected")
            print(f"Signal SFC: {data}")

    def scan_product_code(self):
        set_default_state(self)
        self.set_default_variables()
        i = 0
        stime = time.time()
        while i < self.SCAN_LIMIT:
            i = i + 1
            gray_frame = process_frame(frame=self.frame1)
            self.data_scan1 = read_dmt_zxingcpp(gray_frame)
            if self.data_scan1:
                break
            if self.data_scan1 is None:
                processed = process_frame(frame=self.frame1)
                self.data_scan1 = read_dmt_loop(self, processed)
                if self.data_scan1:
                    break

        print("--> RESULT SCAN")
        logger.info("--> RESULT SCAN")
        print(f"-----> spends {round(time.time() - stime,3)}s to read code")

        # IF FAIL SCAN
        if self.data_scan1 is None:
            print("FAILED")
            logger.error("FAILED")
            self.THREAD_PLC.send_signal_to_plc(b"2")

            self.is_processing = False
            if self.IS_SAVE_NG_IMAGE == 1:
                if self.data_scan1 is None:
                    image_filename = "image_NG/{}/{}.png".format(
                        get_current_date(), format_current_time()
                    )
                    cv2.imwrite(image_filename, self.frame1)

            logger.error("------FAIL SCAN-------")

            logger.error(f"Data : {self.data_scan1}")

            print("------FAIL SCAN-------")
            print(f"Data : {self.data_scan1}")
            set_fail_state(self)

        # IF PASS SCAN
        if self.data_scan1 is not None:
            self.is_processing = False
            cmd_printer("SUCCESS", "PASS SCAN")
            logger.info("PASS SCAN")
            print(f"Data : {self.data_scan1}")

            print("----------- SEND TO SFC -----------")
            logger.info("----------- SEND TO SFC -----------")
            self.THREAD_SFC.send_signal_to_sfc(self.data_scan1.encode("utf-8"))
            print("Send data to SFC:  ", self.data_scan1)
            logger.info(f"Send data to SFC: {self.data_scan1} ")

    def set_default_variables(self):
        self.data_scan1 = None

    def display_frame1(self, frame):
        self.frame1 = frame
        frame_zoom_out = cv2.resize(frame, (320, 240))
        frame_rgb = cv2.cvtColor(frame_zoom_out, cv2.COLOR_BGR2RGB)
        img = QImage(
            frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], QImage.Format_RGB888
        )
        scaled_pixmap = img.scaled(self.Uic.CameraFrame1.size())
        pixmap = QPixmap.fromImage(scaled_pixmap)
        self.Uic.CameraFrame1.setPixmap(pixmap)

    def closeEvent(self, event):
        req = QMessageBox.question(
            self,
            "Confirm Close",
            "Do you want to close the application?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if req == QMessageBox.Yes:
            event.accept()
            self.THREAD_CAMERA_1.stop()
            self.THREAD_PLC.stop()
            self.THREAD_SFC.stop()
            self.THREAD_SFC_RC.stop()
            print("--------------\nCLOSE")

            # Close Camera and release
            if self.THREAD_CAMERA_1.isRunning():
                self.THREAD_CAMERA_1.wait()
                self.THREAD_CAMERA_1.cap.release()
            cv2.destroyAllWindows()
        else:
            event.ignore()

    def update_status_camera_error(self):
        self.is_update_cam_error = True
        if self.is_update_cam_error:
            logger.error(f"CAM ERROR")
            self.is_update_cam_error = False
        set_error_camera_state(self)

    def open_camera_thread(self):
        self.THREAD_CAMERA_1 = CameraThread(self.ID_C1)
        self.THREAD_CAMERA_1.frame_received.connect(self.display_frame1)
        self.THREAD_CAMERA_1.start()
        # if self.IS_OPEN_CAM_PROPS == 1:
        #     self.THREAD_CAMERA_1.cap.set(cv2.CAP_PROP_SETTINGS, 1)
        self.THREAD_CAMERA_1.update_error_signal.connect(
            self.update_status_camera_error
        )

        set_default_state(self)
        self.set_default_variables()

    def reconnect_camera_thread(self):
        try:
            if (
                len(self.graph.get_input_devices()) == self.NUM_CAMERA
                and not self.THREAD_CAMERA_1.is_running
            ):
                self.open_camera_thread()
        except Exception as E:
            print(E)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApplication()
    sys.exit(app.exec_())
