#!./redes2/bin/python

from termcolor import colored
import re

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
            filename = offer[0]
            return 'AGREGANDO EL ARCHIVO'

        # Mandó get?
        else:
            get = re.match(r'get <(\d*)>', msg)
            if get:
                fileid = get[1]
                return f'INICIANDO DESCARGA DEL ARCHIVO {fileid}'

    return 'COMANDO INCORRECTO!'