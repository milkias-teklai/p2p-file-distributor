import socket
import threading
import hashlib
import time
import random
from collections import defaultdict

class Peer:
    def __init__(self, port, my_file=None):
        #Initialize peer with a port and an optionl file to share
        self.host = "127.0.0.1"
        self.port = port
        self.neededChunks = defaultdict(list)  # {chunk_id : [peer1, peer2, ...]}
        self.storage = {} #Store downloaded chunks
        self.name = self.port % 50000 #Keep track of the peer's name (just for easier logging)
        
        #If this peer has a file to share
        if my_file:
            filename = my_file.split('/')[-1]
            file_chunks = {}
            
            #Read the file and hash the chunks
            with open(my_file, 'r') as file:
                info = file.readlines()
                for i in range(len(info)):
                    #Hash the chunk
                    hash_object = hashlib.sha256()
                    hash_object.update(info[i].encode())
                    hash_hex = hash_object.hexdigest()

                    #Dictionary keeps the chunks in the form {i: (string, hashed_string)}
                    file_chunks[i] = (info[i], hash_hex)
            
            self.storage[filename] = file_chunks

    
    def handle_client(self, conn, addr):
        #Handle incoming requests from other peers
        print(f"Connected by {addr}")
        with conn:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                port, op, message = data.split(' ')

                if op == "FileChunkRequest":
                    #Provide the requested chunk. Give the appropriate hash as well
                    my_port, filename, chunk_id = message.split('-')
                    chunk = self.storage[filename][int(chunk_id)][0]
                    chunk_hash = self.storage[filename][int(chunk_id)][1]
                    response = f"{self.port}<>FileChunkReply<>{filename}^^{chunk_id}^^{chunk}^^{chunk_hash}"


                conn.send(response.encode('utf-8'))


        
    
    def start_server(self):
        #Start up the peer and listen for incoming requests
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Peer listening on {self.host} : {self.port}")
            
            while True:
                conn, addr = s.accept()
                # Start a new thread to handle the new client
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
    

    def send_to_peer(self, to_host, to_port, message):
        #Send a message to another peer
        message = f"{self.port} {message}"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as p:

            try:
                # Connect to the central server, then send a message
                p.connect((to_host, int(to_port)))
                print(f"{self.name % 50000} Sending request to peer {int(to_port) % 50000}...")
                print(message)
                p.send(message.encode('utf-8'))
                
                # Wait for a response from the peer
                response = p.recv(1024).decode('utf-8')
                peer_port, op, reply = response.split("<>")

                if op == "FileChunkReply":
                    filename, chunk_id, chunk, chunk_hash = reply.split('^^')

                    #If the hash doesn't pass the check, then don't download the file
                    if self.verifyHash(chunk, chunk_hash):
                        self.downloadChunk(filename, chunk_id, chunk, chunk_hash)
                        print(f"Peer {self.name} downloaded chunk {chunk_id} from Peer {int(peer_port) % 50000}")
                        return True
                    else:
                        return False

                    

            except ConnectionRefusedError:
                print(f"Failed to connect to peer at {to_host}:{to_port}")
            except Exception as e:
                print(f"An error occurred: {e}")        

    def send_to_server(self, message):
        #Method to connect to the central server and send a message
        message = f"{self.port} {message}"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            server_host = '127.0.0.1'
            server_port = 65432

            try:
                #Connect to the central server, then send a message
                s.connect((server_host, server_port))
                print(f"Sending message to server...")
                print(message)
                s.send(message.encode('utf-8'))
                
                # Wait for a response from the server
                response = s.recv(1024).decode('utf-8')
                parsed_response = response.split(" ")
                

                '''
                The requests each use their own parsing methodolgy.
                Depending on the requested operation, we want to parse the message differently.
                This ensured that errors would be noticed easier during development
                '''

                if parsed_response[0] == "RegisterRequest":
                    pass

                elif parsed_response[0] == "FileListRequest":
                    file_list = parsed_response[4].split(',')
                    print(f"FILE LIST: {file_list}")

                elif parsed_response[0] == "FileLocationsRequest":
                    locations = parsed_response[4].split("-")
                    print(f"FILE LOCATIONS {locations}")

                    #Save the locations of the chunks
                    for location in locations:
                        peer, chunks_ids = location.split(':')
                        self.saveLocations(peer, chunks_ids)

                    print(f" Peer {self.port % 50000} needed chunks: {self.neededChunks}")
                

                print(f"Server response: {response}")
            except ConnectionRefusedError:
                print(f"Failed to connect to server at {server_host}:{server_port}")
            except Exception as e:
                print(f"An error occurred: {e}")


    def downloadFile(self, filename):
        #Ask the server who has the file (file location request)
        self.send_to_server(f"FileLocationsRequest {filename}")

        #Loop until the file is fully downloaded
        while True:
            # Check if all chunks are already downloaded
            if filename in self.storage and len(self.storage[filename]) == len(self.neededChunks):
                print(f"Download of {filename} completed")
                break  # Exit the loop when all chunks are downloaded

            #Download any missing chunks
            for chunk_id, peer_list in self.neededChunks.items():
                # If this chunk has already been downloaded, skip it
                if filename in self.storage and chunk_id in self.storage[filename]:
                    continue

                #Choose a random peer who has the chunk and request it
                if peer_list:
                    chosen_peer = random.choice(peer_list)  # Pick an arbitrary peer
                    print(f"Requesting chunk {chunk_id} from peer {chosen_peer}")

                    #Request the chunk from the chosen peer
                    result = self.fileChunkRequest(chosen_peer, filename, chunk_id)
                    if not result:
                        print(f"Chunk {chunk_id} from Peer {chosen_peer} has failed the integrity check")

                else:
                    print(f"No peer available for chunk {chunk_id}. Retrying...")
                
                '''
                To showcase that downloads work concurrently, I've slowed down this function  with time.sleep() to allow
                for peers to be downloading at the same time on differnt threads
                '''
                time.sleep(.1)

            #Re-check to see if all chunks have been downloaded
            if filename in self.storage and len(self.storage[filename]) == len(self.neededChunks):
                print(f"All chunks for {filename} have been downloaded.")
                break
            else:
                missing_chunks = len(self.neededChunks) - len(self.storage[filename])
                print(f"Download incomplete. {missing_chunks} chunks still missing. Retrying...")
                print(f"{self.storage}")

            #Short delay so we don't bombard the server/peers
            time.sleep(1)

        #Call our function to output to our storage folder
        self.buildFile(filename)
        print(f'Peer {self.port % 50000} has built {filename}')


    def buildFile(self, filename):
        length = len(self.storage[filename])

        file = ''
        for chunk in range(length):
            file += (self.storage[filename][chunk][0])
        
        
        with open(f'peer{self.name}_storage/{filename}', 'w') as text:
            text.write(file)



    '''
    Here are some helper functions which clean up the rest of the code
    '''


    def saveLocations(self, peer, chunk_ids):
        ids = chunk_ids.split(',')[:-1]
        for id in ids:
            self.neededChunks[id].append(peer) 

    def sendRegisterRequest(self, filename):
        message = f"RegisterRequest {filename}:{len(self.storage[filename])}"
        self.send_to_server(message)
    
    def fileChunkRequest(self, port, filename, chunk):
        message = f"FileChunkRequest {port}-{filename}-{chunk}"
        return self.send_to_peer('127.0.0.1', port, message)

    def downloadChunk(self, filename, chunk_id, chunk, chunk_hash):
        #Ready up our dictionary
        if filename not in self.storage:
            self.storage[filename] = {}

        #Store the chunk alongside it's id
        self.storage[filename][int(chunk_id)] = (chunk, chunk_hash)
    
        self.ChunkRegisterRequest(filename, chunk_id)


    def ChunkRegisterRequest(self, filename, chunk_id):
        message = f"ChunkRegisterRequest {filename}<>{chunk_id}"
        self.send_to_server(message)
    
    def verifyHash(self, chunk, chunk_hash):

        #Boiler plate code for the hashing library
        hash_object = hashlib.sha256()
        hash_object.update(chunk.encode())
        hash_hex = hash_object.hexdigest()

        #Make sure the hashes match
        if hash_hex == chunk_hash:
            return True
        return False