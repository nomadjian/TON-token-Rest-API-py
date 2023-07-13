from BitString import BitString
from utils.utils import bytes_to_base64, compare_bytes, concat_bytes, crc32c, hex_to_bytes, read_n_bytes_uint_from_array, sha256, bytes_to_hex
from Slice import Slice

reachBocMagicPrefix = hexToBytes('B5EE9C72')
leanBocMagicPrefix = hexToBytes('68ff65f3')
leanBocMagicPrefixCRC = hexToBytes('acc3a728')

class Cell:
    def __init__(self):
        self.bits = BitString(1023)
        self.refs = []
        self.isExotic = False

    @staticmethod
    def fromBoc(self, serializedBoc):
        return self.deserializeBoc(serializedBoc)

    @staticmethod
    def oneFromBoc(self, serializedBoc):
        cells = self.deserializeBoc(serializedBoc)
        if len(cells) != 1:
            raise Exception('expected 1 root cell but have ' + str(len(cells)))
        return cells[0]

    def writeCell(self, anotherCell):
        self.bits.writeBitString(anotherCell.bits)
        self.refs.extend(anotherCell.refs)

    def getMaxLevel(self):
        maxLevel = 0
        for i in self.refs:
            if i.getMaxLevel() > maxLevel:
                maxLevel = i.getMaxLevel()
        return maxLevel

    def isExplicitlyStoredHashes(self):
        return 0

    def getMaxDepth(self):
        maxDepth = 0
        if len(self.refs) > 0:
            for i in self.refs:
                if i.getMaxDepth() > maxDepth:
                    maxDepth = i.getMaxDepth()
            maxDepth = maxDepth + 1
        return maxDepth

    def getMaxDepthAsArray(self):
        maxDepth = self.getMaxDepth()
        d = bytes([0, 0])
        d[1] = maxDepth % 256
        d[0] = maxDepth // 256
        return d

    def getRefsDescriptor(self):
        d1 = bytes([0])
        d1[0] = self.refs.length + self.isExotic * 8 + self.getMaxLevel() * 32
        return d1

    def getBitsDescriptor(self):
        d2 = bytes([0])
        d2[0] = (self.bits.cursor // 8) + (self.bits.cursor // 8)
        return d2
    
    def getDataWithDescriptors(self):
        d1 = self.getRefsDescriptor()
        d2 = self.getBitsDescriptor()
        tuBits = self.bits.getTopUppedArray()
        return concat_bytes(concat_bytes(d1, d2), tuBits)


    async def getRepr(self):
        reprArray = []

        reprArray.append(self.getDataWithDescriptors())
        for i in self.refs:
            reprArray.append(i.getMaxDepthAsArray())
        for i in self.refs:
            reprArray.append(await i.hash())
        x = bytes()
        for i in reprArray:
            x = concat_bytes(x, i)
        return x


    async def hash(self):
        return bytes(await sha256(await self.getRepr()))

    def beginParse(self):
        refs = [ref.beginParse() for ref in self.refs]
        return Slice(self.bits.array[:], self.bits.length, refs)

    def print(self, indent=''):
        s = indent + 'x{' + self.bits.toHex() + '}\n'
        for i in self.refs:
            s += i.print(indent + ' ')
        return s

    async def toBoc(self, has_idx=True, hash_crc32=True, has_cache_bits=False, flags=0):
        root_cell = self

        allcells = await root_cell.treeWalk()
        topologicalOrder = allcells[0]
        cellsIndex = allcells[1]

        cells_num = len(topologicalOrder)
        s = len(bin(cells_num)[2:])  # Minimal number of bits to represent reference (unused?)
        s_bytes = min((s + 7) // 8, 1)
        full_size = 0
        sizeIndex = []
        for cell_info in topologicalOrder:
            sizeIndex.append(full_size)
            full_size += await cell_info[1].bocSerializationSize(cellsIndex, s_bytes)
        offset_bits = len(bin(full_size)[2:])  # Minimal number of bits to offset/len (unused?)
        offset_bytes = max((offset_bits + 7) // 8, 1)

        serialization = BitString((1023 + 32 * 4 + 32 * 3) * len(topologicalOrder))
        serialization.writeBytes(reachBocMagicPrefix)
        serialization.writeBitArray([has_idx, hash_crc32, has_cache_bits])
        serialization.writeUint(flags, 2)
        serialization.writeUint(s_bytes, 3)
        serialization.writeUint8(offset_bytes)
        serialization.writeUint(cells_num, s_bytes * 8)
        serialization.writeUint(1, s_bytes * 8)  # One root for now
        serialization.writeUint(0, s_bytes * 8)  # Complete BOCs only
        serialization.writeUint(full_size, offset_bytes * 8)
        serialization.writeUint(0, s_bytes * 8)  # Root should have index 0
        if has_idx:
            for index, cell_data in enumerate(topologicalOrder):
                serialization.writeUint(sizeIndex[index], offset_bytes * 8)
        for cell_info in topologicalOrder:
            refcell_ser = await cell_info[1].serializeForBoc(cellsIndex, s_bytes)
            serialization.writeBytes(refcell_ser)
        ser_arr = serialization.getTopUppedArray()
        if hash_crc32:
            ser_arr = concat_bytes(ser_arr, crc32c(ser_arr))

        return ser_arr


    async def serializeForBoc(self, cellsIndex, refSize):
        reprArray = []

        reprArray.append(self.getDataWithDescriptors())
        if self.isExplicitlyStoredHashes():
            raise NotImplementedError("Cell hashes explicit storing is not implemented")
        for i in self.refs:
            refHash = await i.hash()
            refIndexInt = cellsIndex[refHash]
            refIndexHex = hex(refIndexInt)[2:]
            if len(refIndexHex) % 2:
                refIndexHex = "0" + refIndexHex
            reference = hex_to_bytes(refIndexHex)
            reprArray.append(reference)
        x = bytes()
        for i in reprArray:
            x = concat_bytes(x, i)
        return x


    async def bocSerializationSize(self, cellsIndex, refSize):
        return len(await self.serializeForBoc(cellsIndex, refSize))


    async def treeWalk(self):
        return self.treeWalk(self, [], {})

    async def moveToTheEnd(self, indexHashmap, topologicalOrderArray, target):
        targetIndex = indexHashmap[target]
        for h in indexHashmap:
            if indexHashmap[h] > targetIndex:
                indexHashmap[h] -= 1
        indexHashmap[target] = len(topologicalOrderArray) - 1
        data = topologicalOrderArray.pop(targetIndex)
        topologicalOrderArray.append(data)
        for subCell in data[1].refs:
            await self.moveToTheEnd(indexHashmap, topologicalOrderArray, await subCell.hash())


    async def treeWalk(self, cell, topologicalOrderArray, indexHashmap, parentHash=None):
        cellHash = await cell.hash()
        if cellHash in indexHashmap:  # Duplication cell
            if parentHash:
                if indexHashmap[parentHash] > indexHashmap[cellHash]:
                    await self.moveToTheEnd(indexHashmap, topologicalOrderArray, cellHash)
            return topologicalOrderArray, indexHashmap
        indexHashmap[cellHash] = len(topologicalOrderArray)
        topologicalOrderArray.append([cellHash, cell])
        for subCell in cell.refs:
            res = await self.treeWalk(subCell, topologicalOrderArray, indexHashmap, cellHash)
            topologicalOrderArray, indexHashmap = res[0], res[1]

        return topologicalOrderArray, indexHashmap
    
    def parseBocHeader(self, serializedBoc):
        if len(serializedBoc) < 4 + 1:
            raise Exception("Not enough bytes for magic prefix")
        inputData = serializedBoc
        prefix = serializedBoc[:4]
        serializedBoc = serializedBoc[4:]
        has_idx, hash_crc32, has_cache_bits, flags, size_bytes = None, None, None, None, None

        if prefix == reachBocMagicPrefix:
            flags_byte = serializedBoc[0]
            has_idx = bool(flags_byte & 128)
            hash_crc32 = bool(flags_byte & 64)
            has_cache_bits = bool(flags_byte & 32)
            flags = (flags_byte & 16) * 2 + (flags_byte & 8)
            size_bytes = flags_byte % 8

        if prefix == leanBocMagicPrefix:
            has_idx = True
            hash_crc32 = False
            has_cache_bits = False
            flags = 0
            size_bytes = serializedBoc[0]

        if prefix == leanBocMagicPrefixCRC:
            has_idx = True
            hash_crc32 = True
            has_cache_bits = False
            flags = 0
            size_bytes = serializedBoc[0]

        serializedBoc = serializedBoc[1:]

        if len(serializedBoc) < 1 + 5 * size_bytes:
            raise Exception("Not enough bytes for encoding cells counters")

        offset_bytes = serializedBoc[0]
        serializedBoc = serializedBoc[1:]

        cells_num = (size_bytes, serializedBoc)
        serializedBoc = serializedBoc[size_bytes:]

        roots_num = read_n_bytes_uint_from_array(size_bytes, serializedBoc)
        serializedBoc = serializedBoc[size_bytes:]

        absent_num = read_n_bytes_uint_from_array(size_bytes, serializedBoc)
        serializedBoc = serializedBoc[size_bytes:]

        tot_cells_size = read_n_bytes_uint_from_array(offset_bytes, serializedBoc)
        serializedBoc = serializedBoc[offset_bytes:]

        if len(serializedBoc) < roots_num * size_bytes:
            raise Exception("Not enough bytes for encoding root cells hashes")

        root_list = []
        for _ in range(roots_num):
            root_list.append(read_n_bytes_uint_from_array(size_bytes, serializedBoc))
            serializedBoc = serializedBoc[size_bytes:]

        index = False
        if has_idx:
            index = []
            if len(serializedBoc) < offset_bytes * cells_num:
                raise Exception("Not enough bytes for index encoding")

            for _ in range(cells_num):
                index.append(read_n_bytes_uint_from_array(offset_bytes, serializedBoc))
                serializedBoc = serializedBoc[offset_bytes:]

        if len(serializedBoc) < tot_cells_size:
            raise Exception("Not enough bytes for cells data")

        cells_data = serializedBoc[:tot_cells_size]
        serializedBoc = serializedBoc[tot_cells_size:]

        if hash_crc32:
            if len(serializedBoc) < 4:
                raise Exception("Not enough bytes for crc32c hashsum")
            length = len(inputData)
            if crc32c(inputData[:length - 4]) != serializedBoc[:4]:
                raise Exception("Crc32c hashsum mismatch")
            serializedBoc = serializedBoc[4:]

        if len(serializedBoc) > 0:
            raise Exception("Too much bytes in BoC serialization")

        return {
            "has_idx": has_idx,
            "hash_crc32": hash_crc32,
            "has_cache_bits": has_cache_bits,
            "flags": flags,
            "size_bytes": size_bytes,
            "off_bytes": offset_bytes,
            "cells_num": cells_num,
            "roots_num": roots_num,
            "absent_num": absent_num,
            "tot_cells_size": tot_cells_size,
             "root_list": root_list,
            "index": index,
            "cells_data": cells_data
        }
    def deserializeCellData(cellData, referenceIndexSize):
        if len(cellData) < 2:
            raise Exception("Not enough bytes to encode cell descriptors")

        d1 = cellData[0]
        d2 = cellData[1]
        cellData = cellData[2:]

        level = d1 // 32
        isExotic = bool(d1 & 8)
        refNum = d1 % 8
        dataBytesize = math.ceil(d2 / 2)
        fullfilledBytes = not bool(d2 % 2)

        cell = Cell()
        cell.isExotic = isExotic

        if len(cellData) < dataBytesize + referenceIndexSize * refNum:
            raise Exception("Not enough bytes to encode cell data")

        cell.bits.setTopUppedArray(cellData[:dataBytesize], fullfilledBytes)
        cellData = cellData[dataBytesize:]

        for _ in range(refNum):
            cell.refs.append(read_n_bytes_uint_from_array(referenceIndexSize, cellData))
            cellData = cellData[referenceIndexSize:]

        return {"cell": cell, "residue": cellData}


    def deserializeBoc(self, serializedBoc):
        if isinstance(serializedBoc, str):
            serializedBoc = hex_to_bytes(serializedBoc)

        header = self.parseBocHeader(serializedBoc)
        cells_data = header["cells_data"]
        cells_array = []

        for ci in range(header["cells_num"]):
            dd = self.deserializeCellData(cells_data, header["size_bytes"])
            cells_data = dd["residue"]
            cells_array.append(dd["cell"])

        for ci in range(header["cells_num"] - 1, -1, -1):
            c = cells_array[ci]
            for ri in range(len(c.refs)):
                r = c.refs[ri]
                if r < ci:
                    raise Exception("Topological order is broken")
                c.refs[ri] = cells_array[r]

        root_cells = []
        for ri in header["root_list"]:
            root_cells.append(cells_array[ri])

        return root_cells