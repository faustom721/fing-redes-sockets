#!./redes2/bin/python

import socket
import selectors
import types
import time
from termcolor import colored
import re
from datetime import datetime


local_files = {}
remote_files = {}

indice_global = 1

def init():
    global indice_global
    indice_global = 1


class RemoteFile:
    def __init__(self, md5, size, indice, locations):
        self.md5 = md5
        self.size = size
        self.indice = indice
        self.locations = locations # {ip: (namefile, time)}

    def __str__(self):
        return str({
            'md5': self.md5,
            'size': self.size,
            'index': self.indice,
            'locations': self.locations
        })


def read_announcements(anuncios, ip):
    anuncios = anuncios.decode('utf-8')   
    anuncios = anuncios.splitlines()

    for anuncio in anuncios[1:]:
        archivo = re.split(r'\t', anuncio)
        filename = archivo[0]
        sizefile = archivo[1]
        md5 = archivo[2]

        print('Archivos')
        for file in remote_files.values():
            print(file)

        if md5 not in local_files:
            if md5 in remote_files:
                remote_files[md5].locations[ip] = (filename, datetime.now()) # Actualizamos el remotefile conforme al nuevo anuncio
                print(colored("Archivo actualizado", "green"))
            else:
                global indice_global
                indice = indice_global
                indice_global = indice_global + 1

                locations = {ip: (filename, datetime.now())}

                remote_file = RemoteFile(md5, sizefile, indice, locations)
                remote_files[md5] = remote_file
                print(colored("Archivo nuevo", "green"))


def purge_files():
    global remote_files
    files_to_delete = []
    locations_to_delete = []
    
    for file_hash, available_file in remote_files.items():
        now = datetime.now()
        # Reviso cada location de cada archivo registrado como disponible en la red p2p para ver si se le pasó el tiempo
        for ip, location_data in available_file.locations.items():
            last_signal = location_data[1]
            delta = now - last_signal
            delta = delta.seconds
            if delta >= 90:
                # Hay que borrar al archivo como disponible de los remotos
                if len(available_file.locations) == 1:
                    # Era la única disponibilidad remota
                    files_to_delete.append(file_hash)
                else:
                    locations_to_delete.append(ip)
                
    # Purgamos
    for file_del in files_to_delete:
        del remote_files[file_del]
    for location_del in locations_to_delete:
        del available_file.locations[ip]


class AnnounceForever(object):
    def __init__(self, announcements = None):
        self.announcements = b''

    def get_announcements(self): 
        return self.announcements 

    def set_announcements(self): 
        ann = 'ANNOUNCE\n'
        for file_hash, app_file in local_files.items():
            ann += f'{app_file.name}\t{app_file.size}\t{app_file.md5}\n'
        ann = ann.encode('utf-8')
        self.announcements = ann

    def send_announcements(self, socket, application_port):
        if self.announcements:
            sent = socket.sendto(self.announcements, ("<broadcast>", application_port))
            print(colored('Anunciando!', 'blue'))
        else:
            print(colored('announcements es None', 'red'))

announce_forever = AnnounceForever()
