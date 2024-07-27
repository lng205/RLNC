import galois

GF = galois.GF(2**8)

def multiply_add_region(dst: bytearray, src: bytearray, coe: int) -> None:
    """
    Multiply a Vecotor by a constant and add the result to another Vector.
    D += cS
    """
    for i in range(len(dst)):
        dst[i] = GF(int(dst[i])) + GF(int(src[i])) * GF(coe)

def divide(a: bytes, b: bytes) -> int:
    quotient = GF(int(a)) / GF(int(b))
    return int(quotient)