from SimpleCV import *
from SimpleCV.Display import Display, pg
import time

gs = Image("/opt/photopops/events/prototyping/orig/IMG_5269.JPG")
background = Image("/opt/photopops/assets/backgrounds/moon.jpg")
background = background.scale(2336,3505)

#matte = gs.hueDistance(color=[0,200,0], minvalue = 40).smooth(aperature=(17,17)).binarize()
matte = gs.hueDistance(color=[0,220,0], minvalue = 40).binarize()
result = (gs-matte)+(background-matte.invert())
result.save('result.jpg')
