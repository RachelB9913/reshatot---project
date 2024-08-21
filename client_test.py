import os
import unittest
from client import send_file_packet, send_file_time, generate_random_file  # Ensure that the client module is imported


class Test(unittest.TestCase):
    def setUp(self):
        # Set up common test data
        self.file_name = 'test_file.txt'
        self.server_address = ('127.0.0.1', 5632)
        self.test_data = b'Test data for the file' * 1000  # Create a decent amount of test data
        self.file_size = 10 * 1024 * 1024
        with open(self.file_name, 'wb') as f:
            f.write(self.test_data)

    def tearDown(self):
        # Clean up by deleting the test file
        if os.path.exists(self.file_name):
            os.remove(self.file_name)

    def test_generate_random_file(self):
        # Test file generation
        generate_random_file(self.file_name, self.file_size)  # creat random file with our function
        self.assertTrue(os.path.exists(self.file_name))  # check that the size and the name is like we wanted
        self.assertEqual(os.path.getsize(self.file_name), self.file_size)
        os.remove(self.file_name)  # Clean up

    def test_send_file_packet(self):
        print('test_send_file_packet')
        # Test sending a file with packet loss based on sequence number
        file_name = 'test_file.txt'
        generate_random_file(file_name, 10 * 1024 * 1024)  # creat 10MB file
        send_file_packet(file_name, self.server_address)  # call the function and send the server address

        # Check if the file was received correctly and the size is at list 10MB
        self.assertTrue(os.path.exists('received_file.txt'))
        self.assertLessEqual(os.path.getsize(file_name), os.path.getsize('received_file.txt'))

    def test_send_file_time(self):
        print('test_send_file_time')
        print('please be patient it takes some time..')
        # Test sending a file with packet loss based on time
        file_name = 'test_file.txt'
        generate_random_file(file_name, 10 * 1024 * 1024)  # creat 10MB file
        lost_by_time = send_file_time(file_name, self.server_address)  # call the function and send the server address

        # Check if the file was received correctly and the size is at list 10MB
        self.assertTrue(os.path.exists('received_file.txt'))
        self.assertLessEqual(os.path.getsize(file_name), os.path.getsize('received_file.txt'))


if __name__ == '__main__':
    unittest.main()
