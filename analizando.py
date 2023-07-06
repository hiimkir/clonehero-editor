import os
import sys
import mmap
import json
import 
import struct


class record:
    instrumentNo = {
        0:"lead", 1: "bass", 2: "rythm", # 3
        4: "6lead", 5: "6bass", # 6 - 7
    }

    def __init__(self, bytestring: bytes):
        self.ID = bytestring[:16]
        self.playCount = bytestring[17]
        # the purpose of these bytes is still unknown
        self.byte1918 = struct.unpack('<H', bytestring[18::20])
        self.path = None
        

    def addScore(self, bytestring: bytes):
        self.instrument = bytestring[0]
        self.nullbyte = bytestring[1]
        self.difficulty = bytestring[2]
        self.percentage = bytestring[3]
        self.crown = bool(bytestring[4])
        self.speed = struct.unpack('<H', bytestring[5::7])
        self.rank = bytestring[7]
        self.mods = struct.unpack('<L', bytestring[8::12])
        self.points = struct.unpack('<L', bytestring[12::16])

    # this could be a classmethod
    def getPath(self):
        if self.path:
            return ""

        with open("songcache.bin", "rb") as fp:
            songcacheMap = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
            idAddress = songcacheMap.rfind(self.ID)
            if idAddress == -1:
                self.path = "*SONG NOT FOUND*"
                return

            # worst case i can trace back to nullbyte b4 prev id and do + 16
            # as of now it won't work on 2 char windows drives and unix systems
            self.path = ""
            pathAddress = songcacheMap.rfind(b":\\", 0, idAddress) - 1
            pathLength = songcacheMap[pathAddress]
            
            for i in range(pathLength):
                self.path[i] += chr(songcacheMap[pathAddress + i])

            songcacheMap.close()


scoredataFile = open("scoredata.bin", "rb")
outputFile = open("CH_scoredata_telemetry.log", "w")
outputFile.write(f"""\n HEADER: {scoredataFile.read(8).hex()} \n
 ID                              | Instrument | MOD | Nulls | Path
------------------------------------------------------------------------\n""")

count_t = 0
count_i = 0
while True:
    byte = scoredataFile.read(20)

    if byte == b"":
        break

    count_t += 1
    track = record(byte)
    for j in range(byte[16]):
        count_i += 1
        track.addScore(scoredataFile.read(16))

#         if ((len(sys.argv) > 1) and (sys.argv[1] == "-a")) or \
#             (track.scores[j]["mods"] not in [1, 8]) or \
#             (track.scores[j]["nulls"]) or (track.scores[j]["instrument"] > 4):
# 
#             track.getPath()
#             outputFile.write(f"{track.ID.hex()} {track.scores[j]['instrument']:>5} \
# {track.scores[j]['mods']:>12} {track.scores[j]['nulls']:>7}   {track.path}\n")

outputFile.write(f"\n TRACKS: {count_t} ({count_t:X}) \
    SCORES: {count_i} ({count_i:X})")

scoredataFile.close()
outputFile.close()

print("Results saved to CH_scoredata_telemetry.log")
