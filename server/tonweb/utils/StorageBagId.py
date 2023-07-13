from utils.utils import hex_to_bytes, bytes_to_hex

class StorageBagId:
    @staticmethod
    def is_valid(any_form):
        try:
            StorageBagId(any_form)
            return True
        except:
            return False

    def __init__(self, any_form):
        if any_form is None:
            raise Exception("Invalid address")

        if isinstance(any_form, StorageBagId):
            self.bytes = any_form.bytes
        elif isinstance(any_form, bytes):
            if len(any_form) != 32:
                raise Exception("Invalid bag id bytes length")
            self.bytes = any_form
        elif isinstance(any_form, str):
            if len(any_form) != 64:
                raise Exception("Invalid bag id hex length")
            self.bytes = hex_to_bytes(any_form)
        else:
            raise Exception("Unsupported type")

    def to_hex(self):
        hex_str = bytes_to_hex(self.bytes)
        while len(hex_str) < 64:
            hex_str = '0' + hex_str
        return hex_str