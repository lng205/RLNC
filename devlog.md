# Devlog

## mystreamc.py

- The C code uses a ring buffer to store the packets. The ported code uses a Python list to store the packets because storage efficiency is not a concern.
- The C code uses shared random seed to generate random numbers. This evades the issue of passing the random coefficients with undetermined length in the packets, but it cannot handle the recoding of the packets.
- IDEA: The receiver would ack the newest source packet id it has decoded, so the sender would actually know a packet miss when a packet is acked twice. This resembles the TCP fast retransmit mechanism. But the current implementation simply updates the encoding window. A more sophisticated implementation would be to retransmit the missing packet immediately.
