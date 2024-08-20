import os
import threading
import unittest
import socket
import time
# from server import receive_file
from client import send_file_time, send_file_packet, generate_random_file # Ensure that the client module is imported


class Test(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls):
    #     # Create a server instance and start it in a separate thread
    #     cls.server_address = ('127.0.0.1', 5632)
    #     cls.server_thread = threading.Thread(target=receive_file, args=('received_file.txt',))
    #     cls.server_thread.daemon = True
    #     cls.server_thread.start()
    #     time.sleep(1)  # Allow time for server to start
    #
    #
    # def setUp(self):
    #     # Create a client socket
    #     self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #
    # def tearDown(self):
    #     # Clean up
    #     if os.path.exists('test_file.txt'):
    #         os.remove('test_file.txt')
    #     if os.path.exists('received_file.txt'):
    #         os.remove('received_file.txt')
    #     self.client_socket.close()

    def setUp(self):
        self.server_address = ('127.0.0.1', 5632)
        self.file_name = 'test_file.txt'
        self.file_size = 1024 * 1024  # 1MB for testing

    def test_generate_random_file(self):
        # Test file generation
        generate_random_file(self.file_name, self.file_size)
        self.assertTrue(os.path.exists(self.file_name))
        self.assertEqual(os.path.getsize(self.file_name), self.file_size)
        os.remove(self.file_name)  # Clean up

    def test_send_file_packet(self):
        print('test_send_file_packet')
        # Test sending a file with packet loss based on sequence number
        file_name = 'test_file.txt'
        generate_random_file(file_name, 1024 * 1024)  # 1MB file
        send_file_packet(file_name, self.server_address)

        # Check if the file was received correctly
        self.assertTrue(os.path.exists('received_file.txt'))
        self.assertEqual(os.path.getsize(file_name), os.path.getsize('received_file.txt'))

    # def test_send_file_time(self):
    #     print('test_send_file_time')
    #     # Test sending a file with packet loss based on time
    #     file_name = 'test_file.txt'
    #     generate_random_file(file_name, 1024 * 1024)  # 1MB file
    #     lost_by_time = send_file_time(file_name, self.server_address)
    #
    #     # Check if the file was received correctly
    #     self.assertTrue(os.path.exists('received_file.txt'))
    #     self.assertEqual(os.path.getsize(file_name), os.path.getsize('received_file.txt'))
    #
    #     # Optionally, check the lost packets if needed
    #     # self.assertGreater(len(lost_by_time), 0)  # Example: Check if there were lost packets


if __name__ == '__main__':
    unittest.main()
