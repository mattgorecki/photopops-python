import PIL
import Image
import sys
import math
import time

#if len(sys.argv) < 3:
#    sys.exit('usage: gs.py <input> <output>')

#input_filename = sys.argv[1]
#output_filename = sys.argv[2]

input_filename = "/opt/photopops/events/prototyping/orig/IMG_5270.JPG"
output_filename = "overlayed.png"

input_img = Image.open(input_filename)
output_img = Image.new("RGBA", input_img.size)
bg_img = Image.open("/opt/photopops/assets/backgrounds/moon.jpg")
bg_img = bg_img.resize((2336,3505))

print bg_img.mode

tola, tolb = 200, 100
for y in xrange(input_img.size[1]):
	for x in xrange(input_img.size[0]):
		p = list(input_img.getpixel((x, y)))
		d = int(math.sqrt(math.pow(p[0], 2) + math.pow((p[1] - 255), 2) + math.pow(p[2], 2)))
		if d > tola:d = 255
		elif (tolb < d):
			p[1] = p[1]-(255-d)
			d = (d-tolb)*(255/(tola-tolb))
		else: d = 0
		output_img.putpixel((x, y), (p[0], p[1], p[2], d))

bg_img.paste(output_img, (0,0), output_img)
bg_img.save(output_filename, "PNG")

print output_img.mode
#output_img.save(output_filename, "PNG")
