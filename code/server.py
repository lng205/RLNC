import socket
import threading
from model import Encoder, Packet

PKTSIZE = 180
MTU = 1500

class Server:
    """Establish a UDP connection to a server, send packets and receive acks."""
    def __init__(self, server_address: tuple[str, int], repfreq: int, file_path: str):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(server_address)
        self.encoder = Encoder(repfreq)
        self.file_path = file_path
        self._load()

    def _load(self):
        """Load the file to be sent."""
        with open(self.file_path, 'rb') as file:
            while data := file.read(PKTSIZE):
                if len(data) < PKTSIZE:
                    # Padding
                    data += b'\x00' * (PKTSIZE - len(data))
                self.encoder.enqueue(data)

    def listen(self):
        """Listen for requests from the client."""
        print("Waiting for requests...")
        _, client_address = self.sock.recvfrom(MTU)
        print(f"Received request from {client_address}")
        threading.Thread(target=self.send, args=(client_address,)).start()
        threading.Thread(target=self.receive_ack).start()

    def send(self, client_address: tuple[str, int]):
        """Send packets to the client."""
        ec = self.encoder
        while not (ec.all_sent() and ec.all_acked()):
            pkt = ec.generate_packet()
            self.sock.sendto(pkt.serialize(), client_address)
        self.sock.sendto(b'', client_address)

    def receive_ack(self):
        """Receive acks from the client."""
        ec = self.encoder
        while not (ec.all_sent() and ec.all_acked()):
            data, _ = self.sock.recvfrom(MTU)
            ack = Packet.deserialize(data)
            print(f"Received ack of pkt id {ack.repairid}")
            self.encoder.flush_acked_packets(ack.repairid)


if __name__ == "__main__":
    server = Server(('localhost', 12345), 0.1, '../data/data.txt')
    server.listen()