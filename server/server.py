import zmq

customers = {}

#useless
parts_chunks = list() 

def main():
    proxy_address = write_proxy_ip()
    print("Connecting to proxy server…")
    #  Conecting to proxy
    server_address = write_server_ip()
    connecting_to_the_proxy(proxy_address,server_address)
    print("Connected to proxy server")
    print("Starting management file server…")
    context = zmq.Context()
    socket_server = context.socket(zmq.REP)
    socket_server.bind(server_address)
    
    while True:
        
        #  Wait for next request from client
        message = socket_server.recv_multipart()
        if message[0] == b'save':
            save_file_chunks(message)
            socket_server.send(b'parte recibida') #b'parte recibida'
        elif message[0] == b'get':
            file_chunk_to_send = send_chunk(message[1])
            socket_server.send(file_chunk_to_send)
        elif message[0] == b'save torrent':
            save_torrent(message)
            socket_server.send(b'ok')
        elif message[0] == b'get torrent':
            file_torrent_name = message[1]
            torrent = read_file(file_torrent_name)
            socket_server.send(torrent)
            
    
def write_server_ip():
    server_ip = str(input("Ingrese la dirección ip de su computadora, ejemplo 192.168.10.6: "))
    server_ip = server_ip.strip()
    server_puerto = str(input("Ingrese el puerto a usar, ejemplo 7777, recuerde que no debe usar un puerto usado por otro servicio: "))
    server_puerto = server_puerto.strip()
    server_address = "tcp://" + server_ip + ":" + server_puerto
    return server_address
    
def write_proxy_ip():
    proxy_ip = str(input("Ingrese la dirección ip del proxy, ejemplo 192.168.10.1: "))
    proxy_ip = proxy_ip.strip()
    proxy_puerto = str(input("Ingrese el puerto del proxy, ejemplo 5555: "))
    proxy_puerto = proxy_puerto.strip()
    proxy_address = "tcp://" + proxy_ip + ":" + proxy_puerto
    return proxy_address
    
def save_file_chunks(message):
    hash = message[1].decode('utf-8')
    file_chunk = message[2]
    file_name = f"{hash}.txt"
    path_to_save = f"{file_name}"

    with open(path_to_save,"wb") as file:
        file.write(file_chunk)

def save_torrent(message):
    hash_torrent = message[1].decode('utf-8')
    json = message[2].decode('utf-8')
    file_name = f"{hash_torrent}.torrent"

    with open(file_name,'w') as file:
        file.write(json)
        
def if_hash(message):  #if all work good the hashes are not posible that repeat
    hash = message[1].decode('utf-8')
    if hash in customers:
        return False
    else:
        return True
    
def send_chunk(hash):
    hash = hash.decode('utf-8')
    file_name = f'{hash}.txt'
    with open(file_name,'rb') as file:
        chunk = file.read()
    return chunk
    
def connecting_to_the_proxy(proxy_address,server_address):
    context = zmq.Context() 
    
    socket_proxy = context.socket(zmq.REQ)
    socket_proxy.connect(proxy_address)
    server_send = bytes(server_address, 'utf-8')
    socket_proxy.send_multipart([b'new server',server_send])
    socket_proxy.recv_string()
    
def add_localhost(server):
    server_localhost = server.replace('*','localhost')
    return server_localhost
    
def read_file(file_name):
    file_name = file_name.decode('utf-8')
    full_file_name = f"{file_name}.torrent"
    with open(full_file_name,'rb') as file:
        file_content = file.read()
    return file_content
    
if __name__ == "__main__":
    main()