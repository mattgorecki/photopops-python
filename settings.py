'''
settings.py - Photopops settings
'''
sys.path.append("/opt/web2py")
from gluon import DAL
db = DAL('sqlite://storage.sqlite', folder='/opt/web2py/applications/photopops/databases', auto_import=True)

# Load configuration settings
EVENTNAME = event.shortname
TMPDIR = "/tmp/photopops"
EV_DIR = "/opt/photopops/%s" % EVENTNAME
EV_ORIG_DIR = "/opt/photopops/%s/original" % EVENTNAME
EV_PROC_DIR = "/opt/photopops/%s/processed" % EVENTNAME
USB_DIR = "/media/photopops"
WATERMARK = "/opt/photopops/assets/logo-angled-600x250.png"
