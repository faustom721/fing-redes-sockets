#!./redes2/bin/python

import selectors
import socket
import types
import argparse
from termcolor import colored
from announcements import start_announcements_client, start_announcements_server
 
arg_parser = argparse.ArgumentParser(description='Server grupo 67.')
arg_parser.add_argument('-p','--port', help='Puerto de escucha.', required=True)
args = arg_parser.parse_args()
 
print("***********************************************")
print ("Puerto de la aplicación: %s" % args.port )
print("***********************************************")
HOST = '127.0.0.1' 
PORT = int(args.port) # Listening port

start_announcements_client(PORT)
start_announcements_server(PORT)
