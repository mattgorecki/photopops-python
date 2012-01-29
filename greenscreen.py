#from SimpleCV import *
from SimpleCV import Image, ColorCurve
from etc import settings
import os, random, sys

fn = sys.argv[1]
shortname = sys.argv[2]
bg_fn = random.choice(os.listdir("/opt/photopops/assets/backgrounds"))

gs = Image("/opt/photopops/events/%s/orig/%s" % (shortname, fn))
gs_x, gs_y = gs.size()
#background = Image("/opt/photopops/assets/backgrounds/%s" % bg_fn)
background = Image("%s/%s" % (settings.BG_FOLDER, bg_fn))
background = background.scale(gs_x,gs_y)

matte = gs.toHLS()
cc = ColorCurve([[0,50],[40,40],[90,110],[255,150]])
cc2 = ColorCurve([[0,0],[80,40],[170,90],[255,240]])
matte = gs.toRGB()
matte = matte.hueDistance(color=[0,200,0], minvalue = 20, minsaturation=90)
matte = matte.applyIntensityCurve(cc2).binarize(thresh=30).bilateralFilter().morphOpen().smooth(aperature=(5,5))

result = (gs-matte)+(background-matte.invert())
result.save("/opt/photopops/events/%s/proc/%s" % (shortname, fn))
