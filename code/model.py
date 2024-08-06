import random
import galois
from typing import Union
import numpy as np
GF = galois.GF(2**8)


class Queue:
    """A queue datastructure implementation using a circular buffer."""
    def __init__(self, capacity=1024):
        self.capacity = capacity
        self.data = [None] * capacity
        self.head = 0
        self.tail = 0
        self.size = 0

    def enqueue(self, item):
        self.data[self.tail] = item
        self.tail = (self.tail + 1) % self.capacity
        self.size += 1
        if self.size == self.capacity:
            self._enlarge()

    def dequeue(self):
        if self.size == 0:
            raise ValueError("Queue is empty")
        item = self.data[self.head]
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return item

    def __getitem__(self, index: Union[int, slice]):
        """random access"""
        if isinstance(index, int):
            if index < 0:
                index += self.size
            if index < 0 or index >= self.size:
                raise IndexError("Index out of range")
            return self.data[(self.head + index) % self.capacity]
        elif isinstance(index, slice):
            start = index.start or 0
            stop = index.stop or self.size
            step = index.step or 1
            return [self[i] for i in range(start, stop, step)]
        else:
            raise TypeError("Index must be an integer or a slice")

    def _enlarge(self):
        new_capacity = self.capacity * 2
        new_data = [None] * new_capacity
        for i in range(self.size):
            new_data[i] = self.data[(self.head + i) % self.capacity]
        self.data = new_data
        self.head = 0
        self.tail = self.size
        self.capacity = new_capacity

    def __len__(self):
        return self.size


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

    def __str__(self) -> str:
        if self.sourceid >= 0:
            return f"Source Packet {self.sourceid}"
        else:
            return f"Repair Packet [{self.win_s}, {self.win_e})"


class Encoder:
    def __init__(self, repfreq: int):
        self.repfreq = repfreq
        self.srcpkt = Queue()
        self.nextsid: int = 0
        self.acksid: int = -1
        self.rcount: int = -1

    def enqueue(self, data: bytes):
        self.srcpkt.enqueue(data)

    def generate_packet(self) -> Packet:
        all_acked: bool = self.acksid + 1 == self.nextsid
        all_sent: bool = self.nextsid - self.acksid - 1 == len(self.srcpkt)

        if all_acked:
            pkt = self._output_source_packet(self.nextsid)
            self.nextsid += 1
        elif random.random() < self.repfreq or all_sent:
            self.rcount += 1
            pkt = self._output_repair_packet(self.rcount, self.acksid + 1, self.nextsid)
        else:
            pkt = self._output_source_packet(self.nextsid)
            self.nextsid += 1
        return pkt

    def _output_source_packet(self, sourceid: int) -> Packet:
        syms = GF(list(self.srcpkt[sourceid - self.acksid - 1]))
        return Packet(sourceid, -1, -1, -1, None, syms)

    def _output_repair_packet(self, repairid, win_s, win_e) -> Packet:
        coes = GF.Random(win_e-win_s, seed=repairid).reshape(1, -1)
        syms_all = GF([list(row) for row in self.srcpkt[:(win_e - win_s)]])
        syms = coes @ syms_all
        return Packet(-1, repairid, win_s, win_e, coes, syms)

    def flush_acked_packets(self, acksid: int) -> None:
        if acksid > self.acksid:
            for _ in range(acksid - self.acksid):
                self.srcpkt.dequeue()
            self.acksid = acksid


class Decoder:
    def __init__(self):
        self.inorder = -1
        self.recovered:list[galois.FieldArray] = []
        self.active = False
        self.win_s = -1
        self.win_e = -1
        self.coes = None
        self.messages = None

    def receive_packet(self, pkt: Packet) -> None:
        if self._is_outdated(pkt):
            return
        if self.active:
            self._process_packet(pkt)
        elif pkt.sourceid == self.inorder + 1:
            self.recovered.append(pkt.syms)
            self.inorder += 1
        else:
            self._activate(pkt)

    def _is_outdated(self, pkt: Packet) -> bool:
        if pkt.sourceid >= 0:
            return pkt.sourceid <= self.inorder
        else:
            return pkt.win_e <= self.inorder + 1 and pkt.win_s <= self.inorder

    def _activate(self, pkt: Packet) -> None:
        if pkt.sourceid >= 0:
            self.active = True
            self.win_s = self.inorder + 1
            self.win_e = pkt.sourceid + 1
            coes = GF(np.pad([1], (pkt.sourceid - self.inorder - 1, 0)))
            self.coes = coes.reshape(1, -1)
            self.messages = pkt.syms
        else:
            coes, syms = self._process_repair_packet(pkt)
            if len(coes) == 1:
                self.recovered.append(syms / coes[0])
                self.inorder = pkt.win_e - 1
                return

            self.active = True
            self.win_s = self.inorder + 1
            self.win_e = pkt.win_e
            self.coes = coes.reshape(1, -1)
            self.messages = syms

    def _process_packet(self, pkt: Packet) -> None:
        if pkt.sourceid >= 0:
            pad_left = pkt.sourceid - self.win_s
            pad_right = max(0, self.win_e - pkt.sourceid - 1)
            coes = GF(np.pad([1], (pad_left, pad_right)))
            syms = pkt.syms
        else:
            coes, syms = self._process_repair_packet(pkt)

        # extend the decoding window
        delta = len(coes) - self.coes.shape[1]
        if delta > 0:
            self.coes = GF(np.pad(self.coes, ((0, 0), (0, delta))))
            self.win_e = self.win_e + delta

        coes_new = GF(np.vstack((self.coes, coes.reshape(1, -1))))
        if np.linalg.matrix_rank(coes_new) != coes_new.shape[0]:
            # linearly dependent
            return

        self.coes = coes_new
        self.messages = GF(np.vstack((self.messages, syms)))

        if self.coes.shape[0] == self.coes.shape[1]:
            self.active = False
            decoded = np.linalg.inv(self.coes) @ self.messages
            for row in decoded:
                self.recovered.append(row)
            self.inorder = len(self.recovered) - 1
            self.win_s = -1
            self.win_e = -1
            self.coes = None
            self.messages = None

    def _process_repair_packet(self, pkt: Packet) -> tuple[galois.FieldArray, galois.FieldArray]:
        win_s = self.inorder + 1
        cut_left = win_s - pkt.win_s
        if cut_left > 0:
            A = pkt.coes[:cut_left].reshape(1, -1)
            B = self.recovered[pkt.win_s:win_s]
            coes = pkt.coes[cut_left:]
            syms = pkt.syms - (GF(A) @ GF(B)).reshape(-1)
        else:
            coes = pkt.coes
            syms = pkt.syms

        pad_left = max(0, pkt.win_s - win_s)
        if self.win_e >= 0:
            pad_right = max(0, self.win_e - pkt.win_e)
        else:
            pad_right = 0
        coes = GF(np.pad(coes, (pad_left, pad_right)))

        return coes, syms