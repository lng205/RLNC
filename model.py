import random
import galois

GF = galois.GF(2**8)

# ANSI escape codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

class Packet:
    def __init__(self, sourceid, repairid, win_s=0, win_e=0, coes=b'', syms=b'') -> None:
        """
        sourceid: source packet id
        repairid: repair packet id, -1 if source packet
        win_s: start of repair encoding window
        win_e: end of repair encoding window
        coes: encoding coefficients
        syms: source or coded symbols
        """
        self.sourceid: int = sourceid
        self.repairid: int = repairid
        self.win_s: int = win_s
        self.win_e: int = win_e
        self.coes: bytes = coes
        self.syms: bytes = syms

    def serialize(self) -> bytes:
        """
        Convert the packet to bytes
        MTU of Ethernet is 1500 Bytes
        coe is assumed to be generated at the decoder using the same random seed (This approach doesn't support recoding)
        """
        sourceid = self.sourceid.to_bytes(4, byteorder="big", signed=True)
        repairid = self.repairid.to_bytes(4, byteorder="big", signed=True)
        win_s = self.win_s.to_bytes(4, byteorder="big", signed=True)
        win_e = self.win_e.to_bytes(4, byteorder="big", signed=True)
        return sourceid + repairid + win_s + win_e + self.syms

    def __str__(self) -> str:
        syms = " ".join(f"{byte:02x}" for byte in self.syms)
        if self.repairid == -1:
            return f"{YELLOW} Source Packet {self.sourceid}: {RESET} {syms}"
        else:
            coes = RED + " ".join(f"{byte:02x}" for byte in self.coes) + RESET
            return f"{YELLOW} Repair Packet {self.repairid} ({self.win_s}-{self.win_e}): {RESET} {coes} {syms}"


class Encoder:
    def __init__(self, pktsize) -> None:
        """
        count: number of sent packets
        nextsid: next source packet id
        rcount: number of sent repair packets
        srcpkt: available source packets for encoding
        """
        self.pktsize = pktsize
        self.count = 0
        self.nextsid = 0
        self.rcount = 0
        self.srcpkt: list[bytes] = []

    def enqueue_packet(self, syms: bytes) -> None:
        self.srcpkt.append(syms)

    def output_source_packet(self) -> Packet:
        packet = Packet(self.nextsid, -1, syms=self.srcpkt[self.nextsid])
        self.count += 1
        self.nextsid += 1
        return packet

    def output_repair_packet(self, win_s, win_e) -> Packet:
        repairid = self.rcount

        random.seed(repairid)
        coes = [random.randint(0, 255) for _ in range(win_e - win_s)]

        syms = []
        for i in range(self.pktsize):
            sym = GF(0)
            for j in range(win_s, win_e):
                src = GF(int(self.srcpkt[j][i]))
                coe = GF(coes[j - win_s])
                sym += src * coe
            syms.append(int(sym))

        packet = Packet(-1, repairid, win_s=win_s, win_e=win_e, coes=bytes(coes), syms=bytes(syms))
        self.rcount += 1

        return packet

    def flush_acked_packets(self, ack_sid) -> None:
        self.ack_sid = ack_sid


class Decoder:
    def __init__(self, pktsize) -> None:
        """
        
        """
        self.activate: bool = False
        self.pktsize = pktsize
        self.inorder = -1
        self.win_s = -1
        self.win_e = -1
        self.dof = 0
        self.row = []
        self.message = []
        self.recovered = []
        self.prev_rep = -1

    def deserialize_packet(self, packet: bytes) -> Packet:
        sourceid = int.from_bytes(packet[:4], byteorder="big", signed=True)
        repairid = int.from_bytes(packet[4:8], byteorder="big", signed=True)
        win_s = int.from_bytes(packet[8:12], byteorder="big", signed=True)
        win_e = int.from_bytes(packet[12:16], byteorder="big", signed=True)

        random.seed(repairid)
        coes = [random.randint(0, 255) for _ in range(win_e - win_s)]

        syms = packet[16:]

        return Packet(sourceid, repairid, win_s, win_e, bytes(coes), syms)

    def receive_packet(self, pkt: Packet) -> None:
        if pkt.repairid == -1:
            self.prev_rep = pkt.repairid
        if not self.activate:
            # In-Order Receiving
            if pkt.sourceid >= 0:
                # Source Packet
                if pkt.sourceid <= self.inorder:
                    print(f"{YELLOW} [Decoder] Receive out-dated source packet: {pkt.sourceid}, current inorder: {self.inorder} {RESET}")
                elif pkt.sourceid == self.inorder + 1:
                    print(f"{GREEN} [Decoder] Receive in-order source packet: {pkt.sourceid}, current inorder: {self.inorder} {RESET}")
                    self.recovered.append(pkt.syms)
                    self.inorder += 1
                else:
                    print(f"{RED} [Decoder] Receive out-of-order source packet: {pkt.sourceid}, current inorder: {self.inorder}, activating decoder...{RESET}")
                    self.activate(pkt)
            else:
                if pkt.win_e <= self.inorder:
                    print(f"{YELLOW} [Decoder] Receive out-dated repair packet across [{pkt.win_s}, {pkt.win_e}], current inorder: {self.inorder}, just ignore...{RESET}")
                else:
                    print(f"{RED} [Decoder] Receive repair packet across [{pkt.win_s}, {pkt.win_e}], current inorder: {self.inorder}, activating decoder...{RESET}")
                    self.activate(pkt)
        else:
            self.process_packet(pkt)
            if self.dof == self.win_e - self.win_s + 1:
                self.deactivate()

    def activate(self, pkt: Packet) -> None:
        pass

    def deactivate(self) -> None:
        pass

    def process_packet(self, pkt: Packet) -> None:
        pass
