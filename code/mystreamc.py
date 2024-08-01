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

    ec = Encoder(repfreq)
    dc = Decoder()

    for i in range(snum):
        ec.enqueue(data[i*PKTSIZE:(i+1)*PKTSIZE])

    while dc.inorder < snum-1:
        slot += 1

        # enqueue to the cyclic buffer
        pos1 = slot % (Tp+1)
        pkt = ec.generate_packet()
        if random.random() < epsilon:
            queue[pos1] = None
            print(f"[Channel]   Packet at slot {slot} is lost")
        else:
            queue[pos1] = pkt.serialize()
            print(f"[Channel]   {str(pkt)} is sent")

        # delayed receiving
        pos2 = (slot-Tp) % (Tp+1)
        if queue[pos2] is not None:
            dc.receive_packet(Packet.deserialize(queue[pos2]))
            queue[pos2] = None

        # lossless feedback
        if dc.inorder >= 0 and slot >= Tp:
            feedback[pos1] = dc.inorder
            print(f"[Feedback]  Acknowledgement for {feedback[pos1]} is sent")
            if slot >= Tp and feedback[pos2] is not None:
                ec.flush_acked_packets(feedback[pos2])
                feedback[pos2] = None

    # check the correctness
    correct = True
    for i in range(snum):
        if data[i*PKTSIZE:(i+1)*PKTSIZE] != dc.recovered[i].tobytes():
            correct = False
            print(f"[Summary]   Source packet {i} is not identical to the original")
    if correct:
        print("[Summary]    All source packets are recovered correctly")

if __name__ == "__main__":
    main()