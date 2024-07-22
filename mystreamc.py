"""
This is a python port of the C code in streamc
"""

import sys
import model

USAGE = """Usage: ./programName snum arrival repfreq epsilon Tp irange pos1 pos2 ... 
                       snum     - maximum number of source packets to transmit
                       arrival  - Bernoulli arrival rate at the sending queue, value: [0, 1)
                                  0 - all source packets available before time 0
                       repfreq  - frequency of inserting repair packets
                                  random insertion of repair packets if repfreq < 1
                                  fixed-interval insertion if repfreq >= 1 (must be integer)
                       epsilon  - erasure probability of the end-to-end link
                       Tp       - propagation delay of channel
                       irange   - period of the irregular pattern (0: regular or random depending on repfreq)
                       posX     - positions sending source packets in the irregular range"""
FILE = "/dev/urandom" # Binary Input Stream
PKTSIZE = 200

def main():
    if len(sys.argv) < 7:
        print(USAGE)
        sys.exit(1)
    snum = int(sys.argv[1])
    arrival = float(sys.argv[2])
    repfreq = float(sys.argv[3])
    pe = float(sys.argv[4])
    T_P = int(sys.argv[5])
    irreg_range = int(sys.argv[6])
    irreg_pos = [int(sys.argv[i]) for i in range(7, len(sys.argv))]

    urandom = open(FILE, "rb")
    data = urandom.read(snum * PKTSIZE)

    queue: list[int] = []
    feedback: list[int] = []

    ec = model.Encoder(PKTSIZE)
    dc = model.Decoder()

    if arrival == 0:
        for i in range(snum):
            ec.enqueue_packet(data[i * PKTSIZE:(i + 1) * PKTSIZE])

    print(ec.output_source_packet())
    print(ec.output_repair_packet(3, 7))
    print(ec.output_source_packet())
    print(ec.output_source_packet())


if __name__ == "__main__":
    main()