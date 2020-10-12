#!./redes2/bin/python

import socket
import selectors
import types
import time
from termcolor import colored
from threading import Timer
import atexit


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


def send_announcements(socket, application_port, announcements):
    if announcements:
        socket.sendto(announcements, ("<broadcast>", application_port))
        print(colored('Anunciando!', 'blue'))
    else:
        print(colored('announcements es None', 'red'))


class AnnounceForever(object):
    def __init__(self, announcements = None): 
        self._announcements = announcements

    def get_announcements(self): 
        return self._announcements 

    def set_announcements(self, x): 
        self._announcements = x

    def start(self, socket, application_port, interval):
        # Anunciamos
        send_announcements(socket, application_port, self._announcements)
        # Armamos timer que se llama recursivamente cada interval segundos
        timer = Timer(interval, AnnounceForever.start, (self, socket, application_port, interval))
        # Registramos timer.cancel para poder parar el timer cuando el intérprete pare
        atexit.register(timer.cancel)
        timer.start()


def start_announcements_client(application_port):
    """
    Hace los anuncios de archivos recurrentemente.
    Hace pedidos de anuncios
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Habilitando reuso del socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # Habilitando modo broadcasting
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    announce_forever = AnnounceForever(b'ANUNCIOS')
    announce_forever.start(sock, application_port, 1) #TODO: poner interval correcto 30s
