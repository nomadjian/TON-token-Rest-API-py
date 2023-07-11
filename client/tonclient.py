from requests import request
from urllib.parse import urlencode
import json


class TonClient():
    """
        This class encapsulates logic with SDKServer's interactions

        __SDKServer -> IP-address and port for of the docker container ton-server
        __provider -> public https://toncenter.com/api/v2/jsonRPC
        __provider_key -> obtained API-key with telegrambot @tonapibot

        __types -> types of contracts for the wallet
        Explanation:
        'simpleR1': SimpleWalletContractR1,
        'simpleR2': SimpleWalletContractR2,
        'simpleR3': SimpleWalletContractR3,
        'v2R1': WalletV2ContractR1,
        'v2R2': WalletV2ContractR2,
        'v3R1': WalletV3ContractR1,
        'v3R2': WalletV3ContractR2,
        'v4R1': WalletV4ContractR1,
        'v4R2': WalletV4ContractR2


    """
    __types = ['simpleR1', 'simpleR2', 'simpleR3',
               'v2R1', 'v2R2', 'v3R1', 'v3R2', 'v4R1',
               'v4R2']
    __jettons = {
            'TGR': {
                'address': 'EQAvDfWFG0oYX19jwNDNBBL1rKNT9XfaGP9HyTb5nb2Eml6y'
            }
        }

    def __init__(self, type_: str, sdk_server, provider, provider_key):
        if type_ not in self.__types:
            raise Exception('Unknow contract type')
        self.__type = type_
        self.__SDKServer = sdk_server
        self.__provider = provider
        self.__providerKey = provider_key

    def create_wallet(self):
        return self.__send(method='createWallet')

    def get_balance(self, address: str):
        return self.__send(method='getBalance', data={'address': address})

    def get_transactions(self, address: str):
        return self.__send(method='getTransaction', data={'address': address})

    def send_transaction(self, mnemonics: str, to_address: str, amount: str, payload: str = None):
        return self.__send(method='getBalance',
                           data={
                               'mnemonics': mnemonics,
                               'to_address': to_address,
                               'amount': amount,
                               'payload': payload,
                               })

    def send_transaction_jetton(self, mnemonics: str, to_address: str, amount: str, jetton: str):
        if jetton in self.__jettons:
            return self.__send(method='getBalance',
                               data={'mnemonics': mnemonics,
                                     'to_address': to_address,
                                     'amount': amount,
                                     'jetton': jetton,
                                     })
        else:
            raise Exception

    def __send(self, method, data={}):
        query = urlencode({
            'provider': self.__provider,
            'providerKey': self.__providerKey,
            'type': self.__type,
            'jettons': self.__jettons
        })
        url = self.__SDKServer + method + '?' + query
        jsoned_response = json.loads(request(method='GET', url=url))
        return jsoned_response
