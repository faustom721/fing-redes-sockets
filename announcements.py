#!./redes2/bin/python

import socket
import selectors
import types
import time
from termcolor import colored
from threading import Timer
import atexit


local_files = {}
remote_files = {}


def start_announcements_server(host_ip, application_port):
    """
    Recibe los anuncios de archivos, los procesa y responde.
    """
    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Habilitando reuso de la conexión
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # Habilitando modo broadcasting
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind((host_ip, application_port))
    sock.setblocking(False)
    events = selectors.EVENT_READ
    sel.register(sock, events, data=None)

    # Event loop
    while True:
        events = sel.select(timeout=None) # Bloquea hasta que un socket registrado esté listo para leer/escribir
        # data, addr = sock.recvfrom(1024)
        # if data:
        #     if str(sock.type) == "SocketKind.SOCK_DGRAM":
        #         print("jsuuaj")
        #     print(data)
        #     print("Recibiendo anuncios de:", addr)
        print("mal")


class AnnounceForever(object):
    def __init__(self, announcements = None): 
        self.announcements = b''

    def get_announcements(self): 
        return self.announcements 

    def set_announcements(self): 
        ann = 'ANNOUNCE\n'
        lista_ann = []
        for file_hash, app_file in local_files.items():
            annAux = f'{app_file.name}\t{app_file.size}\t{app_file.md5}\n'
            if (len(annAux) + len(ann)) > 1024:
                lista_ann.append(ann.encode('utf-8'))
                ann = 'ANNOUNCE\n'
            ann += annAux
        self.announcements = lista_ann

    def send_announcements(self, socket, application_port):
        if self.announcements:
            for ann in self.announcements:
                sent = socket.sendto(ann, ("<broadcast>", application_port))
            print(colored('Anunciando!', 'blue'))
            print(sent)
        else:
            print(colored('announcements es None', 'red'))


announce_forever = AnnounceForever()
