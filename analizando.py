import sys
import mmap


class record:

    def __init__(self, bytestring: bytes):
        self.ID = bytestring[:16]
        self.playCount = bytestring[17]
        # the purpose of these bytes is still unknown
        self.byte1819LE = bytestring[19]*0x100 + bytestring[18]
        self.scores = []
        self.path = None

    def addScore(self, bytestring: bytes):
        instrument = bytestring[0]
        nulls = ""
        if (bytestring[1] + bytestring[6] + bytestring[10] + bytestring[11] +
            self.byte1819LE) != 0:

            nulls = f"{self.byte1819LE}{bytestring[1]}{bytestring[6]}\
{bytestring[10]}{bytestring[11]}"

        rank = bytestring[7]
        mods = bytestring[9]*0x100 + bytestring[8]

        self.scores.append({
            "instrument": instrument, "nulls": nulls, "rank": rank,
            "mods": mods
        })

    def getPath(self):
        if self.path:
            return

        with open("songcache.bin", "rb") as fp:
            songcacheMap = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
            idAddress = songcacheMap.rfind(self.ID)
            if idAddress == -1:
                self.path = "*SONG NOT FOUND*"
                return

            # this is unfathomably bad
            self.path = ""
            pathAddress = songcacheMap.rfind(b":\\", 0, idAddress) - 1
            while chr(songcacheMap[pathAddress]).isprintable() \
                    and (pathAddress < idAddress):

                self.path += chr(songcacheMap[pathAddress])
                pathAddress += 1

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

        if ((len(sys.argv) > 1) and (sys.argv[1] == "-a")) or \
            (track.scores[j]["mods"] not in [1, 8]) or \
            (track.scores[j]["nulls"]) or (track.scores[j]["instrument"] > 4):

            track.getPath()
            outputFile.write(f"{track.ID.hex()} {track.scores[j]['instrument']:>5} \
{track.scores[j]['mods']:>12} {track.scores[j]['nulls']:>7}   {track.path}\n")

outputFile.write(f"\n TRACKS: {count_t} ({count_t:X}) \
    SCORES: {count_i} ({count_i:X})")

scoredataFile.close()
outputFile.close()

print("Results saved to CH_scoredata_telemetry.log")
