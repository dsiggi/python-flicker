from PIL import Image, ImageDraw
from math import ceil

"""
Aufbau FLICKER_BEGINN
Byte 1 = BCD-Kodiert (0) und Länge Startcode (4)
Byte 2 = Freie Maskengestaltung (8) und Zusatzdaten (5)
Byte 3 = Zusatzdaten (5) und Betrag (1)
Byte 4 - 5 = Zufallszahl
"""
FLICKER_BEGINN = ['0x04', '0x85', '0x51', '0x00', '0x03']
FLICKER_START = ["0x0F", "0xFF"]
FLICKER_ASCII = 0x1

class tools:
    def is_ascii(data: str):
        return len(data) == len(data.encode())
     
    def ascii2hex(value):
        return hex(ord(value))

    def append_hex(a, b):
        sizeof_b = 0

        # get size of b in bits
        while((b >> sizeof_b) > 0):
            sizeof_b += 1

        # every position in hex in represented by 4 bits
        sizeof_b_hex = ceil(sizeof_b/4) * 4

        val =  hex((a << sizeof_b_hex) | b)
        if len(val) == 3:
            if b == 0:
                val = val + "0"
            else:
                val = val[:2] + "0" + val[2:]

        return val    

    def Quersumme(zahl):
       result = 0
       while zahl:
           result += zahl % 10
           zahl = int(zahl / 10)
       return result

    def str2hexlist(data: str):
        """
        Diese Funktion wandelt einen String in eine Liste
        aus HEX-Werten
        """
        out = []
        for c in data:
            out.append(tools.ascii2hex(c))

        return out

    def data2hexlist(data: str):
        length = len(data)
        data_list = tools.str2hexlist(data)

        return length, data_list

    def check_bit(x, y):
        if (x & (1 << y)):
            return True
        else:
            return False

    def luhn(data: list):
        erg = 0
        """
        Die Luhn-Prüfsumme wird wie folg berechnet
        1. Das linke Halbbyte wird einfach gezählt. Das rechte Halbbyte doppelt.
        2. Aus den Werten von 1. werden Quersummen gebildet und diese summiert.
        3. Die Prüfsumme ist 10 - (Summe aus 2. modulo 10)

        Beispiel
        Input:      87  2C
        1xl:        8   2
        QS 1xl:     8   2
        2xl:         14  24
        QS 2xl:      5   6
        ------------------
        Summe:      21 (8 + 2 + 5 + 6)
        10 - (Summe modulo 10): 9   
        """

        for x in data:
            first = str(x[2])
            first = int(first, 16)
            first = tools.Quersumme(first)

            second = str(x[3])
            second = int(second, 16)
            second *= 2
            second = tools.Quersumme(second)

            erg += first + second

        return ( 10 - ( erg % 10 )) % 10

    def xor(data: list):
        xor = 0

        for x in data:
            first = str(x[3])
            second = str(x[2])

            xor ^= int(first, 16)
            xor ^= int(second, 16)

        return xor

class InputError(Exception):
    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.value} -> {self.message}'

class create():
    def __init__(self, HIGH, BAR_SIZE, SPACE, SPACE_BEGIN_END, DURATION):
        """
        HIGH =  Höhe des GIFs. Die Breite ergibt sich dann aus BAR_SIZE, SPACE & SPACE_BEGIN_END
        BAR_SIZE = Breite der Datenblöcke in px
        SPACE = Breite der Leerstellen zwischen den Datenblöcken in px
        SPACE_BEGIN_END = Breite der Leerstellen am Anfang und Ende in px
        DURATION = Länge eines Bildes in ms
        """
        self.BAR_SIZE = BAR_SIZE
        self.SPACE = SPACE
        self.SPACE_BEGIN_END = SPACE_BEGIN_END
        self.DURATION = DURATION
        self.SIZE = (SPACE_BEGIN_END * 2 + BAR_SIZE * 5 + SPACE * 4, HIGH)
        self.IMAGES = []

        # Koordinaten des Taktsignals
        # [(x, y), (x, y)]
        self.takt_block = [(self.SPACE_BEGIN_END, 0), (self.SPACE_BEGIN_END + self.BAR_SIZE, self.SIZE[1])]
        # X-Position des ersten Datenblocks nach dem Takt
        begin = self.SPACE_BEGIN_END + self.BAR_SIZE + self.SPACE
        # Koordinaten des ersten Datenblocks
        # [(x, y), (x, y)]
        self.bar = [[( begin, 0), (begin + self.BAR_SIZE, self.SIZE[1])]]
        # Die Koordinaten aller weiteren Datenblöcke berechnen
        for x in range(1, 4):
            # Beginn des nächsten Datenblocks
            begin += self.BAR_SIZE + self.SPACE
            self.bar.append([( begin, 0), (begin + self.BAR_SIZE, self.SIZE[1])])

    def save_picture(self, data):
        for x in range(0, 2):
            # Base Image erzeugen
            base_img = Image.new('RGB', self.SIZE, color="black")
            d = ImageDraw.Draw(base_img)

            # Den Takt auf True setzen
            if x == 0:
                d.rectangle(self.takt_block, fill='white')

            # Alle nötigen Bits auf True setzen
            for x in range(0, 4):
                if tools.check_bit(data, x):
                    d.rectangle(self.bar[x], fill='white')

            self.IMAGES.append(base_img)

    def create_pictures(self, data: list):
        for x in data:        
            first = int(str(x[3]), 16)
            second = int(str(x[2]), 16)

            self.save_picture(first)
            self.save_picture(second)

    def create_raw(self, data1: str, data2: str):
        """
        Diese Funktion erstellt die RAW-Daten für einen Flicker-Code
        data1: String für Daten 1 (max. 12 Zeichen, nur ASCII Zeichen)
        data2: String für Daten 1 (max. 12 Zeichen, nur ASCII Zeichen)
        """

        # Überprüfe
        if not tools.is_ascii(data1):
            raise InputError(data1, "Daten enthalten nicht ASCII-Charakter!")
        if not tools.is_ascii(data2):
            raise InputError(data2, "Daten enthalten nicht ASCII-Charakter!") 
        if len(data1) > 12: 
            raise InputError(data1, "Daten zu lang!")
        if len(data2) > 12:
            raise InputError(data2, "Daten zu lang!")

        data1_len, data1_hex = tools.data2hexlist(data1)
        data2_len, data2_hex = tools.data2hexlist(data2)
        
        # Luhn-Prüfsumme berechnen
        # Die Luhn-Prüfsumme wird über folgende Daten berechnet
        # FLICKER_BEGINN, data1_hex & data2_hex
        # Von FLICKER_BEGINN muss aber das erste Byte entfernt werden
        luhn = tools.luhn(FLICKER_BEGINN[1:] + data1_hex + data2_hex)

        # Nun wird der erste Teil des Flicker-Codes zusammen gebaut
        FLICKER_CODE = FLICKER_BEGINN
        FLICKER_CODE.append(tools.append_hex(FLICKER_ASCII, data1_len))
        FLICKER_CODE += data1_hex
        FLICKER_CODE.append(tools.append_hex(FLICKER_ASCII, data2_len))
        FLICKER_CODE += data2_hex     

        # Nun muss an den Anfang noch die aktuelle Länge 
        # plus die Länge des nachfolgenden Prüfcodes (dieser ist 1)
        # des Flicker-Codes gesetzt werden
        FLICKER_CODE.insert(0, hex(len(FLICKER_CODE) + 1))
        # XOR-Prüfsumme berechnen
        # Die XOR-Prüfsumme wirde nun über den kompletten Flicker-Code
        # (ohne Prüfsumme) berechnet
        xor = tools.xor(FLICKER_CODE)

        # Prüfsumme zusammensetzen und an den Flicker-Code anhängen
        FLICKER_CODE.append(tools.append_hex(luhn, xor))

        # Jetzt noch die Startsequenz hinzufügen
        FLICKER_CODE = FLICKER_START + FLICKER_CODE
        
        return FLICKER_CODE

    def create_gif(self, data: list, filename: str):
        self.create_pictures(data)

        self.IMAGES[0].save(filename, save_all=True, append_images=self.IMAGES[1:], optimize=False, duration=self.DURATION, loop=0, )

    def create(self, data1: str, data2: str, filename: str = "flicker.gif"):
        self.create_gif(self.create_raw(data1, data2), filename)