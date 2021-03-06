#!./redes2/bin/python

import selectors
import socket
import types
from termcolor import colored
import announcements
import telnet
import os

from helpers import send_msg, recv_msg

import time
import linuxfd
import random

HOST = '0.0.0.0'
PORT = 2020 # Listening port
TELNET_PORT = 2025

sel = selectors.DefaultSelector()

announcements.init()

# Sockets creados para atender conexiones telnet
telnet_connections = []


def accept_wrapper(key):
    listening_socket = key.fileobj
    conn, addr = listening_socket.accept() # conn es la nueva conexión (socket) para este nuevo cliente
    if key == telnet_selectorkey:
        telnet_connections.append(conn)
    print(colored('Conexión aceptada desde ' + str(addr), 'green'))
    conn.setblocking(True) # El listening socket debe seguir ready to read, por eso ponemos este nuevo en non-blocking. Así no tranca el (los) otro(s)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ
    sel.register(conn, events, data=data)


def service_connection_telnet(key, mask):
    socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = socket.recv(1024)  # Debe estar ready to read
        if recv_data:
            response = telnet.parse_message(recv_data, sel).encode('utf-8')
            response += b'\r\n'
            sent = socket.send(response)  # Debe estar ready to write
        else:
            print(colored('Cerrando conexión a ' + str(data.addr), 'red' ))
            sel.unregister(socket)
            socket.close()
            telnet_connections.remove(socket)


def service_connection(key, mask):
    socket = key.fileobj
    if mask & selectors.EVENT_READ:
        recv_data = recv_msg(socket)
        if recv_data:
            data = recv_data.decode('utf-8')
            # Me pidieron chunk
            if data.splitlines()[0] == "DOWNLOAD":
                response = telnet.process_download(data)
                send_msg(socket, response)
                print('Chunk enviado')
            
            # Error en pedido de descarga
            elif data.splitlines()[0] == "DOWNLOAD FAILURE":
                success = telnet.re_request_download(socket)
                if not success:
                    telnet_connections[0].send(b'DESCARGA FALLIDA\n')
                sel.unregister(socket)
                socket.close()

            else:
                download_manager = telnet.process_file_chunk(socket, data)
                if download_manager:
                    # Escribimos el archivo en disco
                    file_path = os.getcwd() + "/files/" + download_manager[0]
                    conns = []
                    for conn in download_manager[1].values():
                        for i in range(len(conn[0])):
                            conns.append([conn[0][i], conn[1][i]])

                    with open(file_path, "w") as f:
                        chunks = sorted(conns, key=lambda x: x[0])
                        for chunk in chunks:
                            f.write(chunk[1])
                        telnet_connections[0].send(b'DESCARGA EXITOSA\n')

                    # Cerramos conexiones
                    for sock in download_manager[1].keys():
                        sel.unregister(sock)
                        sock.close()

        else:
            print(colored('Cerrando conexión.', 'red'))
            sel.unregister(socket)
            socket.close()
        

# Seteamos listening socket TCP de la aplicación. Para solicitudes de conexión.
telnet_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
telnet_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
telnet_sock.bind((HOST, TELNET_PORT))
telnet_sock.listen()
print('Esperando telnet en', (HOST, TELNET_PORT))
telnet_sock.setblocking(False)
telnet_selectorkey = sel.register(telnet_sock, selectors.EVENT_READ, data=None)

# Socket TCP para atender telnet
L_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
L_TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
# L_UDP.setblocking(False)
events = selectors.EVENT_READ
udp_selectorkey = sel.register(L_UDP, events, data=None)

request = b'REQUEST\n'
sent = L_UDP.sendto(request, ("<broadcast>", PORT))

# Timer anuncios
tfd = linuxfd.timerfd(rtc=True, nonBlocking=True)
tfd.settime(1,30)

timer_selectorkey = sel.register(tfd.fileno(), selectors.EVENT_READ)


# Event loop
while True:
    events = sel.select(timeout=None) # Bloquea hasta que un socket registrado tenga lista I/O
    for key, mask in events:

        # Llegó timer
        if key == timer_selectorkey:
            announcements.announce_forever.send_announcements(udp_selectorkey.fileobj, PORT)
            tfd.read()
            announcements.purge_files()


        # UDP de escucha
        elif key == udp_selectorkey:
            #Pasamos data que llega al parser de UDP para ver si son anuncios o qué.
            data, addr = key.fileobj.recvfrom(1024)

            data = data.decode('utf-8')
            if 'REQUEST' in data:
                # Espera random de hasta 5 segundos
                time.sleep(random.randint(1, 5))
                announcements.announce_forever.send_announcements(udp_selectorkey.fileobj, PORT)
            else:
                print("Recibiendo anuncios de:", addr)
                announcements.read_announcements(data, addr[0])


        # TCP de escucha
        elif key in [tcp_selectorkey, telnet_selectorkey]:
            # Sabemos que es el listening socket de TCP y que es un pedido de conexión nuevo. Entonces aceptamos la conexión registrando un nuevo socket en el selector
            accept_wrapper(key)


        # Sabemos que es de un socket cliente TCP ya aceptado y entonces servimos. Pero hay que ver si es una conexión Telnet
        else:
            # Data telnet
            if key.fileobj in telnet_connections:
                service_connection_telnet(key, mask)
            
            # Data TCP
            else:
                service_connection(key, mask)
