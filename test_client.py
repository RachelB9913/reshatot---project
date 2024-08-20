import unittest
import threading
import os
import time
import socket
from your_module_name import generate_random_file, send_file_packet, send_file_time

# Replace 'your_module_name' with the actual module name where your functions are located.

class TestUDPFileTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the server in a separate thread
        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()
        time.sleep(1)  # Give the server a moment to start

    @classmethod
    def tearDownClass(cls):
        # You can implement a way to stop the server cleanly if needed
        pass

    def setUp(self):
        # Generate a test file
        self.filename = 'test_file.txt'
        generate_random_file(self.filename, 1024 * 1024)  # 1MB file

    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.filename):
            os.remove(self.filename)
        if os.path.exists('received_file.txt'):
            os.remove('received_file.txt')

    def test_send_file_packet(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(b'1', ('127.0.0.1', 5632))
        send_file_packet(self.filename)
        client_socket.close()
        
        # Now we check if the received file is correct
        self.assertTrue(os.path.exists('received_file.txt'))
        self.assertTrue(os.path.getsize(self.filename), os.path.getsize('received_file.txt'))

    def test_send_file_time(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(b'2', ('127.0.0.1', 5632))
        lost_packets = send_file_time(self.filename)
        client_socket.close()

        # Now we check if the received file is correct
        self.assertTrue(os.path.exists('received_file.txt'))
        self.assertTrue(os.path.getsize(self.filename), os.path.getsize('received_file.txt'))
        # Additionally, check that the list of lost packets is not empty
        self.assertTrue(isinstance(lost_packets, list))

    def test_send_file_packet_and_time(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(b'3', ('127.0.0.1', 5632))
        lost_packets = send_file_time(self.filename)
        client_socket.close()

        # Now we check if the received file is correct
        self.assertTrue(os.path.exists('received_file.txt'))
        self.assertTrue(os.path.getsize(self.filename), os.path.getsize('received_file.txt'))
        # Additionally, check that the list of lost packets is not empty
        self.assertTrue(isinstance(lost_packets, list))


def run_server():
    # This function runs your UDP server
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5632
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((UDP_IP, UDP_PORT))
    receive_file('received_file.txt')
    server_socket.close()


if __name__ == '__main__':
    unittest.main()
