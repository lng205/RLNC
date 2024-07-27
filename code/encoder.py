import random
import mygalois
from model import Packet

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

        syms = bytearray([0] * self.pktsize)
        for i in range(win_s, win_e):
            mygalois.multiply_add_region(syms, self.srcpkt[i], coes[i - win_s])

        packet = Packet(-1, repairid, win_s=win_s, win_e=win_e, coes=bytes(coes), syms=bytes(syms))
        self.rcount += 1

        return packet

    def flush_acked_packets(self, ack_sid) -> None:
        self.ack_sid = ack_sid
