import socket
import threading  # For handling clients in separate threads

class Server():
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 65432  # Listen on this port
        self.fileOwners = {}

    # Method to handle individual client connections
    def handle_client(self, conn, addr):
        print(f"Connected by {addr}")
        with conn:
            while True:
                data = conn.recv(1024).decode('utf-8')  # Receive data from the client
                if not data:
                    break
                
                #Send an acknowledgment message back to the client
                port, op, message = data.split(' ')

                response = f"{op} from {port} completed "

                if op == "RegisterRequest":
                    print(f"Server registering {message}")
                    self.RegisterRequest(port, message)
                    print(self.fileOwners)

                elif op == "FileListRequest":
                    file_list = self.FileListRequest()
                    response += file_list

                elif op == "FileLocationsRequest":
                    locations_list = self.FileLocationsRequest(message)
                    response += locations_list

                elif op == "ChunkRegisterRequest":
                    filename, chunk_id = message.split("<>")
                    self.updateOwners(port, filename, chunk_id)

                conn.send(response.encode('utf-8'))
                

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            s.listen()
            print(f"Server listening on {self.HOST}:{self.PORT}")
            
            while True:
                conn, addr = s.accept()  # Accept a new connection
                # Start a new thread to handle the client
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
    
    def RegisterRequest(self, port, message):
        fileName, length = message.split(":")
        peer = {port: set(i for i in range(int(length)))}
        self.fileOwners[fileName] = peer

    def FileListRequest(self):
        lst = list(self.fileOwners.keys())
        lst = ",".join(lst)
        return lst

    def FileLocationsRequest(self, file_name):
        file_owners = list(self.fileOwners[file_name].keys())
        response = []
        for owner in file_owners:
            curr = [f"{owner}:"]
            for chunk in self.fileOwners[file_name][owner]:
                curr.append(f"{chunk},")
            response.append(''.join(curr))
        return "-".join(response)

    def updateOwners(self, port, filename, chunk_id):
            if port not in self.fileOwners[filename]:
                self.fileOwners[filename][port] = set()
            
            self.fileOwners[filename][port].add(int(chunk_id))
