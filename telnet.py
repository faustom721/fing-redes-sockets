#!./redes2/bin/python

from termcolor import colored
import re
import os
import hashlib
from announcements import local_files, announce_forever


class AppFile:
    def __init__(self, name, size, md5):
        self.name = name
        self.size = size
        self.md5 = md5

    # def __str__(self):
    #     f'{str(self.name)} - {str(self.size)} - {str(self.md5)}'


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
                local_files.setdefault(
                    file_hash, aux_file
                )

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