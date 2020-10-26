#!./redes2/bin/python

from termcolor import colored
import re
import os
import hashlib
from announcements import local_files, remote_files, announce_forever
from prettytable import PrettyTable
import socket
import selectors
from helpers import send_msg, recv_msg

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
    start = int(download[2])
    size = int(download[3])

    if md5 in local_files:
        filename = local_files[md5].name
        file_path = os.getcwd() + '/files/' + filename

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                f.read(int(start))
                chunk = f.read(int(size))
            return b'DOWNLOAD OK\n' + chunk

    return b'DOWNLOAD FAILURE\n'


download_manager = (None, {}) # (file_name, {socket: (id_chunk, chunk, recieved, msg)})

def process_file_chunk(sock, chunk):
    global download_manager
    download_manager[1][sock][1] = chunk[12:]
    download_manager[1][sock][2] -= 1 

    ready = 0
    total_connections = len(download_manager[1])

    for connection in download_manager[1].values():
        if connection[2] == 0:
            ready += 1

    state = f'Estado de la descarga: {ready} / {total_connections}'
    print(colored(state, 'cyan'))

    if ready == total_connections:
        return download_manager
    else:
        return None


def request_download(file_id, selector):
    global download_manager
    md5 = None
    for value in remote_files.values():
        if value.indice == file_id:
            md5 = value.md5
            filename = list(value.locations.values())[0][0]
            download_manager = (filename, {})
            break
    size = remote_files[md5].size // len(remote_files[md5].locations)
    remaining_data = remote_files[md5].size % len(remote_files[md5].locations)
    start = 0
    index = 1
    for ip in remote_files[md5].locations.keys():
        msg = 'DOWNLOAD\n'
        msg += md5 + '\n'
        msg += str(start) + '\n'
        if index == len(remote_files[md5].locations):
            size += remaining_data
        msg += str(size) + '\n'
        start += size
        index += 1
        sock = start_connection(ip, selector)
        download_manager[1][sock] = [index, None, 1, msg]
        send_msg(sock, msg.encode('UTF-8'))


def re_request_download(socket):
    global download_manager
    conn = download_manager[1].pop(socket) # Eliminamos la conexión del socket del peer que no respondió lo que le pedimos
    if len(download_manager[1]) > 0:
        new_responsible_sock = min(download_manager[1], key=download_manager[1].get)
        download_manager[1][new_responsible_sock][2] += 1
        send_msg(new_responsible_sock, conn[3].encode('UTF-8')) # Le reasignamos el mensaje que no nos dieron al nuevo
        return True
    else:
        return False


def start_connection(host, selector):
    print('Estableciendo conexión para descargar a', (host, 2020))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex((host, 2020))
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    selector.register(sock, events, data=None)
    return sock

def parse_message(message, selector):
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
                sizefile = int(os.path.getsize(file_path))

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

                # Lo borramos del de los disponibles remotos
                if remote_files.get(file_hash):
                    del remote_files[file_hash]

                # Una vez actualizada la lista de archivos locales, mandamos a actualizar los anuncios
                announce_forever.set_announcements()

                return 'ARCHIVO AGREGADO'

            else:
                return 'ARCHIVO NO ENCONTRADO'


        # Mandó get?
        else:
            get = re.match(r'get (\d*)\r\n', msg)
            if get:
                file_id = int(get[1])
                msg = f'INICIANDO DESCARGA DEL ARCHIVO {file_id}'
                print(msg)
                request_download(file_id, selector)
                return msg

    return 'COMANDO INCORRECTO!'

