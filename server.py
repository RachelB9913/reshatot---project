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
    lost_packets = []  # List to store lost packet sequence numbers
    losi = 0
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        expected_seq_num = 0
        while True:
            recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
            if not recv_packet:
                break
            recv_time = time.time()  # Record the time when a packet is received
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            if seq_num != expected_seq_num:
                # in case of some lost packages in a row add them all to the loss list
                for i in range(seq_num - expected_seq_num):
                    lost_packets.append(expected_seq_num + i)  # Store the sequence number of the lost packet
                losi += 1
                expected_seq_num += (seq_num - expected_seq_num)
                # continue  # Skip processing the out-of-order packet
            f.write(data)
            message = "ACK " + str(seq_num)
            ack = message.encode()
            server_socket.sendto(ack, address)  # Send acknowledgment back to client
            send_time = time.time()  # Record the time after sending the acknowledgment
            rtt = send_time - recv_time  # Calculate the round-trip time
            expected_seq_num += 1
    recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
    if recv_packet == b'YES':
        # Convert list of lost packet sequence numbers to bytes
        lost_packets_bytes = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
        # Send the list of lost packet sequence numbers back to the client as part of acknowledgment
        server_socket.sendto(lost_packets_bytes, address)
        # opening the same file again in order to append to it all the lost data
        print("packets were lost by time\nwaiting for the resent packets...")
        with open(filename, 'ab') as f:
            while True:
                recv_re_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
                if not recv_re_packet:
                    break
                seq_bytes_re = recv_re_packet[:4]
                data_re = recv_re_packet[4:]
                seq_num_re = int.from_bytes(seq_bytes_re, byteorder='big')
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
            while True:
                while True:
                    recv_re_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
                    if not recv_re_packet:
                        break  # from the small loop because this send over
                    seq_bytes_re = recv_re_packet[:4]
                    data_re = recv_re_packet[4:]
                    seq_num_re = int.from_bytes(seq_bytes_re, byteorder='big')
                    lost_packets.remove(seq_num_re)  # remove the num we got from the lost list
                    f.write(data_re)
                if len(lost_packets) > 0:  # there is more packets we didn't got yet
                    lost_packets_agin = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
                    server_socket.sendto(lost_packets_agin, address)  # Send acknowledgment back to client
                else:
                    server_socket.sendto(b'FIN', address)
                    break  # from the big loop because we didn't loss packets
        print('Lost packets by sequence num received successfully.')


# while True:
receive_file('received_file.txt')  # Receive the file
server_socket.close()
print("Server socket closed.\nbye bye :)")
