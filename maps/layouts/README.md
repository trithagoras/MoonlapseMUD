# What is this?
This is where you will put your map files for your Moonlapse server. This is **not** where you put any other files unless you want an unstable or broken game.

# What is the format?
The format is as follows:
1. Under `maps/layouts/`, create a new directory with the name of your map. This must be unique. E.g. `maps/layouts/forest/`.
2. Inside this new folder, create three files.
  * ground.data
  * solid.data
  * roof.data
  These files, respectively, represent terrain for the ground level, roof level, and things between which are collidable.

  These files must be formatted according to the Moonlapse map file specification.

# Moonlapse map file specification?
Yeah, it's a long story. Basically something that looks like this:
```
64$
63$}
24G6(34}
```
In this made up context, what this means is
```
A row of 64x "$" terrain tiles
A row of 63x "$" terrain tiles followed by a "}" terrain tile
A row of 24x "G" terrain tiles followed by 6x "(" terrain tiles followed by 34 "}" terrain tiles
```

Whatever "$", "}", "G", "{", etc. represents is up to you and defined in `maps/__init__.py`.

# How do I make one of these files?
You can draw a bitmap file and use the `maps/bmp2ml.py` script to spit out a properly formatted file. The script defines a colour palette for you, so your bitmaps need to have those exact colours loaded. I should probably add a colour palette bitmap in here so you can use your image manipulation software's colour picker to easier draw your maps.

In the future, I will probably add a proper map editor GUI with the names of the terrain materials but please bear with the project in its early stages.

# What is the point of all this?
Like I said, it's a long story, but in short, we needed to have a compact format for map files and there's no built-in solution for image compression in Python and we want to require as few external libraries as possible (Pillow, for instance, could have done a better job).
