from libs.libs import QThread, pyqtSignal, serial
from src.utilities import config, logger, cmd_printer

#!  PLC Class


class PLCThread(QThread):
    data_received = pyqtSignal(bytes)
    signal_error = pyqtSignal()

    def __init__(self, port, baudrate, timeout=0.009, ref=None):
        super(PLCThread, self).__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_running = False
        self.main_ref = ref

    def connect_serial(self):
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            self.is_running = True
        except Exception as e:
            cmd_printer("ERROR", f"{e}, Connect PLC Error")

    def send_signal_to_plc(self, data: str):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(data.strip())

    def run(self):
        try:
            self.connect_serial()
            while self.is_running:
                if self.serial_port and self.serial_port.is_open:
                    data = self.serial_port.readline()

                    if len(data) > 0:
                        # SCAN_SIGNAL = config["PLC_SIGNALS"]["SCAN_SIGNAL"].encode(
                        #     "utf-8"
                        # )
                        # RESET_SIGNAL = config["PLC_SIGNALS"]["RESET_SIGNAL"].encode(
                        #     "utf-8"
                        # )

                        if data not in [b"1", b"2"]:
                            cmd_printer("WARNING", "Wrong Signal!")
                            logger.warning("Wrong PLC Signal")
                        else:
                            if self.main_ref.is_processing == False:
                                self.main_ref.is_processing = True
                                self.data_received.emit(data)
                            elif self.main_ref.is_processing:
                                cmd_printer(
                                    "WARNING",
                                    "Received signal PLC when program is processing.",
                                )
                                logger.warning(
                                    "Received signal PLC when program is processing."
                                )
        except Exception as e:
            self.signal_error.emit()
            logger.error(f"Connect PLC Error: {e}")

    def stop(self):
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
