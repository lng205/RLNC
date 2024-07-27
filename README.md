# MyStreamC.py

MyStreamC.py is a Python port of the [streamc](https://github.com/yeliqseu/streamc) project, implementing the code from Prof. Li's paper:

> [Y. Li, X. Chen, Y. Hu, R. Gao, J. Wang, and S. Wu, "Low-Complexity Streaming Forward Erasure Correction for Non-Terrestrial Networks," IEEE Transactions on Communications, 2023](https://ieeexplore.ieee.org/document/10246292)

## Overview

Stream Coding is an algorithm based on erasure codes (e.g., RS, LDPC, Raptor, RLNC). It aims to ensure reliable delivery when the acknowledgment channel is poor (e.g., long RTT, high packet loss rate, unidirectional link). Prof. Li's paper references [this paper](https://ieeexplore.ieee.org/document/5729366) as the foundational streaming code algorithm. The On-the-Fly Gaussian Elimination is key to the algorithm, which maintains an upper triangular matrix in the decoder.

### Key Concepts

- **Sliding Window**: The algorithm maintains a sliding window of packets. The sender inserts repair packets into the stream to protect the packets within this window.
- **Repair Packets**: The receiver uses these packets to recover lost packets within the window and sends feedback to the sender to indicate the decoder's state.
- **Reliable Delivery**: Similar to TCP, the algorithm aims to provide in-order and reliable packet delivery. This makes it feasible to implement as a [TCP Performance Enhancement Proxy](https://github.com/yeliqseu/pepesc).
- **Encoding Window Optimization**: Since the sender may not know the receiver's current state, it tends to maintain a large encoding window. Prof. Li's paper proposes mixing short packets randomly into the stream to reduce the encoding window size, which is an optimization to improve efficiency.

## Usage

Execute `pip install -r requirements.txt` to install the required dependencies.

- A debug configuration for VSCode is provided in `.vscode/launch.json`.
- Execute `python3 code/mystreamc.py` to see the script's usage instructions.

Feel free to explore the code and contribute feedback or improvements!

## Roadmap

1. A direct port of the original C code
    - [x] Encoder
    - [ ] Decoder
    - [ ] Example-TestBernoulliFull

2. Further improvements
    - [ ] Use numpy for matrix operations (Module `galois` is compatible with numpy)
    - [ ] Improve the code structure and readability