from doctest import debug
from genericpath import exists
from sys import argv
import mmap
from struct import unpack
import configparser
from inspect import currentframe, getframeinfo


# WIP
# songcache: 20b header - [uc section # - ul count - [ul len - utf name]] - 
# - ul count - [
#    uc pathLen - utf path - 16b (prob links to sections) - uc fileLen - utf chartFile -
#    - 7 ul - 
#   ]
# (sections: title, author, album, genre, year, charter, playlist)

# class Song:
#     def __init__(self, bytestring: bytes):
#         self.title = ""
#         self.ID = None
#         self.path = ""
#         self.scores = Score(self.ID)


class Score:
    INSTRUMENT_NO = {
        0:"guitar", 1: "bass", 2: "rythm", # 3
        4: "guitarghl", 5: "bassghl", # 6 - 7
    }
    DIFFICULTY_NO = ["E", "M", "H", "X"]

    def raiseError(self, frame, err: str = "") -> None:
        if "-v" in argv:
            print(f"{self.ID.hex()} \033[93m line {getframeinfo(frame).lineno} \033[00m {err}")

    def __init__(self, bytestring: bytes):

        self.ID = bytestring[:16]
        self.playCount = bytestring[17]
        # the purpose of these bytes is still unknown
        self.byte1918 = unpack('<H', bytestring[18:20])[0]
        self.instrument = -1
        self.nullbyte = 0
        self.difficulty = -1
        self.percentage = -1
        self.crown = -1
        self.speed = -1
        self.rank = -1
        self.mods = -1
        self.points = -1

        self.path = None
        self.intensity = -1

    def addScore(self, bytestring: bytes) -> None:

        self.instrument = bytestring[0]
        self.nullbyte = bytestring[1]
        self.difficulty = bytestring[2]
        self.percentage = bytestring[3]
        self.crown = bool(bytestring[4])
        self.speed = unpack('<H', bytestring[5:7])[0]
        self.rank = bytestring[7]
        self.mods = unpack('<L', bytestring[8:12])[0]
        self.points = unpack('<L', bytestring[12:16])[0]

        self.intensity = -1

    # this could be a classmethod
    # add return value to use it in conditions
    def getPath(self) -> None:
        if self.path:
            self.raiseError(currentframe(), "Path already found")
            return

        with open("songcache.bin", "rb") as fp:
            songcacheMap = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
            idAddress = songcacheMap.rfind(self.ID)
            if idAddress == -1:
                self.raiseError(currentframe(), "No songcache.bin entry")
                return

            # worst case i can trace back to nullbyte b4 prev id and do + 16
            # as of now it won't work on 2 char windows drives and unix systems
            pathAddress = songcacheMap.rfind(b":\\", 0, idAddress) - 1
            pathLength = songcacheMap[pathAddress - 1]
            
            self.path = songcacheMap[pathAddress:(pathAddress+pathLength)].decode()

            songcacheMap.close()
            return self.path
    
    # .sng - https://github.com/mdsitton/SngFileFormat
    # actually, this should be accessible from songcache.bin
    def getIntensity(self) -> int | None:
        self.getPath()
        if not self.path:
            self.raiseError(currentframe(), "No path found")
            return
        if self.path[-4:] == ".sng":
            self.raiseError(currentframe(), ".sng support is not yet implemented")
            return 8
        if not exists(self.path + "/song.ini"):
            self.raiseError(currentframe(), "song.ini not found")
            return
        if self.instrument not in self.INSTRUMENT_NO.keys():
            self.raiseError(currentframe(), "instrument byte unknown value")
            return
        
        songProperties = configparser.ConfigParser()
        songProperties.read(self.path + "/song.ini")
        option = f"diff_{self.INSTRUMENT_NO[self.instrument]}"

        if option not in songProperties[songProperties.sections()[0]]:
            self.raiseError(currentframe(), "difficulty option not found")
            return 9
        
        self.intensity = int(songProperties[songProperties.sections()[0]][option])
        if self.intensity == -1:
            self.raiseError(currentframe(), "defined as undefined")
        return self.intensity
        

# you actually should color them based on aggregate max freq, not just line by line
def plotter(ordinates: list[list[int]]) -> None:
    STYLE_NO = ["\u001b[42m", "\u001b[43m", "\u001b[41m"]

    for y, abscissas in reversed(list(enumerate(ordinates))):
        line = f" {y} | "
        if len(abscissas) > 0:
            z_values = []
            for x in range(max(abscissas)+1):
                z_values.append(abscissas.count(x))
            if "-v" in argv:
                print(z_values)
            for z in z_values:
                style = STYLE_NO[z*(len(STYLE_NO)-1)//max(z_values)] if z > 0 else ""
                line += f"{style} \u001b[0m"
        print(line)
    print(f" * | 0 2 4 6")

scoredataFile = open("scoredata.bin", "rb")
scoredataFile.read(4)

# outputFile = open("CH_scoredata_telemetry.log", "w")
# outputFile.write(f"""\n HEADER: {scoredataFile.read(4).hex()} \n
#  ID                              | Instrument | MOD | Nulls | Path
# ------------------------------------------------------------------------\n""")
# if "-a" in argv or (track.mods not in [1, 8]) or (track.intensity == -1) or \
#     (track.instrument not in [0, 1, 4]) or track.byte1918 or track.nullbyte:
# outputFile.write(f"{track.ID.hex()} {track.instrument:>4} \
# {track.difficulty} {track.intensity:>2} *{track.rank} {track.mods:>5} \
# {track.byte1918:>4}-{track.nullbyte:<3}  {track.path}\n")
# outputFile.close()
# print("Results saved to CH_scoredata_telemetry.log")


# This whole idea is actually incorrect because hit%/rank is disconnected from diff/score
results = [[[], [], [], [], [], [], [], []], [[], [], [], [], [], [], [], []]]
for i in range(unpack('<L', scoredataFile.read(4))[0]):
    byte = scoredataFile.read(20)

    track = Score(byte)
    for j in range(byte[16]):
        track.addScore(scoredataFile.read(16))
        track.getIntensity()

        if (track.difficulty >= 2) and (track.intensity in range(8)):
            results[track.difficulty-2][track.intensity].append(track.rank)

scoredataFile.close()

print("\nHARD")
plotter(results[0])
print("\nXTREME")
plotter(results[1])

if "-v" in argv:
    print("\n", results)
