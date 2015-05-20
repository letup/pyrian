A space shooter type game similar to Tyrian. The game is written in python using pygame. The game currently requires:

  * python (2.5)
  * pygame

Building the media files locally requires:

  * povray
  * perl
  * GNU make

Currently the game just allows you to start a server, connect with a client and fly around.

### Installation ###

Right now it just runs from a local directory. The only installation necessary is to make sure you have (either by building or downloading) the media files. To build them enter the media/ directory and just:
```
make
```

This will take some time because it must render all the images. Alternately you can download the media pack and unpack it in the root of the source tree. With some versions of povray you may need to give it permission to write the appropriate directories.

### Usage ###

To start a server (from the src/ dir):
```
python game.py <host> <port> <username> <password>
```

To connect a client to the server run the same command. Every argument must match the corresponding field in the server line above except the username should be different. The password is used to gain you access to the server.