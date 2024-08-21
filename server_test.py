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
    def test_receive1(self, mock_socket):
        # Simulate receiving packets in sequence without loss
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x01' + b'data2', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x02' + b'data3', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        # call the receive1 function that check by seq num that all the packets arrived, return the lost packets seq num
        lost_packets = receive1('test_no_loss.txt', mock_socket_instance)
        with open('test_no_loss.txt', 'rb') as f:
            content = f.read()
            # check that the data we got contain the data we send
            self.assertEqual(content, b'data1data2data3')

    @patch('socket.socket')
    def test_receive1_loss(self, mock_socket):
        # Simulate receiving packets with loss
        mock_socket_instance = mock_socket.return_value
        # sending 2 packets that their seq num are non-consecutive
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x02' + b'data3', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        # calling the receive1 function and want to get a list that say that packet with seq num 1 is lost
        lost_packets = receive1('test_with_loss.txt', mock_socket_instance)
        self.assertEqual(lost_packets, [1])

        with open('test_with_loss.txt', 'rb') as f:
            content = f.read()
            # check that the data we got contain the data we send
            self.assertEqual(content, b'data1data3')

    @patch('socket.socket')
    def test_receive2(self, mock_socket):
        # Simulate acknowledgment handling
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x01' + b'data2', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        # sent 2 packets and want to check that the data we sent is now in the new file
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            receive2('test_ack.txt', mock_socket_instance)
            mock_file().write.assert_any_call(b'data1')
            mock_file().write.assert_any_call(b'data2')
        # check that we got ack for each packet we sent
        mock_socket_instance.sendto.assert_any_call(b'ACK ', ('127.0.0.1', 5632))

    @patch('socket.socket')
    def test_receive3(self, mock_socket):
        # Simulate acknowledgment handling and packet lost
        mock_socket_instance = mock_socket.return_value
        # sending 2 packets that their seq num are non-consecutive
        mock_socket_instance.recvfrom.side_effect = [
            (b'\x00\x00\x00\x00' + b'data1', ('127.0.0.1', 5632)),
            (b'\x00\x00\x00\x02' + b'data3', ('127.0.0.1', 5632)),
            (b'', ('127.0.0.1', 5632)),  # End of file
        ]
        # in receive3 we look for loss packets by time and seq num so we combin the last 2 tests
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            lost_list = receive3('test_ack_loss.txt', mock_socket_instance)
            # check that the data i in the new file
            mock_file().write.assert_any_call(b'data1')
            mock_file().write.assert_any_call(b'data3')
        # check that we sent ack for each packet
        mock_socket_instance.sendto.assert_any_call(b'ACK ', ('127.0.0.1', 5632))
        # check that the function realize that we "lost" packet with seq num 1
        self.assertEqual(lost_list, [1])


if __name__ == '__main__':
    unittest.main()
