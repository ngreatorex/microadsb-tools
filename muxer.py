#!/usr/bin/env python3

from socket_wrapper import SocketWrapper
from serial_wrapper import SerialWrapper
import queue
import logging
import sys

class Muxer:
    def __init__(self, tcp_port=54321, serial_port='/dev/ttyACM0'):
        self.tcp_port = tcp_port
        self.serial_port = serial_port
        self.logger = logging.getLogger(__name__)

        self.sock = SocketWrapper(self.tcp_port)
        self.serial = SerialWrapper(self.serial_port)

    def run(self):
        self.serial.write('#43-52\r')

        while self.sock.is_open() and self.serial.is_open():
            input_queue, output_queue = self.sock.run_once()
            
            while True:
                try:
                    next_msg = input_queue.get_nowait()
                except queue.Empty:
                    break
                else:
                    self.logger.debug("Received message [%s] from network client", next_msg)
                    self.serial.write_bytes(next_msg)

            message = self.serial.read_line()
            if len(message) > 0:
                self.logger.debug("Received message [%s] from serial port", message)
                output_queue.put(message)

if __name__ == "__main__":
    stdout = logging.StreamHandler(stream=sys.stdout)
    stdout.setLevel(logging.DEBUG)
    stderr = logging.StreamHandler(stream=sys.stderr)
    stderr.setLevel(logging.INFO)
    logging.basicConfig(handlers=[stdout, stderr], level=logging.DEBUG)

    m = Muxer()

    m.run()

