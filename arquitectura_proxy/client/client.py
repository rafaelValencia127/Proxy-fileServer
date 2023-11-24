import zmq
import hashlib
import json
import os

#size of the division of each part of file 
chunks = 1024*1024*10

context = zmq.Context()

list_of_file = list()

def main():
    server_address = write_server_ip()
    print("Connecting to management file server…")
    socket = context.socket(zmq.REQ)
    while True:
        print("Hola este es un administrador de archivos publicos")
        print("1. Guardar un archivo en la nube \n2. Descagar un archivo de la nube\n3. Salir del programa")
        menu_input = int(input("Escoje la opcion que se adapte a lo que neceitas: "))
        
        if menu_input == 1:
            file_path, hash, extension = fill_file_information()
            send_chunks_hash_and_file(file_path,socket,hash, extension,server_address)
        elif menu_input == 2:
            seleccion_de_archivo = int(input("ingrese:\n1. si desea ingresar el hash manualmente\n2. si desea utilizar un hash que haya guardado en este cliente: "))
            if seleccion_de_archivo == 1:
                hash_to_dowload = input("Digite el hash: ")
                hash_to_dowload = hash_to_dowload.encode('utf-8')
                server_torrent = get_information_to_dowload(hash_to_dowload,socket,server_address)
                file = get_torrent(hash_to_dowload,server_torrent)
                get_information(file,hash_to_dowload)
            elif seleccion_de_archivo == 2:
                user_ui = 0
                for x in list_of_file:
                    user_ui += 1
                    print(f'Hash numero: {user_ui} = {x}') 
                hash_to_dowload = ((int(input("Digite el numero del .torrent de archivo que desee descargar: "))) - 1)
                if 0 <= hash_to_dowload < len(list_of_file):
                    hash_to_dowload = list_of_file[(hash_to_dowload)]
                    server_torrent = get_information_to_dowload(hash_to_dowload,socket,server_address)
                    file = get_torrent(hash_to_dowload,server_torrent)
                    get_information(file,hash_to_dowload)
                    
                else:
                    print("El valor ingresado no es valido")
        elif menu_input == 3:
            socket.close()
            break
            
def get_path():
    file_path = input("Ingrese el path del archivo: ")
    return file_path

#get file hash
def get_full_hash(file_path):       
    hash_sha512 = hashlib.sha512()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunks), b""):
            hash_sha512.update(chunk)
    return hash_sha512.hexdigest()

def send_chunks_hash_and_file(file_path,socket,hash, extension,server_address):
    word = b'continue'
    with open(file_path,'rb') as file:
        while True:
            socket.connect(server_address)
            hash_chunk = hashlib.sha512()
            file_data = file.read(chunks)
            if not file_data:
                break
            hash_chunk.update(file_data)
            hash_send_chunk = hash_chunk.hexdigest()
            hash_send_chunk_bytes = bytes(hash_send_chunk, 'utf-8')

            socket.send_multipart([word,hash, extension,hash_send_chunk_bytes])
            send_chunk_to_choice_server(socket.recv(),file_data,hash_send_chunk_bytes)
        
        word = b'ok'
        socket.connect(server_address)
        socket.send_multipart([word,hash])
        hash_of_payload,server_to_send_torrent,payload = socket.recv_multipart()
        send_torrent(hash_of_payload,server_to_send_torrent,payload) 
        hash_of_payload.decode('utf-8')
        print(f'El .Torrent del archivo que acabas de subir es: {hash_of_payload}')
        list_of_file.append(hash_of_payload)

def send_chunk_to_choice_server(server_to_send,file_data,hash_send_chunk_bytes):
    word = b'save'
    server_socket = context.socket(zmq.REQ)
    server_socket.connect(server_to_send)
    server_socket.send_multipart([word,hash_send_chunk_bytes,file_data])
    server_socket.recv()
    server_socket.close()
    
def send_torrent(hash_of_payload,server_to_send_torrent,payload):
    server_to_send_str = server_to_send_torrent.decode('utf-8')
    word = b'save torrent'
    server_socket = context.socket(zmq.REQ)
    server_socket.connect(server_to_send_str)
    server_socket.send_multipart([word,hash_of_payload,payload])
    server_socket.recv()
    server_socket.close()

def get_extension(file_path):

    # get file name without path
    full_name = os.path.basename(file_path)

    # separate extension name
    nombre_sin_extension, extension = os.path.splitext(full_name)

    return extension

def fill_file_information():
    file_path = get_path()
    hash = get_full_hash(file_path)
    file_extension = get_extension(file_path)

    hash_b = bytes(hash, 'utf-8')
    file_extension_b = bytes(file_extension, 'utf-8')

    return file_path, hash_b, file_extension_b

def get_information_to_dowload(hash,socket,server_address):        #hash del archivo original
    socket.connect(server_address)
    word = b'get server'
    socket.send_multipart([word,hash])
    server_torrent = socket.recv_string()
    print(server_torrent)
    return server_torrent

def get_torrent(hash,server_address):
    server_socket = context.socket(zmq.REQ)
    server_socket.connect(server_address)
    word = b'get torrent'
    server_socket.send_multipart([word,hash])
    file_torrent = server_socket.recv()
    server_socket.close()
    return file_torrent
    
def get_information(file,hash):        #hash del archivo original
    file_decode = file.decode('utf-8')
    diccionario_torrent = json.loads(file_decode)
    file_partition_count = diccionario_torrent["server_address"]
    list_of_chunks = list()
    for index_list in range(len(file_partition_count)) :
        server_to_get_chunks = file_partition_count[index_list]
        hash_chunk = diccionario_torrent["hash_chunk"][index_list]
        hash_chunk = hash_chunk.encode('utf-8')
        file_chunk = get_file_to_server(server_to_get_chunks,hash_chunk)
        list_of_chunks.append(file_chunk)

    create_file(hash,diccionario_torrent["extension"],list_of_chunks)
        

        
def get_file_to_server(server_to_get_chunks,hash_chunk):
    word = b'get'
    server_socket = context.socket(zmq.REQ)
    server_socket.connect(server_to_get_chunks)
    server_socket.send_multipart([word,hash_chunk])
    file_chunk = server_socket.recv()
    return file_chunk

#unless
def create_file_characteristic(hash,extension,file_chunk,customers):
    customer_hash = hash.decode('utf-8')

    if customer_hash in customers:
        customers[customer_hash]["file_chunks"].append(file_chunk)
    else:
        customer_extension = extension.decode('utf-8') 

        customers[customer_hash] = {
                "extension" : customer_extension,
                "file_chunks" : [file_chunk]
            }
    
def join_bytes(lista_chunks):
    x = b''.join(lista_chunks)
    return x

def create_file(hash,extension,lista_chunks):
    hash = hash.decode('utf-8')
    
    file_name = f"{hash}{extension}"
    file_bytes = join_bytes(lista_chunks)

    with open(file_name,"wb") as file:
        file.write(file_bytes)
    
def write_server_ip():
    server_ip_address = input("Ingrese la dirección ip del proxy, ejemplo 192.168.10.6:5555: ")
    server_ip_address = server_ip_address.strip()
    server_address = "tcp://" + server_ip_address
    return server_address

if __name__ == "__main__":
    main()