import os
import unittest
from unittest.mock import patch

from server import receive2, receive1, receive3


class TestUDPServer(unittest.TestCase):

    def tearDown(self):
        # Clean up by deleting the test file
        if os.path.exists('test_no_loss.txt'):
            os.remove('test_no_loss.txt')
        if os.path.exists('test_with_loss.txt'):
            os.remove('test_with_loss.txt')

    @patch('socket.socket')
    def test_receive_file_no_loss(self, mock_socket):
        # Simulate receiving packets in sequence without loss
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x01' + b'data2', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x02' + b'data3', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        lost_packets = receive1('test_no_loss.txt', mock_socket_instance)
        with open('test_no_loss.txt', 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'data1data2data3')

    @patch('socket.socket')
    def test_receive_file_with_loss(self, mock_socket):
        # Simulate receiving packets with loss
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x02' + b'data3', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        lost_packets = receive1('test_with_loss.txt', mock_socket_instance)
        self.assertEqual(lost_packets, [1])

        with open('test_with_loss.txt', 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'data1data3')

    @patch('socket.socket')
    def test_receive_file_acknowledgment(self, mock_socket):
        # Simulate acknowledgment handling
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x01' + b'data2', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            receive2('test_ack.txt', mock_socket_instance)
            mock_file().write.assert_any_call(b'data1')
            mock_file().write.assert_any_call(b'data2')
        mock_socket_instance.sendto.assert_any_call(b'ACK ', ('127.0.0.1', 5632))

    @patch('socket.socket')
    def test_receive_file_acknowledgment_loss(self, mock_socket):
        # Simulate acknowledgment handling !!!!!!!!!!!!!!!!
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x02' + b'data3', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            lost_list = receive3('test_ack_loss.txt', mock_socket_instance)
            mock_file().write.assert_any_call(b'data1')
            mock_file().write.assert_any_call(b'data3')

        mock_socket_instance.sendto.assert_any_call(b'ACK ', ('127.0.0.1', 5632))

        self.assertEqual(lost_list, [1])




if __name__ == '__main__':
    unittest.main()
