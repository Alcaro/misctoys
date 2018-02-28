#!/usr/bin/env python3

import sys
from PIL import Image

if len(sys.argv) != 4:
	print("usage: ./imgdiff.py black_bg.png white_bg.png with_alpha.png")
	exit()

black = Image.open(sys.argv[1])
white = Image.open(sys.argv[2])
if black.size != white.size:
	print("images must have same size")
	exit()
out = Image.new('RGBA', black.size)

for y in range(black.size[1]):
	for x in range(black.size[0]):
		bp = black.getpixel((x,y))  # bp = tuple(r, g, b, maybe a)
		wp = white.getpixel((x,y))
		a = 255-(wp[0]-bp[0])
		a2 = a
		if a == 0: a2 = 999999 # force transparent pixels to black
		np = (bp[0]*255//a2, bp[1]*255//a2, bp[2]*255//a2, a)
		out.putpixel((x,y), np)
out.save(sys.argv[3])
