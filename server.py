import socket
import time

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address
UDP_IP = "127.0.0.1"
UDP_PORT = 5632
server_address = (UDP_IP, UDP_PORT)
server_socket.bind(server_address)

print('UDP server is listening on', server_address)


def receive_file(filename):
    opt, address = server_socket.recvfrom(4096)
    lost_packets = []
    if opt == b'1':
        lost_packets = receive1(filename)
    elif opt == b'2':
        receive2(filename)
    elif opt == b'3':
        lost_packets = receive3(filename)
    recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
    print(recv_packet)
    if recv_packet == b'YES':
        print("Received 'YES' packet from client")
        # lost_packets_agin = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
        server_socket.sendto(b'LOST', address)  # update the client that it is ready to start receiving the lost packets
        print("packets were lost by time - sending 'LOST'")
        if opt == b'3':
            lost_packets_bytes = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
            server_socket.sendto(lost_packets_bytes, address)
        print("waiting for the resent packets...")
        # opening the same file again in order to append to it all the lost data
        with open(filename, 'ab') as f:
            print("file reopened")
            while True:
                recv_re_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
                if not recv_re_packet:
                    break
                data_re = recv_re_packet[4:]
                f.write(data_re)
                message_re = "ACK"
                ack_re = message_re.encode()
                server_socket.sendto(ack_re, address)  # Send acknowledgment back to client
        print('Lost packets by time received successfully.')
    elif not lost_packets:
        print('No packets are lost - file received successfully.')
        server_socket.sendto(b'FIN', address)
    else:
        print("packets were lost by sequence num\nwaiting for the resent packets...")
        # Convert list of lost packet sequence numbers to bytes
        lost_packets_bytes = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
        # Send the list of lost packet sequence numbers back to the client as part of acknowledgment
        server_socket.sendto(lost_packets_bytes, address)
        # opening the same file again in order to append to it all the lost data
        with open(filename, 'ab') as f:
            while True:  # while there is lost packest
                while True:  # whule the client sending
                    recv_re_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
                    if not recv_re_packet:  # the client done to resend
                        break
                    seq_bytes_re = recv_re_packet[:4]  # read the packet
                    data_re = recv_re_packet[4:]
                    seq_num_re = int.from_bytes(seq_bytes_re, byteorder='big')
                    lost_packets.remove(seq_num_re)  # remove from the lost list
                    f.write(data_re)  # write in the data
                if len(lost_packets) > 0:  # if there is lost packets
                    lost_packets_agin = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
                    print('the lost packets are: ', lost_packets)
                    server_socket.sendto(lost_packets_agin, address)  # Send acknowledgment back to client
                else:  # we got all the packets
                    server_socket.sendto(b'FIN', address)
                    break
        print('Lost packets by sequence num received successfully.')


def receive1(filename):
    lost_packets = []  # List to store lost packet sequence numbers
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        expected_seq_num = 0
        while True:
            recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
            if not recv_packet:
                break
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            if seq_num != expected_seq_num:
                # in case of some lost packages in a row add them all to the loss list
                for i in range(seq_num - expected_seq_num):
                    lost_packets.append(expected_seq_num + i)  # Store the sequence number of the lost packet
                expected_seq_num += (seq_num - expected_seq_num)
                # continue  # Skip processing the out-of-order packet
            f.write(data)
            expected_seq_num += 1
    return lost_packets


def receive2(filename):
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        expected_seq_num = 0
        while True:
            recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
            if not recv_packet:
                break
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            f.write(data)
            message = "ACK " + str(seq_num)
            ack = message.encode()
            server_socket.sendto(ack, address)  # Send acknowledgment back to client
            expected_seq_num += 1


def receive3(filename):
    lost_packets = []  # List to store lost packet sequence numbers
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        expected_seq_num = 0
        while True:
            recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
            if not recv_packet:
                break
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            if seq_num != expected_seq_num:
                # in case of some lost packages in a row add them all to the loss list
                for i in range(seq_num - expected_seq_num):
                    lost_packets.append(expected_seq_num + i)  # Store the sequence number of the lost packet
                expected_seq_num += (seq_num - expected_seq_num)
                # continue  # Skip processing the out-of-order packet
            f.write(data)
            message = "ACK " + str(seq_num)
            ack = message.encode()
            server_socket.sendto(ack, address)  # Send acknowledgment back to client
            expected_seq_num += 1
    return lost_packets


receive_file('received_file.txt')  # Receive the file
server_socket.close()
print("Server socket closed.\nbye bye :)")