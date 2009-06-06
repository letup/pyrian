POV_SRC = ship.pov
ANIM_BASES = ship-light-0-angle-.png
ANIMS = $(foreach anim,$(ANIM_BASES),../../images/ship/$(anim))

IMAGE_FLAGS = +FN16 +UA +W320 +H240
ANIM_FLAGS = +KI0.0 +KF1.0 +KFI0 +KFF1 +KC
QUALITY_FLAGS = +Q9 +A +J +AM1
ALL_FLAGS = $(IMAGE_FLAGS) $(ANIM_FLAGS) $(QUALITY_FLAGS)

all: $(ANIMS)

$(ANIMS): %.png: $(POV_SRC)
	povray +I$(POV_SRC) +O../../images/ship/$@ $(ALL_FLAGS) >/dev/null 2>/dev/null

clean:
	rm ../../images/ship/*