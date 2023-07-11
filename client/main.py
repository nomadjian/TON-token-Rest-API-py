"""Main File."""
from tonclient import TonClient

ton_client = TonClient('v4R2', 'http://127.0.0.1:5885/', 'https://toncenter.com/api/v2/jsonRPC', '__KEY__')
ton_client.create_wallet()
print(ton_client)