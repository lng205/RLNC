"""
Figure 2 in the paper clearly illustrates the decoding algorithm
"""
import random
import mygalois
from model import Packet

WIN_ALLOC = 10000

class Decoder:
    def __init__(self, cp) -> None:
        self.active = 0
        self.cp = cp
        self.inorder = -1
        self.win_s = -1
        self.win_e = -1
        self.dof = 0
        self.row = [None] * WIN_ALLOC
        self.message = [None] * WIN_ALLOC
        self.recovered = [None] * WIN_ALLOC
        self.prev_rep = -1

    def deserialize_packet(self, packet: bytes) -> Packet:
        sourceid = int.from_bytes(packet[:4], byteorder="big", signed=True)
        repairid = int.from_bytes(packet[4:8], byteorder="big", signed=True)
        win_s = int.from_bytes(packet[8:12], byteorder="big", signed=True)
        win_e = int.from_bytes(packet[12:16], byteorder="big", signed=True)
        random.seed(repairid)
        coes = [random.randint(0, 255) for _ in range(win_e - win_s)]
        syms = packet[16:]
        return Packet(sourceid, repairid, win_s, win_e, bytearray(coes), syms)

    def receive_packet(self, pkt: Packet) -> None:
        if pkt.repairid == -1:
            self.prev_rep = pkt.repairid
        if not self.active:
            # In-Order Receiving
            if pkt.sourceid >= 0:
                # Source Packet
                if pkt.sourceid <= self.inorder:
                    print(f"[Decoder] Receive out-dated source packet: {pkt.sourceid}, current inorder: {self.inorder}")
                elif pkt.sourceid == self.inorder + 1:
                    print(f"[Decoder] Receive in-order source packet: {pkt.sourceid}")
                    self.recovered[pkt.sourceid] = pkt.syms
                    self.inorder += 1
                else:
                    print(f"[Decoder] Receives source packet {pkt.sourceid} but in-order is {self.inorder}, activating decoder...")
                    self.activate(pkt)
            else:
                if pkt.win_e <= self.inorder:
                    print(f"[Decoder] Receives repair packet coded across [{pkt.win_s}, {pkt.win_e}], in-order is {self.inorder}, just ignore...")
                else:
                    print(f"[Decoder] Receives repair packet coded across [{pkt.win_s}, {pkt.win_e}], in-order is {self.inorder}, activating decoder...")
                    self.activate(pkt)
        else:
            self.process_packet(pkt)
            if self.dof == self.win_e - self.win_s + 1:
                self.deactivate()

    def activate(self, pkt: Packet) -> None:
        """
        The activate method would have to build up the initial A and C in A*S=C,
        where A is the upper triangular matrix, S is the unknown source symbol vector,
        and C is the known coded symbol vector.
        """
        self.n_repair = 0 # number of repair packets received during decoder activation
        self.n_row_sub_ops = 0 # number of row operations during subtraction, reset once decoder is deactivated
        if pkt.sourceid >= 0:
            """
            A source packet triggered decoder activation
            Packets of inorder+1, inorder+2,..., sourceid-1 are missing

            Save the packet to A:
            X
              X
                ...
                    1

            Notice that the starting column's info is not needed as we are maintaining an upper triangular matrix
            """
            self.win_s = self.inorder + 1
            self.win_e = pkt.sourceid
            index = pkt.sourceid - self.win_s
            self.row[index] = [1]
            self.message[index] = pkt.syms
            self.dof = 1
            print(f"[Decoder] Activated by source packet {pkt.sourceid}")
        else:
            self.n_repair += 1
            self.win_s = self.inorder + 1
            self.win_e = pkt.win_e
            self.dof = 0

            """
            Eliminate those already in-order recovered packets from the packet
            The elements addition inverse is theirself in GF(2^p)
            Set the recovered coefficients to 0
            """
            for i in range(pkt.win_s, self.inorder+1):
                mygalois.multiply_add_region(pkt.syms, self.recovered[i], pkt.coes[i-pkt.win_s])
                pkt.coes[i-pkt.win_s] = 0
            
            """
            Insert the row into the upper triangular matrix
            Assumes the starting point of the packet's ew is earilier than the latest inorder received packet
            The row index should be the first non-zero coefficient in the eliminated coes
            """
            coes = pkt.coes[self.win_s - pkt.win_s:]
            for i in range(len(coes)):
                if coes[i] != 0:
                    self.row[i] = coes[i:]
                    self.message[i] = pkt.syms
                    self.dof = 1
            print(f"[Decoder] Decoder activated by repair packet {pkt.repairid} with encoding window: [{pkt.win_s}, {pkt.win_e}]")

        print(f"[Decoder] Decoder activated with decoding window: [{self.win_s}, {self.win_e}], DoF: {self.dof}")
        self.active = 1

        if self.dof == self.win_e - self.win_s + 1:
            self.deactivate()

    def process_packet(self, pkt: Packet) -> None:
        if (pkt.sourceid >= 0 and pkt.sourceid < self.win_s) or (pkt.repairid >= 0 and pkt.win_e < self.win_s):
            # Ignore out-dated packets
            return

        if pkt.sourceid >= 0 and pkt.sourceid > self.win_e:
            # A newer source packet beyond the current decoding window, expand the decoding window
            index = pkt.sourceid - self.win_s
            self.row[index] = [1]
            self.message[index] = pkt.syms
            self.dof += 1
            self.win_e = pkt.sourceid
            print(f"[Decoder] Processed source packet {pkt.sourceid}, decoding window [{self.win_s}, {self.win_e}], DoF: {self.dof}")
            return

        if pkt.repairid >= 0:
            # Eliminate the already recovered packets from the repair packet
            self.n_repair += 1
            for i in range(pkt.win_s, self.inorder+1):
                mygalois.multiply_add_region(pkt.syms, self.recovered[i], pkt.coes[i-pkt.win_s])
                pkt.coes[i-pkt.win_s] = 0
                self.n_row_sub_ops += 1
            if pkt.win_e > self.win_e:
                self.win_e = pkt.win_e

        # Find the index
        if pkt.sourceid >= 0:
            index = pkt.sourceid - self.win_s
            print(f"[Decoder] Processing 'lost' source packet {pkt.sourceid} ...")
        else:
            index = max((pkt.win_s - self.win_s), 0)
            # The packet may has a shorter encoding window than the current decoding window
            offset = max((self.win_s - pkt.win_s), 0)

        width = self.win_e - self.win_s + 1 - index
        if pkt.sourceid >= 0:
            coes = [1]
        else:
            coes = pkt.coes[offset:pkt.win_e - self.win_s + 1]

        # Process the effective EV to the appropriate row
        filled = -1
        for i in range(width):
            if coes[i] != 0:
                if self.row[index + i] is not None:
                    # This row already exists. Subtract the row from the packet, and leave A unchanged.
                    quotient = mygalois.divide(coes[i], self.row[index + i][0])
                    mygalois.multiply_add_region(coes[i], self.row[index + i], quotient)
                    mygalois.multiply_add_region(pkt.syms, self.message[index + i], quotient)
                else:
                    self.row[index + i] = coes[i:]
                    self.message[index + i] = pkt.syms
                    self.dof += 1
                    filled = i + index
                    break

        if pkt.sourceid >= 0:
            print(f"[Decoder] Processed source packet {pkt.sourceid}, current decoding window: [{self.win_s}, {self.win_e}], filled: {filled+self.win_s}, DoF: {self.dof}")
        else:
            print(f"[Decoder] Processed repair packet {pkt.repairid}, encoding window [{pkt.win_s}, {pkt.win_e}], current decoding window: [{self.win_s}, {self.win_e}], filled: {filled+self.win_s}, DoF: {self.dof}")

    def deactivate(self) -> None:
        width = self.win_e - self.win_s + 1
        # eliminate all nonzeros above diagonal elements from right to left
        for i in range(width-1, -1, -1):
            # i th column
            for j in range(0, i):
                # j th row
                if j + len(self.row[j]) <= i or self.row[j][i-j] == 0:
                    continue
                # c_j - a_ji / a_ii
                quotient = mygalois.divide(self.row[j][i-j], self.row[i][0])
                mygalois.multiply_add_region(self.message[j], self.message[i], quotient)
                self.row[j][i-j] = 0
            
            # convert diagonal to 1
            if self.row[i][0] != 1:
                quotient = mygalois.divide(1, self.row[i][0])
                mygalois.multiply_region(self.message[i], quotient)
                self.row[i][0] = 1
            
            # save recovered packet
            self.recovered[self.win_s + i] = self.message[i]

            self.message[i] = None
            self.row[i] = None
        
        print(f"[Decoder] Inactivating decoder with DW window [{self.win_s}, {self.win_e}] of width: {width}, new in-order: {self.win_e}, n_repair: {self.n_repair}, n_sub_row_ops: {self.n_row_sub_ops}")
        self.n_repair = 0
        self.n_row_sub_ops = 0
        self.inorder = self.win_e
        self.dof = 0
        self.win_s = -1
        self.win_e = -1
        self.active = 0