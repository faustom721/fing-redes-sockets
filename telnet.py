#!./redes2/bin/python

from termcolor import colored
import re
import os
import hashlib
from announcements import local_files, remote_files, announce_forever
from datetime import datetime
from prettytable import PrettyTable


class AppFile:
    def __init__(self, name, size, md5):
        self.name = name
        self.size = size
        self.md5 = md5



    def __str__(self):
        return str({
            'md5': self.md5,
            'size': self.size,
            'name': self.name
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


def process_download(download):
    download = download.splitlines()
    
    md5 = download[1]
    start = download[2]
    size = download[3]

    filename = local_files[md5].name 
    file_path = os.getcwd() + "/files/" + filename

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            chunk = f.read(start)
            chunk = f.read(size)
        return chunk


download_manager = {} # {socket: (id_chunk, chunk, recieved)}

def process_file_chunk(sock, data):
    global download_manager
    chunk = recv_data
    download_manager[sock][1] = True

    ready = True
    for connection in download_manager.values():
        if connection[1] == False:
            ready = False
            return None
    return download_manager


def request_download(file_id, selector):
    global download_manager
    download_manager = {} 
    md5 = None
    for value in remote_files.values():
        if value.indice == file_id:
            md5 = value.md5
            break
    size = remote_files[md5].size // len(remote_files[md5].locations)
    remaining_data = remote_files[md5].size % len(remote_files[md5].locations)
    start = 0
    index = 1
    for ip in remote_files[md5].locations.keys():
        msg = 'DOWNLOAD\n'
        msg += md5 + '\n'
        msg += start + '\n'
        if index == len(remote_files[md5].locations):
            size += remaining_data
        msg += size + '\n'
        start += size
        index += 1
        download_manager[sock] = (index, None, False)
        sock = start_connection(ip, selector)
        sock.send(msg.encode('utf-8'))


def start_connection(host, selector):
    print('Estableciendo conexión para descargar a', (host, 2020))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex((host, 2020))
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(sock, events, data=None)
    return sock

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

