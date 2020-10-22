#!./redes2/bin/python

from termcolor import colored
import re
import os
import hashlib
from announcements import lista_archivos_locales, announce_forever


class archivo:
    def __init__(self, nombre, tamanio, md5):
        self.nombre = nombre
        self.tamanio = tamanio
        self.md5 = md5

    # def __str__(self):
    #     f'{str(self.nombre)} - {str(self.tamanio)} - {str(self.md5)}'


def parse_message(message):
    """
    Lee y entiende las peticiones por comando que llegan por telnet
    """

    msg = message.decode('utf-8')
    print(colored("Telnet pide " + msg, 'magenta'))

    # Mandó list?
    clist = re.match(r'list', msg)
    if clist:
        return 'TOMA LOS ARCHIVOS'

    # Mandó offer?
    else:
        offer = re.match(r'offer <(.*)>', msg)
        if offer:
            filename = offer[1]         

            file_url = os.getcwd() + "/files/" + filename
            sizefile = os.path.getsize(file_url)
   
            # Calcula el md5
            with open(file_url, "rb") as f:
                file_hash = hashlib.md5()
                chunk = f.read(8192)
                while chunk:
                    file_hash.update(chunk)
                    chunk = f.read(8192)

            print(file_hash.hexdigest())

            file_hash = file_hash.hexdigest()

            aux_file = archivo(filename, sizefile, file_hash)

            # Guardamos el archivo en nuestro diccionario de seguimiento local
            lista_archivos_locales.setdefault(
                file_hash, aux_file
            )

            # TODO: Cuando el archivo no existe

            print(lista_archivos_locales)

            # Una vez actualizada la lista de archivos locales, mandamos a actualizar los anuncios
            announce_forever.set_announcements()

            return 'ARCHIVO AGREGADO'


        # Mandó get?
        else:
            get = re.match(r'get <(\d*)>', msg)
            if get:
                fileid = get[1]
                return f'INICIANDO DESCARGA DEL ARCHIVO {fileid}'

    return 'COMANDO INCORRECTO!'