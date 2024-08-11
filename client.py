import socket
import os
import random
import string
import time


'''
זמנים, כל השאלות (איבוד פאקטות - הסתברות), לפי זמנים, לפי מספר...
'''


# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server address
server_address = ('127.0.0.1', 5632)
buffer = b"hello world"

def generate_random_file(filename, size):
    with open(filename, 'wb') as f:
        f.write(os.urandom(size))


def send_file(filename):
    with open(filename, 'rb') as f:
        prob = float(input("what probability of package loss you want to try? \nenter the probability: "))
        print('Sending file to server...')
        the_seq_num = 0
        while True:
            the_data = f.read(4092)
            if not the_data:
                client_socket.sendto(the_data, server_address)
                break
            send_time = time.time()  # Record the time before sending each packet
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data
            if random.random() > prob:  # defining the probability of the data loss
                client_socket.sendto(packet, server_address)
                print('Packet {} sent.'.format(the_seq_num))
                response, _ = client_socket.recvfrom(4096)  # Receive response from server
                print(response)
                recv_time = time.time()  # Record the time after receiving the response
                rtt = recv_time - send_time  # Calculate the round-trip time
            else:
                print("packet lost here", str(the_seq_num))

            the_seq_num += 1
        print('File sent.')


# Generate a random file of 10MB
file_name = 'big_file.txt'
generate_random_file(file_name, 10 * 1024 * 1024)  # 10MB

try:
    send_file(file_name)
    # Receive acknowledgment from server containing list of lost packet sequence numbers
    ack_data, _ = client_socket.recvfrom(4092)
    print(ack_data)
    if ack_data == b'FIN':
        print("received FIN packet - bye-bye:)")
        client_socket.close()
        exit(0)

    lost_packets = [int.from_bytes(ack_data[i:i + 4], byteorder='big') for i in range(0, len(ack_data), 4)]
    # Resend lost packets the same way as above
    print('Resending lost packets:', lost_packets)
    with open(file_name, 'rb') as f:
        for seq_num in lost_packets:
            f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
            data = f.read(4092)
            resend_packet = seq_num.to_bytes(4, byteorder='big') + data
            client_socket.sendto(resend_packet, server_address)
            print('Resent packet {}.'.format(seq_num))
            response_re, _ = client_socket.recvfrom(4096)  # Receive response from server
            print(response_re)
        f.seek(0, 2)
        the_data = f.read(4092)
        if not the_data:
            client_socket.sendto(the_data, server_address)

finally:
    # Close the socket
    client_socket.close()
