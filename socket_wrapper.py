#!/usr/bin/env python3
import logging
import socket
import select
import queue

class SocketWrapper:
    def __init__(self, port):
        self.port = port
        self.logger = logging.getLogger(__name__)

        # create an INET, STREAMing socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.bind(('', port))
        self.server.listen(5)
        self.logger.info("Listening on port %d...", port)

        self.clients = []

        self.inputs = [self.server]
        self.outputs = []
        self.message_output_queues = {}

        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

    def is_open(self):
        return len(self.inputs) > 0

    def run_loop(self):
        while self.inputs:
            self.run_once()

    def run_once(self):
        while True:
            try:
                msg = self.output_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.logger.debug("Got message to output [%s]", msg)
                for c in self.clients:
                    if c not in self.outputs:
                        self.logger.debug("Appending [%s] to outputs", c)
                        self.outputs.append(c)
                    self.logger.debug("Appending output message to message queue for [%s]", c)
                    self.message_output_queues[c].put(msg)

        if self.inputs:
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, 0.1)
            self.logger.debug("Select returned [%s, %s, %s]", readable, writable, exceptional)

            for s in readable:
                if s is self.server:
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    self.logger.info("Accepted connection from %s", client_address)
                    self.inputs.append(connection)
                    self.clients.append(connection)
                    self.message_output_queues[connection] = queue.Queue()
                else:
                    try:
                        data = s.recv(1024)

                        if data:
                            self.logger.info("Received message [%s] from [%s]", data, s.getpeername())
                            self.input_queue.put(data)
                            #self.message_output_queues[s].put(data)
                            #if s not in self.outputs:
                            #    self.outputs.append(s)
                        else:
                            if s in self.outputs:
                                self.outputs.remove(s)
                            if s in writable:
                                writable.remove(s)
                            self.inputs.remove(s)
                            self.clients.remove(s)
                            self.logger.info("Removed connection [%s]", s)
                            s.close()
                            del self.message_output_queues[s]
                    except:
                        pass

            for s in writable:
                try:
                    next_msg = self.message_output_queues[s].get_nowait()
                except queue.Empty:
                    self.outputs.remove(s)
                else:
                    self.logger.debug("Sending message [%s] to [%s]", next_msg, s)
                    try:
                        s.send(next_msg)
                    except:
                        if s in self.outputs:
                            self.outputs.remove(s)
                        self.inputs.remove(s)
                        self.clients.remove(s)
                        self.logger.info("Removed connection [%s]", s)
                        s.close()
                        del self.message_output_queues[s]
        
            for s in exceptional:
                self.logger.info("Received exception for [%s]", s)
                self.clients.remove(s)
                self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                s.close()
                del self.message_output_queues[s]
            
        return self.input_queue, self.output_queue

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    s = SocketWrapper(54321)
    s.run_loop()


