"""
This is a python port of the C code in streamc. The porting would strive to maintain the same structure as the C code.
Streamc is a stream network coding simulator.
The C code is written in a object-oriented style with structs and functions. The python code would be written in a class-based style.
"""

import sys
import random
from encoder import Encoder
from decoder import Decoder
from model import Packet, Cp

slot = -1
T_P = 0
arrival_time = []
sent_time = []
inorder_delay = []

irreg_range = 0
irreg_snum = 0
irreg_spos = []

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
    """
    TestBernoulliFull
    """
    if len(sys.argv) < 7:
        print(USAGE)
        sys.exit(1)
    snum = int(sys.argv[1])
    arrival = float(sys.argv[2])
    cp = Cp(8, PKTSIZE, float(sys.argv[3]), 0)
    if cp.repfreq > 1:
        print(USAGE)
        sys.exit(1)

    pe = float(sys.argv[4])

    T_ACK = 1
    T_P = int(sys.argv[5])

    global irreg_range, irreg_snum, irreg_pos
    irreg_range = int(sys.argv[6])
    irreg_snum = len(sys.argv) - 7
    irreg_pos = [int(arg) for arg in sys.argv[7:]]

    queue = [0] * (T_P+1)
    feedback = [-1] * (T_P+1)

    data = open(FILE, "rb").read(snum * PKTSIZE)
    data = bytearray(data)

    ec = Encoder(cp, None, 0)
    dc = Decoder(cp)

    nuse = 0
    global arrival_time
    arrival_time = [0] * snum
    global sent_time
    sent_time = [0] * snum

    global slot
    if arrival == 0:
        for eqnsid in range(snum):
            ec.enqueue_packet(eqnsid, data[eqnsid * PKTSIZE:(eqnsid + 1) * PKTSIZE])
            arrival_time[eqnsid] = slot

    eqnsid = 0
    while dc.inorder < snum - 1:
        slot += 1
        if arrival != 0 and random.random() < arrival and len(queue) < snum:
            # There seems to contain a bug in the original C code
            ec.enqueue_packet(data[eqnsid * PKTSIZE:(eqnsid + 1) * PKTSIZE])
            arrival_time[eqnsid] = slot
            eqnsid += 1

        pkt = generate_packet(ec)
        if pkt is None:
            continue
        pktstr = pkt.serialize()
        nuse += 1
        pos1 = slot % (T_P + 1)
        if random.random() >= pe:
            queue[pos1] = pktstr
            print(f"[Channel] Non-erased packet queued at pos {pos1} of the buffer at time {slot}")
        else:
            if pkt.sourceid != -1:
                print(f"[Channel] Source packet {pkt.sourceid} erased in channel at time {slot}")
            else:
                print(f"[Channel] Repair packet {pkt.repairid} erased in channel at time {slot}")
            queue[pos1] = None

        pos2 = (slot-T_P) % (T_P+1)
        if slot >= T_P and queue[pos2] is not None:
            print(f"[Channel] Packet at pos {pos2} of the buffer is erased at time {slot} by the decoder")
            rpkt = dc.deserialize_packet(queue[pos2])
            if rpkt.repairid >= 0 and dc.active:
                print(f"[Observation] repair packet {rpkt.repairid} with EW width {rpkt.win_e-rpkt.win_s+1} arrives, and sees DW width {(dc.win_e-dc.win_s+1)*(dc.active)}")
            dc.receive_packet(rpkt)
            queue[pos2] = None

        if dc.inorder >= 0 and slot >= T_P and slot % T_ACK == 0:
            feedback[pos1] = dc.inorder
            print(f"[Decoder] Decoder feedback in-order {dc.inorder} at time {slot}")
            if slot >= T_P and feedback[pos2] != -1:
                print(f"[Encoder] Encoder processes in-order feedback {feedback[pos2]} at time {slot}")
                feedback[pos2] = -1

    correct = 1
    for i in range(snum):
        if data[i * PKTSIZE:(i + 1) * PKTSIZE] != dc.recovered[i]:
            correct = 0
            print(f"[Warning] recovered {i} is NOT identical to original.")

    if correct:
        print("[Summary] All source packets are recovered correctly")
        print(f"[Summary] snum: {snum}, repfreq: {cp.repfreq:.3f}, erasure: {pe:.3f}, nuses: {nuse}")


def generate_packet(ec: Encoder) -> Packet:
    if ec.nextsid > len(ec.srcpkt):
        return None
    if time_to_send_repair(ec):
        pkt = ec.output_repair_packet()
    else:
        pkt = ec.output_source_packet()
        sent_time[pkt.sourceid] = slot
    return pkt

def time_to_send_repair(ec: Encoder) -> bool:
    if irreg_range != 0:
        sent = ec.nextsid + ec.rcount
        if ec.nextsid >= len(ec.srcpkt):
            return True
        match = 0
        for i in range(0, irreg_snum):
            if sent % irreg_range == irreg_spos[i]:
                match = 1
                break
        if ec.nextsid > 0 and match == 0:
            return True

        return False

    else:
        if ec.nextsid >= len(ec.srcpkt) or \
            (ec.nextsid > 0 and ec.cp.repfreq < 1 and random.random() < ec.cp.repfreq) or \
            (ec.nextsid > 0 and ec.cp.repfreq >= 1 and (ec.count+1) % (ec.cp.repfreq+1) == 0):
            return True
        else:
            return False


if __name__ == "__main__":
    main()