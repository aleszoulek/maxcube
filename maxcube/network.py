import socket


def read_raw_data(host, port):
    print('Connecting to %s:%s' % (host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(2)
    got = b''
    while True:
        try:
            got += s.recv(100000)
        except socket.timeout:
            break
    return got
