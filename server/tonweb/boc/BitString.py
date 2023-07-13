import sys
sys.path.append('/.../tonweb/utils/utils')
from utils.utils import bytes_to_hex


class BitString:
    def __init__(self, length):
        self.array = bytearray((0 for _ in range((length + 7) // 8)))
        self.cursor = 0
        self.length = length

    def get_free_bits(self):
        return self.length - self.cursor

    def get_used_bits(self):
        return self.cursor

    def get_used_bytes(self):
        return (self.cursor + 7) // 8

    def get(self, n):
        return (self.array[n // 8] & (1 << (7 - (n % 8)))) > 0

    def check_range(self, n):
        if n > self.length:
            raise ValueError("BitString overflow")

    def on(self, n):
        self.check_range(n)
        self.array[n // 8] |= 1 << (7 - (n % 8))

    def off(self, n):
        self.check_range(n)
        self.array[n // 8] &= ~(1 << (7 - (n % 8)))

    def toggle(self, n):
        self.check_range(n)
        self.array[n // 8] ^= 1 << (7 - (n % 8))

    def for_each(self, callback):
        max_index = self.cursor
        for x in range(max_index):
            callback(self.get(x))

    def write_bit(self, b):
        if b and b > 0:
            self.on(self.cursor)
        else:
            self.off(self.cursor)
        self.cursor += 1

    def write_bit_array(self, ba):
        for b in ba:
            self.write_bit(b)

    def write_uint(self, number, bit_length):
        number = int(number)
        if bit_length == 0 or len(bin(number)[2:]) > bit_length:
            if number == 0:
                return
            raise ValueError(
                "bit_length is too small for number,"
                f"got number={number}, bit_length={bit_length}"
            )
        s = bin(number)[2:].zfill(bit_length)
        for bit in s:
            self.write_bit(bit == '1')

    def write_int(self, number, bit_length):
        number = int(number)
        if bit_length == 1:
            if number == -1:
                self.write_bit(True)
                return
            if number == 0:
                self.write_bit(False)
                return
            raise ValueError("Bitlength is too small for number")
        else:
            if number < 0:
                self.write_bit(True)
                b = 2
                nb = b**(bit_length - 1)
                self.write_uint(nb + number, bit_length - 1)
            else:
                self.write_bit(False)
                self.write_uint(number, bit_length - 1)

    def write_uint8(self, ui8):
        self.write_uint(ui8, 8)

    def write_bytes(self, ui8):
        for byte in ui8:
            self.write_uint8(byte)

    def write_string(self, value):
        self.write_bytes(value.encode())

    def write_grams(self, amount):
        if amount == 0:
            self.write_uint(0, 4)
        else:
            amount = int(amount)
            lenght = len(hex(amount)[2:]) // 2
            self.write_uint(lenght, 4)
            self.write_uint(amount, lenght * 8)

    def write_coins(self, amount):
        self.write_grams(amount)

    def write_address(self, address):
        if address is None:
            self.write_uint(0, 2)
        else:
            self.write_uint(2, 2)
            self.write_uint(0, 1)  # TODO split addresses (anycast)
            self.write_int(address.wc, 8)
            self.write_bytes(address.hashPart)

    def write_bit_string(self, another_bit_string):
        another_bit_string.for_each(lambda x: self.write_bit(x))

    def clone(self):
        result = BitString(0)
        result.array = self.array[:]
        result.length = self.length
        result.cursor = self.cursor
        return result

    def to_string(self):
        return self.to_hex()

    def get_top_upped_array(self):
        return self.clone()
