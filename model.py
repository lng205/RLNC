import random
import galois

GF = galois.GF(2**8)

# ANSI escape codes
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

class Packet:
    """
    sourceid: source packet id
    repairid: repair packet id, -1 if source packet
    win_s: start of repair encoding window
    win_e: end of repair encoding window
    coes: encoding coefficients
    syms: source or coded symbols
    """
    def __init__(self, sourceid, repairid, win_s=None, win_e=None, coes=None, syms=None) -> None:
        self.sourceid = sourceid
        self.repairid = repairid
        self.win_s = win_s
        self.win_e = win_e
        self.coes: list[bytes] = coes
        self.syms: list[bytes] = syms

    def __str__(self) -> str:
        syms = " ".join(f"{byte:02x}" for byte in self.syms)
        if self.repairid == -1:
            return f"{YELLOW} Source Packet {self.sourceid}: {RESET} {syms}"
        else:
            coes = RED + " ".join(f"{byte:02x}" for byte in self.coes) + RESET
            return f"{YELLOW} Repair Packet {self.repairid} ({self.win_s}-{self.win_e}): {RESET} {coes} {syms}"


class Encoder:
    def __init__(self, packet_size) -> None:
        """
        count: number of sent packets
        nextsid: next source packet id
        rcount: number of sent repair packets
        srcpkt: available source packets for encoding
        """
        self.packet_size = packet_size
        self.count = 0
        self.nextsid = 0
        self.rcount = 0
        self.srcpkt: list[list[bytes]] = []

    def enqueue_packet(self, syms: list[bytes]) -> None:
        self.srcpkt.append(syms)

    def output_source_packet(self) -> Packet:
        packet = Packet(self.nextsid, -1, syms=self.srcpkt[self.nextsid])
        self.count += 1
        self.nextsid += 1
        return packet

    def output_repair_packet(self, win_s, win_e) -> Packet:
        coes = [random.randint(0, 255) for _ in range(win_e - win_s)]
        syms = []
        for i in range(self.packet_size):
            sym = GF(0)
            for j in range(win_s, win_e):
                src = GF(int(self.srcpkt[j][i]))
                coe = GF(coes[j - win_s])
                sym += src * coe
            syms.append(int(sym))
        packet = Packet(-1, self.rcount, win_s=win_s, win_e=win_e, coes=bytes(coes), syms=bytes(syms))
        self.rcount += 1
        return packet

    def flush_acked_packets(self, ack_sid) -> None:
        self.ack_sid = ack_sid


class Decoder:
    pass