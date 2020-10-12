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
    print("hola soy el server")
    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Habilitando reuso de la conexión
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # Habilitando modo broadcasting
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(('', application_port))
    sock.setblocking(False)
    events = selectors.EVENT_READ
    sel.register(sock, events, data=None)

    # Event loop
    while True:
        events = sel.select(timeout=None) # Bloquea hasta que un socket registrado esté listo para leer/escribir
        # data, addr = sock.recv(1024)
        # for key, mask in events:
        #     print(mask)
        print(colored('Anuncio recibido!', 'green'))


def send_announcement(socket, application_port, message):
    socket.sendto(message, ("<broadcast>", application_port))
    print(colored('Anunciando!', 'blue'))


def announcements_forever(socket, application_port, message):
    # TODO: hacer send_announcement cada 30 segundos



def start_announcements_client(application_port):
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

    announcements_forever(sock, application_port, message)
