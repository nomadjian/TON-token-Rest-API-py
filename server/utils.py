import requests
import json

class HttpProvider():
    SHARD_ID_ALL = '-9223372036854775808'
 
    def __init__(self, host: str, options: str = None) -> None:
        self.host = host
        self.options = options if options else {}

    def __send_impl(self, apiUrl: str, request_data):
        headers = {'Content-Type': 'application/json'}

        try:
            headers['X-API-Key'] = self.options['API_KEY']
        except KeyError:
            pass
        response = requests.get(headers=headers, url=apiUrl, data=json.dumps(request_data))

        return response.content

    def send(self, method: str, params):
        return self.__send_impl(apiUrl=self.host, request_data={
            {'id': 1,
             'jsonrpc': "2.0",
             'method': method,
             'params': params}})

    def getAddressInfo(self, address: str):
        return self.send('getAddressInformation', {'address': address})

    def getExtendedAddressInfo(self, address):
        return self.send('getExtendedAddressInformation', {'address': address})

    def getWalletInfo(self, address: str):
        return self.send('getWalletInformation', {'address': address})

    def getTransactions(self, address, limit=20, lt=None, hash=None, to_lt=None, archival=None):
        return self.send("getTransactions", {address, limit, lt, hash, to_lt, archival})

    def getBalance(self, address):
        return self.send('getAddressBalance', {address: address})

    def sendBoc(self, base64):
        return self.send("sendBoc", {'boc': base64})
    
    def sendQuery(self, query):
        return self.send("sendQuerySimple", query)


    # /**
    #  * @param query     object as described https://toncenter.com/api/test/v2/#estimateFee
    #  * @return fees object
    #  */
    def getEstimateFee(self, query):
        return self.send("estimateFee", query)

    # /**
    #  * Invoke get-method of smart contract
    #  * todo: think about throw error if result.exit_code !== 0 (the change breaks backward compatibility)
    #  * @param address   {string}    contract address
    #  * @param method   {string | number}        method name or method id
    #  * @param params?   Array of stack elements: [['num',3], ['cell', cell_object], ['slice', slice_object]]
    #  */
    def call(self, address, method, params = []):
        return self.send('runGetMethod', {
            'address': address,
            'method': method,
            'stack': params,
        })

    # /**
    #  * Invoke get-method of smart contract
    #  * @param address   {string}    contract address
    #  * @param method   {string | number}        method name or method id
    #  * @param params?   Array of stack elements: [['num',3], ['cell', cell_object], ['slice', slice_object]]
    #  */
    def call2(self, address, method, params=[]):
        result = self.send('runGetMethod', {
            'address': address,
            'method': method,
            'stack': params
        })
        return result
        # return HttpProviderUtils.parseResponse(result);

    # /**
    #  * Returns network config param
    #  * @param configParamId {number}
    #  * @return {Cell}
    #  */
    def getConfigParam(self, config_param_id):
        raw_result = self.send('getConfigParam', {
            'config_id': config_param_id
        })
        return raw_result
        # if (rawResult['@type'] !== 'configInfo') throw new Error('getConfigParam expected type configInfo');
        # if (!rawResult.config) throw new Error('getConfigParam expected config');
        # if (rawResult.config['@type'] !== 'tvm.cell') throw new Error('getConfigParam expected type tvm.cell');
        # if (!rawResult.config.bytes) throw new Error('getConfigParam expected bytes');
        # return Cell.oneFromBoc(base64ToBytes(rawResult.config.bytes));    

    # /**
    #  * Returns ID's of last and init block of masterchain
    #  */
    def getMasterchainInfo(self):
        return self.send('getMasterchainInfo', {})

    # /**
    #  * Returns ID's of shardchain blocks included in this masterchain block
    #  * @param masterchainBlockNumber {number}
    #  */
    def getBlockShards(self, masterchainBlockNumber):
        return self.send('shards', {
            'seqno': masterchainBlockNumber
        })

    # /**
    #  * Returns transactions hashes included in this block
    #  * @param workchain {number}
    #  * @param shardId   {string}
    #  * @param shardBlockNumber  {number}
    #  */
    def getBlockTransactions(self, workchain, shardId, shardBlockNumber):
        return self.send('getBlockTransactions', {
            "workchain": workchain,
            "shard": shardId,
            "seqno": shardBlockNumber
        })

    # /**
    #  * Returns transactions hashes included in this masterhcain block
    #  * @param masterchainBlockNumber  {number}
    #  */
    def getMasterchainBlockTransactions(self, masterchainBlockNumber):
        return self.getBlockTransactions(-1, self.SHARD_ID_ALL, masterchainBlockNumber)

    # /**
    #  * Returns block header and his previous blocks ID's
    #  * @param workchain {number}
    #  * @param shardId   {string}
    #  * @param shardBlockNumber  {number}
    #  */
    def getBlockHeader(self, workchain, shardId, shardBlockNumber):
        return self.send('getBlockHeader', {
            'workchain': workchain,
            'shard': shardId,
            'seqno': shardBlockNumber
        })

    # /**
    #  * Returns masterchain block header and his previous block ID
    #  * @param masterchainBlockNumber  {number}
    #  */
    def getMasterchainBlockHeader(self, masterchainBlockNumber):
        return self.getBlockHeader(-1, self.SHARD_ID_ALL, masterchainBlockNumber)

