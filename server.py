#!./redes2/bin/python

import selectors
import socket
import types
import argparse
from termcolor import colored
 
arg_parser = argparse.ArgumentParser(description='Server grupo 67.')
arg_parser.add_argument('-p','--port', help='Puerto de escucha.', required=True)
args = arg_parser.parse_args()
 
print("***********************************************")
print ("Puerto de escucha: %s" % args.port )
print("***********************************************")
HOST = '127.0.0.1' 
PORT = int(args.port) # Listening port

def accept_wrapper(lis_socket):
    conn, addr = lis_socket.accept() # conn es la nueva conexión (socket) para este nuevo cliente
    print(colored('Conexión aceptada desde ' + str(addr), 'green'))
    conn.setblocking(False) # El listening socket (lis_socket) debe seguir ready to read, por eso ponemos este nuevo en non-blocking. Así no tranca el (los) otro(s)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = socket.recv(1024)  # Debe estar ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print(colored('Cerrando conexión a ' + str(data.addr), 'red' ))
            sel.unregister(socket)
            socket.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('Enviando', repr(data.outb), 'a', data.addr)
            sent = socket.send(data.outb)  # Debe estar ready to write
            data.outb = data.outb[sent:]

sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((HOST, PORT))
lsock.listen()
print('Escuchando en', (HOST, PORT))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

# Event loop
while True:
    events = sel.select(timeout=None) # Bloquea hasta que un socket registrado tenga lista I/O
    for key, mask in events:
        if key.data is None:
            pass
            # Sabemos que es el listening socket, entonces aceptamos la conexión registrando un nuevo socket en el selector
            #accept_wrapper(key.fileobj) # key.fileobj es nuestro listening socket
        else:
            # Como hay data sabemos que es de un socket cliente ya aceptado, entonces servimos
            service_connection(key, mask)