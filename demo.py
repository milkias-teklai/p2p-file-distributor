from server import Server
from peer import Peer
import threading
import time



s = Server()
peer1 = Peer(port=50001, my_file="peer1_storage/recipe.txt")
peer2 = Peer(port=50002)
peer3 = Peer(port=50003)
peer4 = Peer(port=50004)
peer5 = Peer(port=50005)
threading.Thread(target=s.start_server).start()

time.sleep(3)

threading.Thread(target=peer1.start_server).start()
threading.Thread(target=peer2.start_server).start()
threading.Thread(target=peer3.start_server).start()
threading.Thread(target=peer4.start_server).start()
threading.Thread(target=peer5.start_server).start()

time.sleep(1)

peer1.sendRegisterRequest("recipe.txt")

time.sleep(1)

threading.Thread(target=peer2.downloadFile, args=("recipe.txt",)).start()
time.sleep(.5)
threading.Thread(target=peer3.downloadFile, args=("recipe.txt",)).start()
time.sleep(.5)
threading.Thread(target=peer4.downloadFile, args=("recipe.txt",)).start()
time.sleep(.5)
threading.Thread(target=peer5.downloadFile, args=("recipe.txt",)).start()

