POVS = pov/ship.pov pov/shot.pov
OUTPUTS = images/ship images/shot

all: $(OUTPUTS)

images/ship: pov/ship.pov
	mkdir -p images/ship
	./pov/get-animations pov/ship.pov pov/scene.ini.template pov/scene.ini images/ship

images/shot: pov/shot.pov
	mkdir -p images/shot
	./pov/get-animations pov/shot.pov pov/scene.ini.template pov/scene.ini images/shot

clean:
	rm -rf $(OUTPUTS)