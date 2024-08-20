import os
import unittest
from unittest.mock import patch, MagicMock
import socket
from client import send_file_time, send_file_packet, generate_random_file


class TestClientFunctions(unittest.TestCase):
    def setUp(self):
        # Set up common test data
        self.file_name = 'test_file.txt'
        self.server_address = ('127.0.0.1', 5632)
        self.test_data = b'Test data for the file' * 1000  # Create a decent amount of test data
        with open(self.file_name, 'wb') as f:
            f.write(self.test_data)

    def tearDown(self):
        # Clean up by deleting the test file
        if os.path.exists(self.file_name):
            os.remove(self.file_name)

    @patch('socket.socket')
    @patch('random.random')
    def test_send_file_packet(self, mock_random, mock_socket):
        mock_socket_inst = mock_socket.return_value
        mock_socket_inst.recvfrom.return_value = (b'ACK', self.server_address)

        # Mock probability to prevent packet loss
        mock_random.side_effect = [0.99] * 10  # Always ensure no packet loss

        with patch('builtins.input', return_value='0.0'):  # No packet loss
            send_file_packet(self.file_name)

        # Ensure the socket sent data
        self.assertTrue(mock_socket_inst.sendto.called)
        self.assertGreater(mock_socket_inst.sendto.call_count, 0)

        # Verify the socket was closed
        mock_socket_inst.close.assert_called_once()

    @patch('socket.socket')
    @patch('random.random')
    def test_send_file_time(self, mock_random, mock_socket):
        mock_socket_inst = mock_socket.return_value
        mock_socket_inst.recvfrom.side_effect = socket.timeout

        # Mock probability to prevent packet loss
        mock_random.side_effect = [0.99] * 10  # Always ensure no packet loss

        with patch('builtins.input', return_value='0.0'):  # No packet loss
            lost_by_time = send_file_time(self.file_name)

        # Since we set socket timeout, lost_by_time should contain all packets
        self.assertGreater(len(lost_by_time), 0)

        # Ensure the socket sent data
        self.assertTrue(mock_socket_inst.sendto.called)
        self.assertGreater(mock_socket_inst.sendto.call_count, 0)

        # Verify the socket was closed
        mock_socket_inst.close.assert_called_once()

    @patch('socket.socket')
    @patch('random.random')
    def test_resend_lost_packets(self, mock_random, mock_socket):
        mock_socket_inst = mock_socket.return_value
        mock_socket_inst.recvfrom.side_effect = [(b'ACK', self.server_address), (b'FIN', self.server_address)]

        # Mock probability to simulate packet loss
        mock_random.side_effect = [0.5] * 10  # 50% chance to lose a packet

        with patch('builtins.input', side_effect=['1', '0.5']):  # Use seq_num method and 50% packet loss
            send_file_packet(self.file_name)

            # Mock receiving lost packets from the server
            lost_packet_seq_nums = [0, 2, 4]
            lost_packet_data = b''.join(num.to_bytes(4, byteorder='big') for num in lost_packet_seq_nums)
            mock_socket_inst.recvfrom.return_value = (lost_packet_data, self.server_address)

            # Resend lost packets and close the socket
            opt = int(input("what method you want to use? 1-seq_num 2-time 3-both? \nenter a number(1,2,3): "))
            if opt == 1:
                send_file_packet(self.file_name)

            self.assertGreater(mock_socket_inst.sendto.call_count, 0)
            mock_socket_inst.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
