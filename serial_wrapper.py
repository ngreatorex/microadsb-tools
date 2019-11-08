#!/usr/bin/env python3
import serial
import logging

class SerialWrapper:
    def __init__(self, port):
        self.port = port
        self.logger = logging.getLogger(__name__)

        self.ser = serial.Serial(self.port, 115200, timeout=0.05)


    def clear_buffer(self):
        self.ser.reset_input_buffer()

    def write(self, string):
        self.write_bytes(string.encode('ASCII'))

    def write_bytes(self, b):
        n = self.ser.write(b)
        self.logger.debug("Wrote %d bytes: %s", n, b)
        return n
    
    def read_raw(self):
        s = self.ser.read(1024)
        self.logger.debug("Read %d bytes: %s", len(s), s)
        return s

    def read_line(self, timeout=-1):
        s = self.ser.read_until(b'\r')
        self.logger.debug("Read %d bytes: %s", len(s), s)
        return s

    def is_open(self):
        return self.ser.is_open

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    s = SerialWrapper('/dev/ttyACM0')
    s.clear_buffer()
    s.write('#43-52\r')
    s.readline()
    while 1:
        s.readline()
