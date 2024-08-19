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
        print('Sending file to server...')
        the_seq_num = 0 # counter for the seq num
        while True:
            the_data = f.read(4092) #read the next packets
            if not the_data:
                client_socket.sendto(the_data, server_address) # if the data end so sending empty packet
                break
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data # create the pacet wuth the seq num
            client_socket.sendto(packet, server_address)
            time.sleep(0.00001)  # Delay
            the_seq_num += 1
        print('File sent - packet number based.')
        client_socket.sendto(b'NO', server_address) # no packets where lost by time


def send_file_time(filename):
    with open(filename, 'rb') as f:
        print('Sending file to server...')
        the_seq_num = 0
        lost_by_time = []
        client_socket.settimeout(0.0001)  # Set a timeout of 0.005 seconds
        while True:
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
                break
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data
            client_socket.sendto(packet, server_address)
            try:
                response, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
            except socket.timeout:
                lost_by_time.append(the_seq_num)  # Append the sequence number to lost_by_time list if no ACK received
            the_seq_num += 1
        print('File sent - time based.')
        if len(lost_by_time) >= 1:
            client_socket.sendto(b'YES', server_address)
            print("'YES' was sent - ", len(lost_by_time), " packets were lost")
        else:
            client_socket.sendto(b'NO', server_address)
            print("NO was sent")
    return lost_by_time


# Generate a random file of 10MB
file_name = 'big_file.txt'
generate_random_file(file_name, 10 * 1024 * 1024)  # 10MB

try:
    opt = int(input("what method you want to use? 1-seq_num 2-time 3-both? \nenter a number(1,2,3): "))
    start_time = time.time()
    if opt == 1:
        client_socket.sendto(b'1', server_address)
        send_file_packet(file_name)
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        ack_data, _ = client_socket.recvfrom(4092)
        if ack_data == b'FIN': # there is no lost packets
            print("received FIN packet")
            client_socket.close()
            exit(0)
        lost_packets = [int.from_bytes(ack_data[i:i + 4], byteorder='big') for i in range(0, len(ack_data), 4)]
        # Resend lost packets the same way as above
        print('lost by seq num:', lost_packets, '\nresending...')
        with open(file_name, 'rb') as f:
            while len(lost_packets) > 0:  # while there is no lost packets
                for seq_num in lost_packets:
                    f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                    data = f.read(4092)
                    resend_packet = seq_num.to_bytes(4, byteorder='big') + data  # creat the packet
                    client_socket.sendto(resend_packet, server_address)
                    time.sleep(0.00001)  # Delay
                f.seek(0, 2)  # moves the pointer to the end of the file
                the_data = f.read(4092)
                if not the_data:
                    client_socket.sendto(the_data, server_address) # send the empty packet
                response_re, _ = client_socket.recvfrom(4096)  # Receive response from server fin or the lost packets
                if response_re == b'FIN':
                    print("received FIN packet")
                    client_socket.close()
                    exit(0)
                lost_packets = [int.from_bytes(response_re[i:i + 4], byteorder='big') for i in range(0, len(response_re), 4)]
                print('the lost packets: ', lost_packets)
        print("all the lost packets were sent again")
    if opt == 2:
        client_socket.sendto(b'2', server_address)
        lost_by_time = send_file_time(file_name)
        # Receive acknowledgment from server containing list of lost packet by time
        client_socket.settimeout(0.05)  # Set a timeout of 0.005 seconds
        try:
            ack_data, _ = client_socket.recvfrom(4092)
        except socket.timeout:
            print("here")
        if ack_data == b'FIN':
            print("Received FIN packet")
        elif ack_data == b'LOST':
            print("Received 'LOST' packet")
            los = b'GOT-LOST'
            client_socket.sendto(los, server_address)
            # Resend lost packets`
            print('Lost by time:', lost_by_time, '\nResending...')
            with open(file_name, 'rb') as f:
                for seq_num in lost_by_time:
                    # Retry logic for each lost packet
                    retries = 3  # Number of retries for each lost packet
                    while retries > 0:
                        f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                        data = f.read(4092)
                        resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                        client_socket.sendto(resend_packet, server_address)
                        try:
                            response_re, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
                            if response_re == b'ACK':
                                break  # Exit the retry loop if ACK is received
                        except socket.timeout:
                            retries -= 1  # Decrement retry count if ACK not received
                    if retries == 0:
                        print(f'Failed to receive ACK for seq_num {seq_num} after multiple retries.')
                # Ensure to handle the end of file
                f.seek(0, 2)  # Move the pointer to the end of the file
                the_data = f.read(4092)
                if not the_data:
                    client_socket.sendto(the_data, server_address)
            print("All lost packets were sent again")
    if opt == 3:
        client_socket.sendto(b'3', server_address)
        lost_by_time = send_file_time(file_name)
        print('File sent - time and packet number based.')
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        client_socket.settimeout(0.05)  # Set a timeout of 0.005 seconds
        try:
            ack_data, _ = client_socket.recvfrom(4092)
        except socket.timeout:
            print("here")
        lost = []
        if ack_data == b'FIN':
            print("received FIN packet")
            client_socket.close()
            exit(0)
        elif ack_data == b'LOST':
            lost, _ = client_socket.recvfrom(4092)
        lost_packets = [int.from_bytes(lost[i:i + 4], byteorder='big') for i in range(0, len(lost), 4)]
        all_lost = list(set(lost_packets).union(set(lost_by_time)))
        all_lost.sort()
        # Resend lost packets the same way as above
        print('all packets lost :', all_lost, '\nresending...')
        with open(file_name, 'rb') as f:
            for seq_num in all_lost:
                # Retry logic for each lost packet
                retries = 3  # Number of retries for each lost packet
                while retries > 0:
                    f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                    data = f.read(4092)
                    resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                    client_socket.sendto(resend_packet, server_address)
                    try:
                        response_re, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
                        if response_re == b'ACK':
                            break  # Exit the retry loop if ACK is received
                    except socket.timeout:
                        retries -= 1  # Decrement retry count if ACK not received
                if retries == 0:
                    print(f'Failed to receive ACK for seq_num {seq_num} after multiple retries.')
            # Ensure to handle the end of file
            f.seek(0, 2)  # Move the pointer to the end of the file
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
        print("all the lost packets were sent again")


finally:
    client_socket.close()  # Close the socket
    end = time.time()
    total_time = end - start_time
    print('the total time it took to send all the file is: ', round(total_time, 5))
    print("Client socket closed.\nbye bye :)")