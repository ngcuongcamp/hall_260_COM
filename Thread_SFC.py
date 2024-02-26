from libs.libs import QThread, pyqtSignal, serial
from utilities import config, logger, cmd_printer


#!  SFC Class
class SFCThread(QThread):
    data_received = pyqtSignal(bytes)
    signal_error = pyqtSignal()

    def __init__(self, port, baudrate, timeout=0.009, ref=None):
        super(SFCThread, self).__init__()
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
            cmd_printer("ERROR", f"{e}, Connect SFC Error")

    def send_signal_to_sfc(self, data: str):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(data.strip())

    def run(self):
        try:
            self.connect_serial()
            while self.is_running:
                if self.serial_port and self.serial_port.is_open:
                    data = self.serial_port.readline()

                    if len(data) > 0:
                        if data not in [b"1", b"2"]:
                            cmd_printer("WARNING", "Wrong Signal!")
                            logger.warning("Wrong SFC Signal")
                        else:
                            if self.main_ref.is_processing == False:
                                self.main_ref.is_processing = True
                                self.data_received.emit(data)
                            elif self.main_ref.is_processing:
                                cmd_printer(
                                    "WARNING",
                                    "Received signal sfc when program is processing.",
                                )
                                logger.warning(
                                    "Received signal sfc when program is processing."
                                )
        except Exception as e:
            self.signal_error.emit()
            logger.error(f"Connect SFC Error: {e}")

    def stop(self):
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
