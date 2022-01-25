from PIL import Image
import os
from .create_flicker import tools

class InputError(Exception):
    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.value} -> {self.message}'

class GIFError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class CheckSumError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class decode:
    STARTCODE = {   "Kodierung": {
                        0: "BCD",
                        1: "ASCII"
                    },
                    "Daten": {
                        1: "Betrag",
                        2: "Kontonummer",
                        3: "Online-Banking-PIN",
                        4: "Telefonnummer",
                        5: "Bankdaten",
                        6: "Anzahl",
                        7: "Kontonummer",
                        8: "IBAN"
                    }
                }

    def __init__(self, file: str, check_luhn: bool=True, check_xor: bool=True):
        """
        Decodieren eines Flicker-Codes.
        file: GIF-Image zum dekodieren
        check_luhn: Luhn-Prüfsumme übeprüfen
        check_xor: XOR-Prüfsumme überprüfen
        """

        if ".gif" not in file:
            raise InputError(file, "Datei hat nicht die Endung .gif!")

        if not os.path.isfile(file):
            raise FileExistsError("Datei", file, "ist nicht vorhanden!")

        self.file = file
        self.BACKGROOUND = [0, 0, 0]
        self.BAR = [255, 255, 255]
        # GIF einlesen und in einer Liste speichern
        self.gif = self.read_GIF()
        # Position der Balken bestimmen
        self.bars = self.BarPositions()
        if self.bars == []:
            raise GIFError("Keinen Frame mit allen Balken gefunden. Das kann nicht sein.")
        # Beginn des Flickercodes finden
        self.start = self.search_Start()
        # Frames anhand des Beginns richtig sortieren
        self.gif = self.sort_gif()
        # Flickercode aufräumen, sprich wir entfernen alle Bilder ohne Taktsignal
        self.gif = self.clean_gif()
        # Wandeln des Codes in eine decodierte Liste
        self.flicker = []
        for x in range(len(self.gif)):
            self.flicker.append(self.read_frame(x))
        # XOR-Prüfsumme
        self.xor = self.Frame2Dec(self.flicker[len(self.flicker) - 2]) 
        # Luhn-Prüfsumme
        self.luhn = self.Frame2Dec(self.flicker[len(self.flicker) - 1])
        # Startcode
        self.startcode = {} 
        self.startcode["Kodierung"] = self.STARTCODE["Kodierung"][self.Frame2Dec(self.flicker[7])]
        self.startcode["Länge"] = self.Frame2Dec(self.flicker[6])
        self.startcode["Daten 1"] = [ self.STARTCODE["Daten"][self.Frame2Dec(self.flicker[9])], self.STARTCODE["Daten"][self.Frame2Dec(self.flicker[8])] ]
        self.startcode["Daten 2"] = [ self.STARTCODE["Daten"][self.Frame2Dec(self.flicker[11])], self.STARTCODE["Daten"][self.Frame2Dec(self.flicker[10])] ]
        self.startcode["Zufallszahl"] = self.Frame2Dec(self.flicker[12]) + self.Frame2Dec(self.flicker[13]) + self.Frame2Dec(self.flicker[14]) + self.Frame2Dec(self.flicker[15])
        # Länge der Datenself
        self.länge = int(str(self.Frame2Dec(self.flicker[5])) + str(self.Frame2Dec(self.flicker[4])), 16)
        # Daten 1
        self.daten1 = self.decode_daten(16)
        # Daten 2
        self.daten2 = self.decode_daten(16 + 2 + self.daten1["Länge"] * 2)

        #Prüfsummen
        if check_luhn:
            luhn = tools.luhn(self.check_luhn())
            if luhn != self.luhn:
                raise CheckSumError("Luhn-Prüfsumme ist falsch! Soll: {}, Ist: {}".format(self.luhn, luhn))
        if check_xor:
            xor = tools.xor(self.check_xor())
            if xor != self.xor:
                raise CheckSumError("XOR-Prüfsumme ist falsch! Soll: {}, Ist: {}".format(self.xor, xor))

    def read_GIF(self):
        img = Image.open(self.file)
        self.frames = img.n_frames
        mode = img.mode
        gif = []
        for frame in range(img.n_frames):
            img.seek(frame)
            gif.append(img.copy().convert(mode))

        img.close()
        return gif

    def BarPositions(self):
        bar = []
        bars = []
        search_color = self.BAR
        search_bar = True
        for frame in self.gif:
            for x in range(frame.width):
                index = frame.getpixel((x, 20))
                if frame.getpalette()[index * 3:index * 3 + 3] == search_color and search_bar:
                    bar.append(x)
                    search_color = self.BACKGROOUND
                    search_bar = False
                if frame.getpalette()[index * 3:index * 3 + 3] == search_color and not search_bar:
                    bar.append(x - 1)
                    search_color = self.BAR
                    search_bar = True

            if len(bar) == 10:
                # Es wurden 5 Balken gefunden also haben wir den passenden Frame
                break
            else:
                search_color = self.BAR
                search_bar = True
                bar = []

        ## Balkenpositionen in einer Liste zusammenstellen
        for pos in range(0, len(bar), 2):
            bars.append((bar[pos], bar[pos + 1]))

        return bars

    def read_frame(self, frame: int):
        val = []
        for x in self.bars:
            index = self.gif[frame].getpixel((int(x[0] + x[1])/2, 20))
            if self.gif[frame].getpalette()[index * 3:index * 3 + 3] == self.BAR:
                val.append(True)
            else:
                val.append(False)

        return val

    def search_Start(self):
        FLICKER_START = [[ True, True, True, True, True ],
                            [ False, True, True, True, True ],
                            [ True, False, False, False, False ],
                            [ False, False, False, False, False ],
                            [ True, True, True, True, True ],
                            [ False, True, True, True, True ],
                            [ True, True, True, True, True ],
                            [ False, True, True, True, True ]]

        found=False
        pos = 0
        index = 0
        for frame in range(len(self.gif)):
            if self.read_frame(frame) == FLICKER_START[index]:
                if index >= 7:
                    found = True
                    pos = frame - index
                    break
                index += 1
            else:
                index = 0

        if found:
            return pos
        else:
            raise GIFError("Der Beginn des Flickercodes wurde nicht gefunden!")

    def sort_gif(self):
        if self.start == 0:
            return self.gif
        else:
            gif = []
            gif = self.gif[self.start:]
            gif.extend(self.gif[:self.start])

            return gif

    def clean_gif(self):
        gif = []
        for frame in range(len(self.gif)):
            if self.read_frame(frame)[0] == True:
                gif.append(self.gif[frame])

        return gif

    def Frame2Dec(self, frame: list):
        op = 1
        val = 0
        for i in frame[1:]:
            if i:
                val += op
            op *= 2

        return val
        
    def Frame2Hex(self, frame: list):
        op = 1
        val = 0
        for i in frame[1:]:
            if i:
                val += op
            op *= 2

        return val
        
    def decode_daten(self, beginn: int):
        daten = {}
        daten["Kodierung"] = self.STARTCODE["Kodierung"][self.Frame2Dec(self.flicker[beginn + 1])]
        daten["Länge"] = self.Frame2Dec(self.flicker[beginn])
        daten["Daten"] = ""
        for x in range(beginn + 2, beginn + 2 + ( daten["Länge"] * 2), 2):
            val = tools.append_hex(self.Frame2Hex(self.flicker[x + 1]), \
                                        self.Frame2Hex(self.flicker[x]))
            if len(val) == 3:
                if self.Frame2Hex(self.flicker[x]) == 0:
                    val = val + "0"
                else:
                    val = val[:2] + "0" + val[2:]
            daten["Daten"] = daten["Daten"] + chr(int(val, 16))

        return daten

    def check_luhn(self):
        val = []
        beginn_beginn = 8
        beginn_ende = 15
        daten1_beginn = 18
        daten1_ende = daten1_beginn + + self.daten1["Länge"] * 2
        daten2_beginn = daten1_ende + 2
        daten2_ende = daten2_beginn + self.daten2["Länge"] * 2

        # Beginn
        for i in range(beginn_beginn, beginn_ende, 2):
            val1 = tools.append_hex(self.Frame2Hex(self.flicker[i + 1]),
                                self.Frame2Hex(self.flicker[i]))
            val.append(val1)

        # Daten1
        for i in range(daten1_beginn, daten1_ende, 2):
            val1 = tools.append_hex(self.Frame2Hex(self.flicker[i + 1]),
                                self.Frame2Hex(self.flicker[i]))
            val.append(val1)

        # Daten2
        for i in range(daten2_beginn, daten2_ende, 2):
            val1 = tools.append_hex(self.Frame2Hex(self.flicker[i + 1]),
                                self.Frame2Hex(self.flicker[i]))
            val.append(val1)

        return val  

    def check_xor(self):
        val = self.check_luhn()
                
        daten1 = 16
        daten2 = daten1 + self.daten1["Länge"] * 2 + 2

        # Länge Startcode
        val1 = tools.append_hex(self.Frame2Hex(self.flicker[7]),
                                self.Frame2Hex(self.flicker[6]))
        val.insert(0, val1)

        # Länge Daten
        val1 = tools.append_hex(self.Frame2Hex(self.flicker[5]),
                                self.Frame2Hex(self.flicker[4]))
        val.insert(0, val1)

        # Länge Daten 1
        val1 = tools.append_hex(self.Frame2Hex(self.flicker[daten1 + 1]),
                                self.Frame2Hex(self.flicker[daten1]))
        val.insert(2 + self.startcode["Länge"], val1)

        # Länge Daten 2
        val1 = tools.append_hex(self.Frame2Hex(self.flicker[daten2 + 1]),
                                self.Frame2Hex(self.flicker[daten2]))
        val.insert(2 + self.startcode["Länge"] + 1 + self.daten1["Länge"], val1)

        return val

    def get_data(self):
        """
        Gibt die gesammelten Daten als Liste zurück
        """
        return [ self.daten1["Daten"], self.daten2["Daten"] ]

    def get_info(self):
        """
        Gibt alle möglichen Infos als Dict zurück
        """

        val = {}
        val["Länge"] = self.länge
        val["Image"] = {    "Frames": self.frames,
                            "Bars": self.bars,
                            "Startframe": self.start
                        }
        val["Startcode"] = self.startcode
        val["Daten 1"] = self.daten1
        val["Daten 2"] = self.daten2
        val["Prüfsummen"] = {   "Luhn": self.luhn,
                                "XOR": self.xor }

        return val