# Python-Flicker

Mit diesem Python modul lässt sich ein Flicker-Code erstellen.
Mit diesem Code wird of der TAN-Code für eine Onlineüberweisung übertragen.


## Beispiel
```python
from  flicker  import  flicker
    
# Initalisieren des Modules mit den nötigen Einstellungen
c = flicker.create(HIGH=100, BAR_SIZE=25, SPACE=10, SPACE_BEGIN_END=10, DURATION=50)
    
# Erzeugen eines Flicker-Codes
c.create("Python", "Flicker", filename="Flicker Test.gif")
```

## Erzeugtes GIF
![Test Flicker GIF](test_flicker.gif)

## TAN-Generator
![Test Flicker GIF](tan_picture1.jpg)
![Test Flicker GIF](tan_picture2.jpg)



