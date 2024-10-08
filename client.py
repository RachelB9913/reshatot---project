import socket
import os
# import sys
import time

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server address
server_address = ('127.0.0.1', 5632)


def generate_random_file(filename, size):
    # creat new file with the name and size given
    with open(filename, 'wb') as n:
        n.write(os.urandom(size))


def send_file_packet(filename, *args):
    # sending the data while looking for packets that lost by seq num
    global server_address, client_socket  # define address and socket for the tests
    if len(args) == 1:
        server_address = args[0]
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with open(filename, 'rb') as r:
        print('Sending file to server...')
        the_seq_num = 0  # counter for the seq num
        while True:
            the_data = r.read(4092)  # read the next packets
            if not the_data:
                client_socket.sendto(the_data, server_address)  # if the data end so sending empty packet
                break
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data  # create the packet with the seq num
            client_socket.sendto(packet, server_address)
            time.sleep(0.00001)  # Delay so won't crush
            the_seq_num += 1
        print('File sent - packet number based.')
        client_socket.sendto(b'NO', server_address)  # no packets where lost by time


def send_file_time(filename, *args):
    # sending the data while looking for packets that lost by time
    global server_address, client_socket  # define address and socket for the tests
    if len(args) == 1:
        server_address = args[0]
        if client_socket is None:  # define new socket if it is a test and there isn't one open
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with open(filename, 'rb') as b:
        print('Sending file to server...')
        # define counter a list for the seq num and the los packets
        the_seq_num = 0
        lost_by_time = []
        client_socket.settimeout(0.01)  # Set a timeout of 0.01 seconds
        while True:
            the_data = b.read(4092)
            if not the_data:
                # if we finish sending the file we are sending empty packet
                client_socket.sendto(the_data, server_address)
                break
            packet = the_seq_num.to_bytes(4, byteorder='big') + the_data  # creat the packet with the seq num
            client_socket.sendto(packet, server_address)
            try:
                response, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
            except socket.timeout:
                lost_by_time.append(the_seq_num)  # Append the sequence number to lost_by_time list if no ACK received
            the_seq_num += 1
        print('File sent - time based.')
        if len(lost_by_time) >= 1:  # if there is lost packets by time
            client_socket.sendto(b'YES', server_address)
            print("'YES' was sent - ", len(lost_by_time), " packets were lost")
        else:  # there is no lost packets by time
            client_socket.sendto(b'NO', server_address)
            print("NO was sent")
    return lost_by_time


# Generate a random file of 10MB
file_name = 'big_file.txt'
generate_random_file(file_name, 10 * 1024 * 1024)  # 10MB

try:
    # the user choose which checking of lost packets he wants to run
    opt = int(input("what method you want to use? 1-seq_num 2-time 3-both? \nenter a number(1,2,3): "))
    start_time = time.time()  # the start time for the later checking
    if opt == 1:
        # if the user chose opt 1 so sending this to the server and start sending the file
        client_socket.sendto(b'1', server_address)
        send_file_packet(file_name)
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        ack_data, _ = client_socket.recvfrom(4092)
        if ack_data == b'FIN':  # there is no lost packets so the server sent 'FIN'
            print("received FIN packet")
        # turning the list from byts
        else:
            lost_packets = [int.from_bytes(ack_data[i:i + 4], byteorder='big') for i in range(0, len(ack_data), 4)]
            # Resend lost packets the same way as above
            print('lost by seq num:', lost_packets, '\nresending...')
            with open(file_name, 'rb') as f:
                while len(lost_packets) > 0:  # while there is no lost packets
                    for seq_num in lost_packets:  # for all the seq num of the packets where lost
                        f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                        data = f.read(4092)
                        resend_packet = seq_num.to_bytes(4, byteorder='big') + data  # creat the packet
                        client_socket.sendto(resend_packet, server_address)
                        time.sleep(0.00001)  # Delay so won't crush
                    f.seek(0, 2)  # moves the pointer to the end of the file
                    the_data = f.read(4092)
                    if not the_data:
                        client_socket.sendto(the_data, server_address)  # send the empty packet
                    response_re, _ = client_socket.recvfrom(4096)  # Receive response from server fin or the lost packets
                    if response_re == b'FIN':
                        print("received FIN packet")
                        lost_packets = []
                    else:
                        lost_packets = [int.from_bytes(response_re[i:i + 4], byteorder='big') for i in range(0, len(response_re), 4)]
                        print('the lost packets: ', lost_packets)
            print("all the lost packets were sent again")
    if opt == 2:
        # if the user chose opt 2 so sending this to the server and start sending the file
        client_socket.sendto(b'2', server_address)
        lost_by_time = send_file_time(file_name)
        # Receive acknowledgment from server containing list of lost packet by time
        client_socket.settimeout(0.05)  # Set a timeout of 0.05 seconds
        try:
            ack_data, _ = client_socket.recvfrom(4092)
        except socket.timeout:
            print("here")
        if ack_data == b'FIN':  # there isn't lost packets
            print("Received FIN packet")
        elif ack_data == b'LOST' or len(lost_by_time) > 0:  # there is some lost packets by time
            print("Received 'LOST' packet")
            los = b'GOT-LOST'
            client_socket.sendto(los, server_address)
            # Resend lost packets`
            print('Lost by time:', lost_by_time, '\nResending...')
            with open(file_name, 'rb') as f:
                while len(lost_by_time) > 0:  # do over and over until all the server will get all the packets for sure
                    for seq_num in lost_by_time:
                        # Retry logic for each lost packet
                        retries = 3  # Number of retries for each lost packet
                        while retries > 0:
                            f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                            data = f.read(4092)
                            # creat the packet and send it
                            resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                            client_socket.sendto(resend_packet, server_address)
                            try:
                                response_re, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
                                if response_re == b'ACK':
                                    lost_by_time.remove(seq_num)  # if got ack so it is no longer lost packets
                                    break  # Exit the retry loop if ACK is received
                            except socket.timeout:
                                retries -= 1  # Decrement retry count if ACK not received
                # Ensure to handle the end of file
                f.seek(0, 2)  # Move the pointer to the end of the file
                the_data = f.read(4092)
                if not the_data:  # if we got an empty packet the client done sending the file
                    client_socket.sendto(the_data, server_address)
            print("All lost packets were sent again")
    if opt == 3:
        # if the user chose opt 3 so sending this to the server and start sending the file
        client_socket.sendto(b'3', server_address)
        lost_by_time = send_file_time(file_name)
        print('File sent - time and packet number based.')
        # Receive acknowledgment from server containing list of lost packet sequence numbers
        client_socket.settimeout(0.05)  # Set a timeout of 0.005 seconds
        try:
            ack_data, _ = client_socket.recvfrom(4092)
        except socket.timeout:
            print("here")
        lost = []  # the lost packets by seq num from the server (define here)
        if ack_data == b'FIN':  # no lost packets
            print("received FIN packet")
        elif ack_data == b'LOST':  # there is lost packets by seq num
            lost, _ = client_socket.recvfrom(4092)
            lost_packets = [int.from_bytes(lost[i:i + 4], byteorder='big') for i in range(0, len(lost), 4)]
            all_lost = list(set(lost_packets).union(set(lost_by_time)))  # union both of the lists
            all_lost.sort()
            # Resend lost packets the same way as above
            print('all packets lost :', all_lost, '\nresending...')
            with open(file_name, 'rb') as f:
                while len(all_lost) > 0:
                    for seq_num in all_lost:
                        # Retry logic for each lost packet
                        retries = 3  # Number of retries for each lost packet
                        while retries > 0:
                            f.seek(seq_num * 4092)  # Move file pointer to the start of the lost packet
                            data = f.read(4092)
                            # creat the packet and send it
                            resend_packet = seq_num.to_bytes(4, byteorder='big') + data
                            client_socket.sendto(resend_packet, server_address)
                            try:
                                response_re, _ = client_socket.recvfrom(4096)  # Try to receive the ACK
                                if response_re == b'ACK':
                                    all_lost.remove(seq_num)  # if we got ack so no longer lost packet
                                    break  # Exit the retry loop if ACK is received
                            except socket.timeout:
                                retries -= 1  # Decrement retry count if ACK not received
                # Ensure to handle the end of file
                f.seek(0, 2)  # Move the pointer to the end of the file
                the_data = f.read(4092)
                if not the_data:  # when the client done sending the file
                    client_socket.sendto(the_data, server_address)
            print("all the lost packets were sent again")


finally:
    client_socket.close()  # Close the socket
    end = time.time()
    total_time = end - start_time  # calculate the total time it took to send the file
    print('the total time it took to send all the file is: ', round(total_time, 5))
    print("Client socket closed.\nbye bye :)")
