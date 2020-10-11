#!./redes2/bin/python

import socket
import selectors
import types
import time
from termcolor import colored

def start_announcements_server(application_port):
    """
    Recibe los anuncios de archivos, los procesa y responde.
    """
    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    

    # Habilitando reuso de la conexión
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # Habilitando modo broadcasting
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(('0.0.0.0', application_port))
    sock.setblocking(False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(sock, events, data=None)

    # Event loop
    while True:
        events = sel.select(timeout=None) # Bloquea hasta que un socket registrado esté listo para leer/escribir
        # data, addr = sock.recv(1024)
        for key, mask in events:
            print(mask)
            print(colored('Anuncio recibido!', 'green'))


def start_announcements_client(application_port, interval):
    """
    Hace los anuncios de archivos recurrentemente.
    Hace pedidos de anuncios
    """

    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setblocking(False)

    # Habilitando reuso del socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # Habilitando modo broadcasting
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    message = b'ANUNCIO'

    data = types.SimpleNamespace(msg_len=len(message),
                                recv_total=0,
                                message=message,
                                outb=b'')
    sel.register(sock, selectors.EVENT_WRITE, data=data)

    # Event loop
    while True:
        events = sel.select(timeout=None) # Bloquea hasta que un socket registrado tenga lista I/O
        sock.sendto(message, ("<broadcast>", application_port))
        print(colored('Anunciando!', 'blue'))
        time.sleep(interval)
