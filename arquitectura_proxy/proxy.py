#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import zmq
import json
import hashlib

hashes = {}

where_are_torrents = {}

list_ip = list()

robin = 0

def main():

    #servidor
    
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    server_address = write_server_ip()
    socket.bind(server_address)
    print("Proxy on")
    while True:
        #  Wait for next request from client
        message = socket.recv_multipart()
        if message[0] == b'continue':
            server_to_save_file_chunk = torrent(message)    #save the server where the file chunk must to go
            socket.send_string(server_to_save_file_chunk) #Chunk recived
                
        elif message[0] == b'ok':
            payload = torrent_json(message)
            payload_hash = torrent_hash(payload)
            server_to_send_torrent = select_server()
            add_torrents_list(payload_hash,server_to_send_torrent)
            delete_hashes_hash(message[1])
            payload = payload.encode('utf-8')
            payload_hash = payload_hash.encode('utf-8')
            server_to_send_torrent = server_to_send_torrent.encode('utf-8')
            socket.send_multipart([payload_hash,server_to_send_torrent,payload])   # I want to send a file when have the torent 
            
        elif message[0] == b'new server':
            add_server(message[1])
            socket.send_string("welcome to the family")
            
        elif message[0] == b'get server':
            server_torrent = get_torrent(message[1])
            socket.send_string(server_torrent)
        
def torrent(message):
    hash = message[1].decode('utf-8')

    if hash in hashes:
        hashes[hash]["server_address"].append(select_server())
        hashes[hash]["hash_chunk"].append(message[3].decode('utf-8'))
        return hashes[hash]["server_address"][-1]
    else:
        #extension = message[2].decode('utf-8')
        hashes[hash] = {
                "extension" : message[2].decode('utf-8'),
                "server_address" : [select_server()],
                "hash_chunk" :  [message[3].decode('utf-8')],
            }
        return hashes[hash]["server_address"][-1]
    
def torrent_json(message):
    hash = message[1].decode('utf-8')
    payload = hashes.get(hash,{})

    extension = payload.get("extension", "")
    server_address = payload.get("server_address", [])
    hash_chunk = payload.get("hash_chunk", [])
    
    payload_dic = {
        "extension": extension,
        "server_address": server_address,
        "hash_chunk": hash_chunk
    }

    payload_json = json.dumps(payload_dic)

    return payload_json
    
def get_torrent(hash):
    hash = hash.decode('utf-8')
    if hash in where_are_torrents:
        server = where_are_torrents[hash]["server"]
        return server
    else:
        return "No existe"
         
def torrent_hash(payload_json):
    # Calcular el hash SHA-512 de la cadena JSON
    hash_sha512 = hashlib.sha512()
    hash_sha512.update(payload_json.encode('utf-8'))
    hash_sha512_calculado = hash_sha512.hexdigest()
    return hash_sha512_calculado

def write_server_ip():
    server_ip = str(input("Ingrese la dirección ip de su computadora, ejemplo 192.168.10.6: "))
    server_ip = server_ip.strip()
    server_puerto = str(input("Ingrese el puerto a usar, ejemplo 7777, recuerde que no debe usar un puerto usado por otro servicio: "))
    server_puerto = server_puerto.strip()
    server_address = "tcp://" + server_ip + ":" + server_puerto
    return server_address
    
# Round Robin
def select_server():
    if not list_ip:
        return None  # No hay servidores disponibles
    server = list_ip.pop(0)  # Obtener el siguiente servidor
    list_ip.append(server)  # Volver a agregar al final
    return server

def add_server(server):
    server = server.decode('utf-8')
    list_ip.append(server)
    
def add_torrents_list(hash,server):

    where_are_torrents[hash] = {
        "server" : server
    }

def delete_hashes_hash(hash):
    hash = hash.decode('utf-8')
    if hash in hashes:
        del hashes[hash]

if __name__ == "__main__":
    main()
    
