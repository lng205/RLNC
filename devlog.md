# Devlog

## mystreamc.py

- The C code uses a ring buffer to store the packets. The ported code uses a Python list to store the packets because storage efficiency is not a concern.

- The C code uses shared random seed to generate random numbers. This evades the issue of passing the random coefficients with undetermined length in the packets, but it cannot handle the recoding of the packets.

- IDEA: The receiver would ack the newest source packet id it has decoded, so the sender would actually know a packet miss when a packet is acked twice. This resembles the TCP fast retransmit mechanism. But the current implementation simply updates the encoding window. A more sophisticated implementation would be to retransmit the missing packet immediately.

- The original galois_multiply_add_region is multiplying each byte of a list of bytes with a single byte, and add the result to another list of bytes.

- It's worth to notice that each element is itself's additive inverse in GF(2^p), because its a field extended from GF(2) with a primitive as the root of a irreducible polynomial, and the coefficients are in GF(2). So the addition is the same as the subtraction.