from tonclient.client import TonClient
from tonclient.types import Abi, Signer
import tonos_ts4.pycontracts.ton_token_js_library.NoxTonTokenRootABI as NoxTonTokenRootABI
import tonos_ts4.pycontracts.ton_token_js_library.NoxTonTokenWalletABI as NoxTonTokenWalletABI


class TonClient:
    def __init__(self, provider, key, type, jettons):
        self.tonweb = TonClient(provider=provider, apiKey=key)
        self.jettons = {}
        self.type = type
        self.jettonsInfo = jettons

    async def getTransaction(self, address):
        return await self.tonweb.net.query_collection('transactions', {'account_addr': address}, ['id'], 20)

    async def getBalance(self, address):
        ret = {
            'balance': await self.getBalanceTON(address),
            'jettons': await self.getBalanceJettons(address)
        }
        return ret

    async def getBalanceTON(self, address):
        return (await self.tonweb.net.query_collection('accounts', {'id': {'eq': address}}, ['balance'])['balance']) / 1000000000

    async def getBalanceJettons(self, address, jettonName=False):
        await self.prepare(address)

        if jettonName:
            try:
                balance = (await self.tonweb.net.query_collection('accounts', {'id': {'eq': self.jettons[jettonName]['jettonWalletAddress']}}, ['balance'])['balance']) / 1000000000
            except:
                balance = 0
            return balance

        jettons = {}
        for name in self.jettons:
            try:
                balance = (await self.tonweb.net.query_collection('accounts', {'id': {'eq': self.jettons[name]['jettonWalletAddress']}}, ['balance'])['balance']) / 1000000000
            except:
                balance = 0
            jettons[name] = balance
        return jettons

    async def prepare(self, address):
        hot_wallet_address = tonos_ts4.ts4.Address(address)

        for name in self.jettonsInfo:
            info = self.jettonsInfo[name]
            ton_token_root_abi = Abi.from_dict(NoxTonTokenRootABI.get())
            ton_token_wallet_abi = Abi.from_dict(NoxTonTokenWalletABI.get())

            ton_token_root = self.tonweb.contracts.create_internal(ton_token_root_abi, info['address'])
            ton_token_wallet_address = await ton_token_root.call_getWalletAddress(hot_wallet_address)
            
            ton_token_wallet = self.tonweb.contracts.create_with_giver(ton_token_wallet_abi, ton_token_wallet_address, Signer.external(info['address']))
            self.jettons[name] = {
                'jettonWallet': ton_token_wallet,
                'jettonWalletAddress': ton_token_wallet_address
            }

    async def createWallet(self):
        wallet_client = self.wallet_client

        mnemonic = self.tonweb.crypto.generate_random_sign_keys().mnemonic_phrase
        wallet = wallet_client.generate_wallet(mnemonic)

        address = wallet.address
        jettons_address = await self.getAddressJettons(address)

        ret = {
            'address': str(address),
            'jettons': jettons_address,
            'mnemonic': mnemonic,
            'mnemonicStr': ' '.join(mnemonic.split(' ')),
            'publicKey': wallet_client.output_pub.private_key,
            'privateKey': wallet_client.output_secret.private_key
        }

        return ret

    async def getAddressJettons(self, address, jettonName=False):
        await self.prepare(address)

        if jettonName:
            return str(self.jettons[jettonName]['jettonWalletAddress'])

        jettons = {}
        for name in self.jettons:
            jettons[name] = str(self.jettons[name]['jettonWalletAddress'])
        return jettons

    async def createTransfer(self, mnemonics, toAddress, amount, payload=None, jetton=None):
        wallet_client = self.wallet_client

        arr_mnemonics = mnemonics.split(' ')
        if len(arr_mnemonics) != 24:
            raise Exception('Incorrect number of mnemonic phrases')
        key_pair = wallet_client.get_keypair_from_mnemonic(arr_mnemonics)

        wallet = wallet_client.create_wallet(self.type, key_pair)
        from_address = str(wallet.get_address())

        balance = await self.getBalanceJettons(from_address, jetton)
