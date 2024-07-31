import sys
from model import Encoder, Packet, Decoder
import random

USAGE = """
python mystreamc.py snum repfreq epsilon Tp
snum: number of sources
repfreq: repair frequency
epsilon: erasure probability
Tp: propagation delay
"""
FILE = "/dev/urandom"
PKTSIZE = 200

def main():
    if len(sys.argv) != 5:
        print(USAGE)
        sys.exit(1)
    snum = int(sys.argv[1])
    repfreq = float(sys.argv[2])
    epsilon = float(sys.argv[3])
    Tp = int(sys.argv[4])

    slot = -1
    queue = [None] * (Tp+1)
    feedback = [None] * (Tp+1)

    datasize = snum * PKTSIZE
    with open(FILE, "rb") as f:
        data = f.read(datasize)

    ec = Encoder(PKTSIZE, repfreq)
    dc = Decoder(PKTSIZE, repfreq)

    for i in range(snum):
        ec.enqueue(data[i*PKTSIZE:(i+1)*PKTSIZE])

    while dc.inorder < snum-1:
        slot += 1
        pktstr = ec.generate_packet().serialize()

        pos1 = slot % (Tp+1)
        if random.random() < epsilon:
            queue[pos1] = None
        else:
            queue[pos1] = pktstr

        pos2 = (slot-Tp) % (Tp+1)
        if queue[pos2] is not None:
            rpkt = Packet.deserialize(queue[pos2])
            dc.receive_packet(rpkt)
            queue[pos2] = None

        if dc.inorder >= 0 and slot >= Tp:
            feedback[pos1] = dc.inorder
            if slot >= Tp and feedback[pos2] is not None:
                ec.flush_acked_packets(feedback[pos2])
                feedback[pos2] = None

    correct = True
    for i in range(snum):
        if data[i*PKTSIZE:(i+1)*PKTSIZE] != dc.recovered[i].tobytes():
            correct = False
            print()
    if correct:
        print()

if __name__ == "__main__":
    main()