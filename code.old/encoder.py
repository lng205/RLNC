"""
The C version of the code uses a ring buffer as a list datastructure, which is not necessary in python
"""
import random
import mygalois
from model import Packet, Cp

class Encoder:
    def __init__(self, cp: Cp, buf, nbytes) -> None:
        """
        count: number of sent packets
        nextsid: next source packet id
        rcount: number of sent repair packets
        srcpkt: available source packets for encoding
        """
        self.cp = cp
        self.count = 0
        self.nextsid = 0
        self.rcount = 0
        if nbytes == 0:
            self.srcpkt: list[bytes] = []
            self.snum = 0
            self.head = -1
            self.headsid = -1
        else:
            pass

    def enqueue_packet(self, sourcesid, syms: bytes) -> None:
        if self.head == -1:
            self.srcpkt.append(syms)
            self.head = 0
            self.headsid = sourcesid
            self.snum += 1
            return
        self.srcpkt.append(syms)

    def output_source_packet(self) -> Packet:
        packet = Packet(self.nextsid, -1, syms=self.srcpkt[self.nextsid])
        self.count += 1
        self.nextsid += 1
        return packet

    def _output_repair_packet(self, win_s, win_e) -> Packet:
        repairid = self.rcount

        random.seed(repairid)
        coes = [random.randint(0, 255) for _ in range(win_e - win_s)]

        syms = bytearray([0] * self.cp.pktsize)
        for i in range(win_s, win_e):
            mygalois.multiply_add_region(syms, self.srcpkt[i], coes[i - win_s])

        packet = Packet(-1, repairid, win_s=win_s, win_e=win_e, coes=bytes(coes), syms=bytes(syms))
        self.rcount += 1

        return packet
    
    def output_repair_packet(self) -> Packet:
        if self.headsid == self.nextsid:
            return self._output_repair_packet(self.headsid, self.nextsid)
        else:
            return self._output_repair_packet(self.headsid, self.nextsid-1)
        
    def output_repair_packet_short(ew_width) -> Packet:
        pass


    def flush_acked_packets(self, ack_sid) -> None:
        pass