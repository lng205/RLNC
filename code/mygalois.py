import galois

GF = galois.GF(2**8)

def multiply_add_region(dst: bytearray, src: bytearray, coe: int) -> None:
    """
    Multiply a Vecotor by a constant and add the result to another Vector.
    D += cS
    """
    # convert to list of GF elements
    dst = [GF(int(x)) for x in dst]
    src = [GF(int(x)) for x in src]
    coe = GF(coe)
    for i in range(len(dst)):
        dst[i] = dst[i] + src[i] * coe
    # convert back to bytearray
    dst = bytearray(dst)
    src = bytearray(src)

def divide(a: bytes, b: bytes) -> int:
    quotient = GF(int(a)) / GF(int(b))
    return int(quotient)

def multiply_region(src: bytearray, multiplier: int) -> None:
    """
    Multiply a Vector by a constant.
    D = cS
    """
    for i in range(len(src)):
        src[i] = GF(int(src[i])) * GF(multiplier)