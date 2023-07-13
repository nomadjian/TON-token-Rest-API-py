import base64
from .utils import crc16

BOUNCEABLE_TAG = 0x11
NON_BOUNCABLE_TAG = 0x51
TEST_FLAG = 0x80


def parse_friendly_address(address_string):
    if len(address_string) != 48:
        raise ValueError("User-friendly address should contain exactly"
                         "48 characters")

    # data = string_to_bytes(base64_to_string(address_string))
    data = (base64.b64decode(address_string)).encode()
    if len(data) != 36:
        # 1 byte tag + 1 byte workchain + 32 bytes hash + 2 byte crc
        raise ValueError("Unknown address type: byte length is"
                         "not equal to 36")

    addr = data[:34]
    crc = data[34:36]
    calced_crc = crc16(addr)
    if calced_crc != crc:
        raise ValueError("Wrong crc16 hashsum")

    tag = addr[0]
    is_test_only = False
    is_bounceable = False
    if tag & TEST_FLAG:
        is_test_only = True
        tag = tag ^ TEST_FLAG
    if tag != BOUNCEABLE_TAG and tag != NON_BOUNCABLE_TAG:
        raise ValueError("Unknown address tag")

    is_bounceable = tag == BOUNCEABLE_TAG

    workchain = None
    if addr[1] == 0xff:  # TODO: we should read signed integer here
        workchain = -1
    else:
        workchain = addr[1]
    if workchain != 0 and workchain != -1:
        raise ValueError("Invalid address wc " + str(workchain))

    hash_part = addr[2:34]
    return {"isTestOnly": is_test_only,
            "isBounceable": is_bounceable,
            "workchain": workchain,
            "hashPart": hash_part}


class Address:
    @staticmethod
    def is_valid(any_form):
        try:
            Address(any_form)
            return True
        except Exception:
            return False

    def __init__(self, any_form=None):
        if any_form is None:
            raise Exception

        if isinstance(any_form, Address):
            self.wc = any_form.wc
            self.hashPart = any_form.hashPart
            self.isTestOnly = any_form.isTestOnly
            self.isUserFriendly = any_form.isUserFriendly
            self.isBounceable = any_form.isBounceable
            self.isUrlSafe = any_form.isUrlSafe
            return
        if any_form.find('-') > 0 or any_form.find('_'):
            self.isUrlSafe = True
            any_form = any_form.replace('-', '+').replace('_', '/')
        else:
            self.isUrlSafe = False
        if ':' in any_form:
            arr = any_form.split(':')
            if len(arr) != 2:
                raise ValueError('Invalid address ' + any_form)
            wc = int(arr[0])
            if wc != 0 and wc != -1:
                raise ValueError('Invalid address wc ' + any_form)
            hex_value = arr[1]
            if len(hex_value) != 64:
                raise ValueError('Invalid address hex ' + any_form)
            self.isUserFriendly = False
            self.wc = wc
            self.hashPart = bytes.fromhex(hex_value)
            self.isTestOnly = False
            self.isBounceable = False
        else:
            self.isUserFriendly = True
            parse_result = parse_friendly_address(address_string=any_form)
            self.wc = parse_result['workchain']
            self.hashPart = parse_result['hashPart']
            self.isTestOnly = parse_result['isTestOnly']
            self.isBounceable = parse_result['isBounceable']

    def to_string(self, is_user_friendly=None, is_url_safe=None,
                  is_bounceable=None, is_test_only=None):
        if is_user_friendly is None:
            is_user_friendly = self.isUserFriendly
        if is_url_safe is None:
            is_url_safe = self.isUrlSafe
        if is_bounceable is None:
            is_bounceable = self.isBounceable
        if is_test_only is None:
            is_test_only = self.isTestOnly

        if not is_user_friendly:
            return str(self.wc) + ":" + (self.hashPart).hex()
        else:
            tag = BOUNCEABLE_TAG if is_bounceable else NON_BOUNCABLE_TAG
            if is_test_only:
                tag |= TEST_FLAG

            addr = bytearray(34)
            addr[0] = tag
            addr[1] = self.wc
            addr[2:34] = self.hashPart

            address_with_checksum = bytearray(36)
            address_with_checksum[:34] = addr
            address_with_checksum[34:] = crc16(addr)
            address_base64 = base64.b64encode(bytes(address_with_checksum)
                                              ).decode("utf-8")

            if is_url_safe:
                address_base64 = address_base64.replace('+', '-'
                                                        ).replace('/', '_')

            return address_base64
