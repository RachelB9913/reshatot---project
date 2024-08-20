import socket

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address
UDP_IP = "127.0.0.1"
UDP_PORT = 5632
server_address = (UDP_IP, UDP_PORT)
server_socket.bind(server_address)

print('UDP server is listening on', server_address)


def receive_file(filename):
    # get from the client the option he chose to check and receive the data correspond to the option
    opt, address = server_socket.recvfrom(4096)
    lost_packets = []
    if opt == b'1':
        lost_packets = receive1(filename)
    elif opt == b'2':
        receive2(filename)
    elif opt == b'3':
        lost_packets = receive3(filename)
    recv_packet, address = server_socket.recvfrom(4096)  # get if there was lost of packets by time
    print(recv_packet)
    # if there waa lost packets by time so send them agin till all th packets will arrive
    if recv_packet == b'YES':
        print("Received 'YES' from client")
        server_socket.sendto(b'LOST', address)  # update the client that it is ready to start receiving the lost packets
        print("packets were lost by time - sending 'LOST'")
        if opt == b'3':
            # if we are in option 3 we need to combine the two list (send the seq num lost list)
            lost_packets_bytes = b''.join(seq_num.to_bytes(4, byteorder='big') for seq_num in lost_packets)
            server_socket.sendto(lost_packets_bytes, address)
        print("waiting for the resent packets...")
        # opening the same file again in order to append to it all the lost data
        with open(filename, 'ab') as f:
            print("file reopened...")
            while True:
                recv_re_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
                if not recv_re_packet:  # when we finish to send the file we send empty packet
                    break
                # read the data without the seq num and write it
                data_re = recv_re_packet[4:]
                f.write(data_re)
                # send an ack message to the client
                message_re = "ACK"
                ack_re = message_re.encode()
                server_socket.sendto(ack_re, address)  # Send acknowledgment back to client
        print('Lost packets by time received successfully.')
    # there is no lost packets at all
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
            while True:  # while there is lost packets
                while True:  # while the client sending
                    recv_re_packet, address = server_socket.recvfrom(4096)  # receive packet
                    if not recv_re_packet:  # the client done to resend
                        break
                    seq_bytes_re = recv_re_packet[:4]  # read the packet seq num and data apart
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


def receive1(filename, *args):  # receive packets when we chose option 1
    global server_socket
    if len(args) >= 1:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address2 = ("127.0.0.1", 5632)
        server_socket.bind(server_address2)
    lost_packets = []  # List to store lost packet sequence numbers
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        expected_seq_num = 0  # counter that check which number we should get now
        while True:
            recv_packet, address = server_socket.recvfrom(4096)
            if not recv_packet:
                break
            # read the data
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            # check that we got what we wanted to get
            if seq_num != expected_seq_num:
                # in case of some lost packages in a row add them all to the loss list
                for i in range(seq_num - expected_seq_num):
                    lost_packets.append(expected_seq_num + i)  # Store the sequence number of the lost packet
                expected_seq_num += (seq_num - expected_seq_num)
            # writing the data and keep going to the next one
            f.write(data)
            expected_seq_num += 1
    # return the list of all the lost packets
    return lost_packets


def receive2(filename, *args):  # receive packets when we chose option 2
    global server_socket
    if len(args) >= 1:
        server_socket = args[0]
        server_address2 = ("127.0.0.1", 5632)
        server_socket.bind(server_address2)
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        # star getting packets
        while True:
            recv_packet, address = server_socket.recvfrom(4096)  # Buffer size is 4096 bytes
            if not recv_packet:  # if we got empty packets its mean that the client sent all the file
                break
            # read and write the data and take out the seq num
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            f.write(data)
            message = "ACK "  # + str(seq_num)
            # on our wireshark run we sent the seq num as well in the ack message, so it is longer
            ack = message.encode()
            server_socket.sendto(ack, address)  # Send acknowledgment back to client


def receive3(filename, *args):  # receive packets when we chose option 3
    global server_socket
    if len(args) >= 1:
        server_socket = args[0]
        server_address2 = ("127.0.0.1", 5632)
        server_socket.bind(server_address2)
    lost_packets = []  # List to store lost packet sequence numbers
    with open(filename, 'wb') as f:
        print('\nWaiting to receive file from client...')
        expected_seq_num = 0  # counter that tell as which seq num we are waiting for
        while True:
            recv_packet, address = server_socket.recvfrom(4096)  # getting packets
            if not recv_packet:  # when the client finish to send the file he sends empty packets
                break
            # read the data
            seq_bytes = recv_packet[:4]
            data = recv_packet[4:]
            seq_num = int.from_bytes(seq_bytes, byteorder='big')
            # check if we got what we expected
            if seq_num != expected_seq_num:
                # in case of some lost packages in a row add them all to the loss list
                for i in range(seq_num - expected_seq_num):
                    lost_packets.append(expected_seq_num + i)  # Store the sequence number of the lost packet
                expected_seq_num += (seq_num - expected_seq_num)
            f.write(data)
            message = "ACK "  # + str(seq_num)
            # on our wireshark run we sent the seq num as well in the ack message, so it is longer
            ack = message.encode()
            server_socket.sendto(ack, address)  # Send acknowledgment back to client
            expected_seq_num += 1
    return lost_packets  # return the lost by seq num


receive_file('received_file.txt')  # Receive the file
server_socket.close()
print("Server socket closed.\nbye bye :)")
