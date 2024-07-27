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
            return YELLOW + f"Source Packet {self.sourceid}: " + RESET + syms
        else:
            coes = RED + " ".join(f"{byte:02x}" for byte in self.coes) + RESET
            return YELLOW + f"Repair Packet {self.repairid} ({self.win_s}-{self.win_e}): " + RESET + coes + " " + syms