import socket
from model import Decoder, Packet

PKTSIZE = 180
MTU = 1500

class Client:
    """Establish a UDP connection to a server, receive packets and send acks."""
    def __init__(self, server_address: tuple[str, int], file_path: str):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.decoder = Decoder()
        self.file_path = file_path
        self.server_address = server_address

    def receive(self):
        """Receive packets from the server."""
        while True:
            data, server_address = self.sock.recvfrom(MTU)
            pkt = Packet.deserialize(data)
            if pkt.sourceid == -2:
                print(f"Received end signal from {server_address}")
                break
            print(f"Received packet from {server_address}")
            self.decoder.receive_packet(pkt)
            self.send_ack(server_address)
        with open(self.file_path, 'wb') as file:
            for data in self.decoder.recovered:
                file.write(data.tobytes())
            # Unpadding: strip trailing zeros
            pass

    def send_ack(self, server_address: tuple[str, int]):
        """Send acks to the server."""
        ack = Packet(-1, self.decoder.inorder)
        self.sock.sendto(ack.serialize(), server_address)
        print(f"Sent ack to {server_address}. Inorder: {self.decoder.inorder}")

    def run(self):
        """Run the client."""
        self.sock.sendto(b'CONNECT', self.server_address)
        self.receive()


if __name__ == "__main__":
    client = Client(('localhost', 12345), '../data/data_received.txt')
    client.run()