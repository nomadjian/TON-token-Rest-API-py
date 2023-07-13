import sys
sys.path.append('/.../tonweb/utils')
from utils.utils import bytes_to_hex
from utils import Address
from .BitString import BitString


class Slice:
    def __init__(self, array, length, refs):
        self.array = array
        self.length = length
        self.read_cursor = 0

        self.refs = refs
        self.ref_cursor = 0

    def get_free_bits(self):
        return self.length - self.read_cursor

    def check_range(self, n):
        if n > self.length:
            raise ValueError("BitString overflow")

    def get(self, n):
        self.check_range(n)
        return (self.array[n // 8] & (1 << (7 - (n % 8)))) > 0

    def load_bit(self):
        result = self.get(self.read_cursor)
        self.read_cursor += 1
        return result

    def load_bits(self, bit_length):
        result = BitString(bit_length)
        for i in range(bit_length):
            result.write_bit(self.load_bit())
        return result.array

    def load_uint(self, bit_length):
        if bit_length < 1:
            raise ValueError("Incorrect bitLength")
        s = ""
        for i in range(bit_length):
            s += "1" if self.load_bit() else "0"
        return int(s, 2)

    def load_int(self, bit_length):
        if bit_length < 1:
            raise ValueError("Incorrect bitLength")
        sign = self.load_bit()
        if bit_length == 1:
            return -1 if sign else 0
        number = self.load_uint(bit_length - 1)
        if sign:
            b = 2
            nb = b**(bit_length - 1)
            number -= nb
        return number

    def load_var_uint(self, bit_length):
        len = self.load_uint(int(int(bit_length).to_bytes(2, 'big').hex(),
                                 2).bit_length() - 1)
        if len == 0:
            return 0
        else:
            return self.load_uint(len * 8)

    def load_coins(self):
        return self.load_var_uint(16)

    def load_address(self):
        b = self.load_uint(2)
        if b == 0:
            return None  # null address
        if b != 2:
            raise ValueError("unsupported address type")
        if self.load_bit():
            raise ValueError("unsupported address type")
        wc = self.load_int(8)
        hash_part = self.load_bits(256)
        return Address(f"{wc}:{bytes_to_hex(hash_part)}")

    def load_ref(self):
        if self.ref_cursor >= 4:
            raise ValueError("refs overflow")
        result = self.refs[self.ref_cursor]
        self.ref_cursor += 1
        return result
    