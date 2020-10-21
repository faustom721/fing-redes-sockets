#!./redes2/bin/python

import selectors
import socket
import types
from termcolor import colored
from announcements import start_announcements_client, start_announcements_server
import telnet

HOST = '0.0.0.0'
PORT = 2020 # Listening port
TELNET_PORT = 2025

sel = selectors.DefaultSelector()

# Sockets creados para atender conexiones telnet
telnet_connections = []

# start_announcements_client(PORT)
# start_announcements_server(HOST, PORT)

def accept_wrapper(key):
    listening_socket = key.fileobj
    conn, addr = listening_socket.accept() # conn es la nueva conexión (socket) para este nuevo cliente
    if key == telnet_selectorkey:
        telnet_connections.append(conn)
    print(colored('Conexión aceptada desde ' + str(addr), 'green'))
    conn.setblocking(False) # El listening socket debe seguir ready to read, por eso ponemos este nuevo en non-blocking. Así no tranca el (los) otro(s)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ
    sel.register(conn, events, data=data)

def service_connection_telnet(key, mask):
    socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = socket.recv(1024)  # Debe estar ready to read
        if recv_data:
            response = telnet.parse_message(recv_data).encode('utf-8')
            response += b'\r\n'
            sent = socket.send(response)  # Debe estar ready to write
            data.outb = data.outb[sent:]
        else:
            print(colored('Cerrando conexión a ' + str(data.addr), 'red' ))
            sel.unregister(socket)
            socket.close()
            telnet_connections.remove(socket)

    # En desuso
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('Enviando', repr(data.outb), 'a', data.addr)
            sent = socket.send(b'cosos')  # Debe estar ready to write
            data.outb = data.outb[sent:]
        

# Seteamos listening socket TCP de la aplicación. Para solicitudes de conexión.
telnet_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
telnet_sock.bind((HOST, TELNET_PORT))
telnet_sock.listen()
print('Esperando telnet en', (HOST, TELNET_PORT))
telnet_sock.setblocking(False)
telnet_selectorkey = sel.register(telnet_sock, selectors.EVENT_READ, data=None)

# Socket TCP para atender telnet
L_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
L_TCP.bind((HOST, PORT))
L_TCP.listen()
print('Escuchando TCP en', (HOST, PORT))
L_TCP.setblocking(False)
tcp_selectorkey = sel.register(L_TCP, selectors.EVENT_READ, data=None)

# Seteamos listening socket UDP de la aplicación. Para recibir anuncios.
L_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Habilitando reuso de la conexión
L_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
# Habilitando modo broadcasting
L_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
L_UDP.bind((HOST, PORT))
print('Escuchando UDP en', (HOST, PORT))
L_UDP.setblocking(False)
events = selectors.EVENT_READ
udp_selectorkey = sel.register(L_UDP, events, data=None)

lap=0

# Event loop
while True:
    events = sel.select(timeout=None) # Bloquea hasta que un socket registrado tenga lista I/O
    print("------------------------")
    for key, mask in events:
        # UDP de escucha
        if key == udp_selectorkey:
            data = key.fileobj.recv(1024)
            #Pasamos data que llega al parser de UDP para ver si son anuncios o qué.
            print(colored("UDP", "yellow"))

        # TCP de escucha
        if key in [tcp_selectorkey, telnet_selectorkey]:
            print(colored("Data None TCP", "yellow"))
            # Sabemos que es el listening socket de TCP y que es un pedido de conexión nuevo. Entonces aceptamos la conexión registrando un nuevo socket en el selector
            accept_wrapper(key)       

        else:
            # Sabemos que es de un socket cliente TCP ya aceptado y entonces servimos. Pero hay que ver si es una conexión Telnet
            if key.fileobj in telnet_connections:
                print(colored("Data Telnet", "yellow"))
                service_connection_telnet(key, mask)
            else:
                print(colored("Data TCP", "yellow"))
                service_connection_telnet(key, mask) # TODO cambiar a un nuevo service_connection

    # lap += 1
    # if lap == 3: 
    #     break
    #     sel.unregister(key.fileobj)
    #     key.fileobj.close()