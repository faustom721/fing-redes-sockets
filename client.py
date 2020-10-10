#!./redes2/bin/python

import socket
import selectors
import types

HOST = '127.0.0.1'  # Server IP
PORT = 2020        # Listening socket en el server
CONNECTIONS = 3     # Cuántas conexiones establece

sel = selectors.DefaultSelector()

def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print('Estableciendo conexión', connid, 'a', server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(connid=connid,
                                     msg_total=sum(len(m) for m in messages),
                                     recv_total=0,
                                     messages=list(messages),
                                     outb=b'')
        sel.register(sock, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Debe estar ready to read
        if recv_data:
            print('Recibido', repr(recv_data), 'de la conexión', data.connid)
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print('Cerrando conexión', data.connid)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print('Enviando', repr(data.outb), 'a la conexión', data.connid)
            sent = sock.send(data.outb)  # Debe estar ready to write
            data.outb = data.outb[sent:]


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hola mundo')
    data = s.recv(1024)

print('Recibido', repr(data))

messages = [b'Mensaje 1 de cliente.', b'Mensaje 2 de cliente.']

start_connections(HOST, PORT, CONNECTIONS)