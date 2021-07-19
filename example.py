from flicker import flicker

# Initalisieren des Modules mit den nötigen Einstellungen
c = flicker.create(HIGH=100, BAR_SIZE=25, SPACE=10, SPACE_BEGIN_END=10, DURATION=50)

# Erzeugen eines Flicker-Codes
c.create("Python", "Flicker", filename="test_flicker.gif")
