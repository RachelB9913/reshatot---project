import socket
import os
import random
import string
import time


# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server address
server_address = ('127.0.0.1', 5632)
buffer = b"hello world"


def generate_random_file(filename, size):
    with open(filename, 'wb') as f:
        f.write(os.urandom(size))


def send_file_packet(filename):
    with open(filename, 'rb') as f:
        # prob = float(input("what probability of package loss you want to try? \nenter the probability: "))
        print('Sending file to server...')
        the_seq_num = 0
        while True:
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
                break
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data
            # if random.random() > prob:  # defining the probability of the data loss
            client_socket.sendto(packet, server_address)
            #    response, _ = client_socket.recvfrom(4096)  # Receive response from server
            time.sleep(0.00001)  # Delay

            the_seq_num += 1
        print('File sent - packet number based.')
        client_socket.sendto(b'NO', server_address)


def send_file_time(filename):
    with open(filename, 'rb') as f:
        prob = float(input("what probability of package loss you want to try? \nenter the probability: "))
        print('Sending file to server...')
        the_seq_num = 0
        lost_by_time = []
        client_socket.settimeout(0.001)  # Set a timeout of 0.05 seconds
        while True:
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
                break
            send_time = time.time()  # Record the time before sending each packet
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data
            if random.random() > prob:  # defining the probability of the data loss
                client_socket.sendto(packet, server_address)
            try:
                response, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
            except socket.timeout:
                lost_by_time.append(the_seq_num)  # Append the sequence number to lost_by_time list if no ACK received
            the_seq_num += 1
        if len(lost_by_time) >= 1:
            client_socket.sendto(b'YES', server_address)
        else:
            client_socket.sendto(b'NO', server_address)
        return lost_by_time


# Generate a random file of 10MB
file_name = 'big_file.txt'
generate_random_file(file_name, 10 * 1024 * 1024)  # 10MB

try:
    opt = int(input("what method you want to use? 1-seq_num 2-time 3-both? \nenter a number(1,2,3): "))
        if opt == 1:
        send_file_packet(file_name)
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        ack_data, _ = client_socket.recvfrom(4092)
        if ack_data == b'FIN':
            print("received FIN packet")
            client_socket.close()
            exit(0)
        lost_packets = [int.from_bytes(ack_data[i:i + 4], byteorder='big') for i in range(0, len(ack_data), 4)]
        # Resend lost packets the same way as above
        print("len: ", len(lost_packets))
        print('lost by seq num:', lost_packets, '\nresending...')
        with open(file_name, 'rb') as f:
            while len(lost_packets) > 0:
                for seq_num in lost_packets:
                    f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                    data = f.read(4092)
                    resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                    client_socket.sendto(resend_packet, server_address)
                    print('resent: ', seq_num)
                    time.sleep(0.00001)  # Delay
                    # response_re, _ = client_socket.recvfrom(4096)  # Receive response from server
                f.seek(0, 2)  # moves the pointer to the end of the file
                the_data = f.read(4092)
                if not the_data:
                    client_socket.sendto(the_data, server_address)
                response_re, _ = client_socket.recvfrom(4096)  # Receive response from server
                if response_re == b'FIN':
                    print("received FIN packet")
                    client_socket.close()
                    exit(0)
                lost_packets = [int.from_bytes(response_re[i:i + 4], byteorder='big') for i in range(0, len(response_re), 4)]
        print("all the lost packets were sent again")
    if opt == 2:
        lost_by_time = send_file_time(file_name)
        print('File sent - time based.')
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        ack_data, _ = client_socket.recvfrom(4092)
        if ack_data == b'FIN':
            print("received FIN packet")
            client_socket.close()
            exit(0)
        # Resend lost packets the same way as above
        print('lost by time:', lost_by_time, '\nresending...')
        with open(file_name, 'rb') as f:
            for seq_num in lost_by_time:
                f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                data = f.read(4092)
                resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                client_socket.sendto(resend_packet, server_address)
                response_re, _ = client_socket.recvfrom(4096)  # Receive response from server
            f.seek(0, 2)  # moves the pointer to the end of the file
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
        print("all the lost packets were sent again")
    if opt == 3:
        lost_by_time = send_file_time(file_name)
        print('File sent - time and packet number based.')
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        ack_data, _ = client_socket.recvfrom(4092)
        if ack_data == b'FIN':
            print("received FIN packet")
            client_socket.close()
            exit(0)
        lost_packets = [int.from_bytes(ack_data[i:i + 4], byteorder='big') for i in range(0, len(ack_data), 4)]
        all_lost = list(set(lost_packets).union(set(lost_by_time)))
        all_lost.sort()
        # Resend lost packets the same way as above
        print('all packets lost :', all_lost, '\nresending...')
        with open(file_name, 'rb') as f:
            for seq_num in all_lost:
                f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                data = f.read(4092)
                resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                client_socket.sendto(resend_packet, server_address)
                response_re, _ = client_socket.recvfrom(4096)  # Receive response from server
            f.seek(0, 2)  # moves the pointer to the end of the file
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
        print("all the lost packets were sent again")


finally:
    # Close the socket
    client_socket.close()
    print("Client socket closed.\nbye bye :)")
