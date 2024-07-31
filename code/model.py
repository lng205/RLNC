import random
import galois
import numpy as np
GF = galois.GF(2**8)

class Packet:
    def __init__(
        self,
        sourceid: int,
        repairid: int,
        win_s: int,
        win_e: int,
        coes: galois.FieldArray,
        syms: galois.FieldArray
    ):
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
        coes = GF.Random(win_e - win_s, seed=repairid) if sourceid == -1 else None
        syms = GF(list(data[16:]))
        return cls(sourceid, repairid, win_s, win_e, coes, syms)


class Encoder:
    def __init__(self, repfreq: int):
        self.repfreq = repfreq
        self.srcpkt: list[bytes] = []
        self.nextsid: int = 0
        self.acksid: int = 0
        self.rcount: int = 0

    def enqueue(self, data: bytes):
        self.srcpkt.append(data)

    def generate_packet(self):
        if self.nextsid >= len(self.srcpkt) or random.random() < self.repfreq:
            return self.output_repair_packet()
        else:
            return self.output_source_packet()

    def output_source_packet(self):
        self.nextsid += 1
        syms = GF(list(self.srcpkt[self.nextsid]))
        return Packet(self.nextsid, -1, -1, -1, None, syms)

    def output_repair_packet(self):
        """The encoding window is [acksid+1, nextsid)."""
        self.rcount += 1

        win_s = self.acksid + 1
        win_e = self.nextsid
        repairid = self.rcount

        coes = GF.Random(win_e-win_s, seed=repairid).reshape(1, -1)
        syms_all = GF([list(row) for row in self.srcpkt[win_s:win_e]])
        syms = coes @ syms_all
        return Packet(-1, repairid, win_s, win_e, coes, syms)

    def flush_acked_packets(self, acksid: int) -> None:
        if acksid > self.acksid:
            self.acksid = acksid


class Decoder:
    def __init__(self):
        self.inorder = -1
        self.recovered:list[galois.FieldArray] = []
        self.active = False

    def receive_packet(self, pkt: Packet) -> None:
        if self.is_outdated(pkt):
            return
        if self.active:
            self.process_packet(pkt)
        elif pkt.sourceid == self.inorder + 1:
            self.recovered.append(pkt.syms)
            self.inorder += 1
        else:
            self.activate(pkt)

    def is_outdated(self, pkt: Packet) -> bool:
        if pkt.sourceid >= 0:
            return pkt.sourceid <= self.inorder
        else:
            return pkt.win_e <= self.inorder + 1

    def activate(self, pkt: Packet) -> None:
        if pkt.sourceid >= 0:
            win_e = pkt.sourceid + 1
            coes = GF(np.pad([1], (pkt.sourceid - self.inorder - 1, 0)))
        else:
            win_e = pkt.win_e
            coes = pkt.coes

        self.active = True
        self.win_s = self.inorder + 1
        self.win_e = win_e
        self.coes = coes.reshape(1, -1)
        self.messages = pkt.syms

    def process_packet(self, pkt: Packet) -> None:
        if pkt.sourceid >= 0:
            extend_length = pkt.sourceid - self.win_e + 1
            if extend_length > 0:
                self.coes = GF(np.pad(self.coes, ((0, 0), (0, extend_length))))
                self.win_e = pkt.sourceid + 1
            pad_left = pkt.sourceid - self.win_s
            pad_right = self.win_e - pkt.sourceid - 1
            coes = GF(np.pad([1], (pad_left, pad_right)))
            syms = pkt.syms
        else:
            coes = pkt.coes
            syms = pkt.syms
            width = self.win_s - pkt.win_s
            if width > 0:
                syms -= GF(coes[:width]) @ GF(self.recovered[pkt.win_s:self.win_s])
                coes = coes[width:]

            if pkt.win_e > self.win_e:
                self.coes = GF(np.pad(self.coes, ((0, pkt.win_e-self.win_e), (0, 0))))
                self.win_e = pkt.win_e
            elif pkt.win_e < self.win_e:
                coes = GF(np.pad(coes, ((0, self.win_e-pkt.win_e), (0, 0))))

        coes_new = GF(np.vstack((self.coes, coes)))
        if np.linalg.matrix_rank(coes_new) == coes_new.shape[0]:
            self.coes = coes_new
        self.messages = GF(np.vstack((self.messages, syms)))

        if self.coes.shape[0] == self.coes.shape[1]:
            self.deactivate()

    def deactivate(self) -> None:
        self.active = False
        self.win_s = -1
        self.win_e = -1
        self.coes = None
        self.messages = None
        self.recovered.append(self.messages @ np.linalg.inv(self.coes))
        self.inorder = len(self.recovered) - 1