import logging
import serial

class TTYHandler(logging.Handler):
    def __init__(self, port='/dev/ttyUSB0'):
        super().__init__()
        self.ser = serial.Serial(port, baudrate=115200)

    def emit(self, record):
        message = self.format(record)
        self.ser.write(message.encode())