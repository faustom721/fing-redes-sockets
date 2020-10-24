#!./redes2/bin/python

from termcolor import colored
import re
import os
import hashlib
from announcements import local_files, remote_files, announce_forever
from datetime import datetime
from prettytable import PrettyTable

indice_global = 1

def init():
    global indice_global
    indice_global = 1


class AppFile:
    def __init__(self, name, size, md5):
        self.name = name
        self.size = size
        self.md5 = md5

    # def __str__(self):
    #     f'{str(self.name)} - {str(self.size)} - {str(self.md5)}'

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

def armar_lista():
    table = PrettyTable()
    table.field_names = ['index', 'size', 'names']
    for value in remote_files.values():
        num = value.indice
        sizefile = value.size
        tuples = list(value.locations.values())

        names = tuples[0][0]
        for tupla in tuples[1:]:
            names += f',{tupla[0]}'
        table.add_row([num, sizefile, names])
    return table.get_string()

def procesar_descarga(download):
    download = download.splitlines()
    
    md5 = download[1]
    start = download[2]
    size = download[3]

    remote_files[md5].locations

# (.*)\\n

# [ANNOUNCE\\n]?(.*)\\t(.*)\\t(.*)\\n

def extraer_anuncios(anuncios,ip):
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


def parse_message(message):
    """
    Lee y entiende las peticiones por comando que llegan por telnet
    """

    msg = message.decode('utf-8')
    print(colored("Telnet pide " + msg, 'magenta'))

    # Mandó list?
    clist = re.match(r'list', msg)
    if clist:
        return armar_lista()

    # Mandó offer?
    else:
        offer = re.match(r'offer (.*)\r', msg)
        if offer:
            filename = offer[1]       

            file_path = os.getcwd() + "/files/" + filename

            if os.path.exists(file_path):
                sizefile = os.path.getsize(file_path)          

                # Calcula el md5
                with open(file_path, "rb") as f:
                    file_hash = hashlib.md5()
                    chunk = f.read(8192)
                    while chunk:
                        file_hash.update(chunk)
                        chunk = f.read(8192)

                file_hash = file_hash.hexdigest()

                aux_file = AppFile(filename, sizefile, file_hash)

                # Guardamos el archivo en nuestro diccionario de seguimiento local
                local_files[file_hash] = aux_file

                # Una vez actualizada la lista de archivos locales, mandamos a actualizar los anuncios
                announce_forever.set_announcements()

                return 'ARCHIVO AGREGADO'

            else:
                return 'ARCHIVO NO ENCONTRADO'


        # Mandó get?
        else:
            get = re.match(r'get (\d*)\r', msg)
            if get:
                fileid = get[1]
                return f'INICIANDO DESCARGA DEL ARCHIVO {fileid}'

    return 'COMANDO INCORRECTO!'

