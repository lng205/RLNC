import random
import galois
GF = galois.GF(2**8)

class Packet:
    def __init__(self, sourceid: int, repairid: int, win_s: int, win_e: int, coes: galois.FieldArray, syms: galois.FieldArray):
        self.sourceid = sourceid
        self.repairid = repairid
        self.win_s = win_s
        self.win_e = win_e
        self.coes = coes
        self.syms = syms

    def serialize(self) -> bytes:
        sourceid = self.sourceid.to_bytes(4, byteorder="big", signed=True)
        repairid = self.repairid.to_bytes(4, byteorder="big", signed=True)
        win_s = self.win_s.to_bytes(4, byteorder="big", signed=True)
        win_e = self.win_e.to_bytes(4, byteorder="big", signed=True)
        syms = self.syms.tobytes()
        return sourceid + repairid + win_s + win_e + syms

    @classmethod
    def deserialize(cls, data: bytes) -> "Packet":
        sourceid = int.from_bytes(data[:4], byteorder="big", signed=True)
        repairid = int.from_bytes(data[4:8], byteorder="big", signed=True)
        win_s = int.from_bytes(data[8:12], byteorder="big", signed=True)
        win_e = int.from_bytes(data[12:16], byteorder="big", signed=True)
        if sourceid == -1:
            coes = GF.Random(win_e-win_s, seed=repairid).reshape(1, -1)
        else:
            coes = None
        syms = GF(list(data[16:]))
        return cls(sourceid, repairid, win_s, win_e, coes, syms)


class Encoder:
    def __init__(self, pktsize, repfreq):
        self.pktsize = pktsize
        self.repfreq = repfreq
        self.srcpkt = []
        self.count = 0
        self.nextsid = 0
        self.rcount = 0
        self.headsid = 0

    def enqueue(self, data):
        self.srcpkt.append(data)

    def output_source_packet(self):
        syms = GF(list(self.srcpkt[self.nextsid]))
        pkt = Packet(self.nextsid, -1, 0, 0, None, syms)

        self.count += 1
        self.nextsid += 1
        return pkt

    def output_repair_packet(self):
        win_s = self.headsid
        win_e = self.nextsid
        repairid = self.rcount

        coes = GF.Random(win_e-win_s, seed=repairid).reshape(1, -1)
        syms_all = GF([list(row) for row in self.srcpkt[win_s:win_e]])
        syms = coes @ syms_all
        pkt = Packet(-1, repairid, win_s, win_e, coes, syms)

        self.count += 1
        self.rcount += 1
        return pkt

    def flush_acked_packets(self, ack_sid):
        if ack_sid >= self.headsid:
            self.headsid = ack_sid + 1

    def generate_packet(self):
        if self.headsid == len(self.srcpkt):
            return None

        if self.nextsid >= len(self.srcpkt) or random.random() < self.repfreq:
            return self.output_repair_packet()
        else:
            return self.output_source_packet()


class Decoder:
    def __init__(self, pktsize, repfreq):
        self.pktsize = pktsize
        self.repfreq = repfreq
        self.inorder = -1
        self.recovered = []

    def receive_packet(self, pkt: Packet) -> None:
        pass