import beanstalkc
import facebook
import Image
import time
import json
from pyQR import *
import sys
import subprocess

#Connect to beanstalkd
beanstalk = beanstalkc.Connection(host='localhost', port=11300)
beanstalk.watch("pp")
beanstalk.use('pp')
beanstalk.ignore("default")

# Connect to database via web2py DAL
sys.path.append("/opt/web2py")
from gluon import DAL
db = DAL('sqlite://storage.sqlite', folder='/opt/web2py/applications/photopops/databases', auto_import=True)

# Facebook Token setup
FB_TOKEN='AAABs3ZCR0wIEBAJbl43Ebky3Y5iq0YPKGTpAEmk0yZBJTL4BfNLExBmSvZCEkYtavTlPKfZAYDZCP0GUC1ouLscGt999FRZBxILhBsOkemAgZDZD' # PhotoPops app token
FB_PAGE_ID='216861271706571' # PhotoPops Facebook Page
graph = facebook.GraphAPI(FB_TOKEN)

### JOB FUNCTIONS
def fb_upload(fn,event):
	print event
	if event.facebook_album_id == None:
		print "no album"
		fb_res = graph.put_object(FB_PAGE_ID, "albums", name=event.title, message=event.title)
		status = db(db.event.id==event.id).update(facebook_album_id=fb_res['id'])
		db.commit()
		print status
		album_id = fb_res['id']
	else:
		album_id = event.facebook_album_id
	
	print album_id
	fb_photo = open(fn, "rb")
	fb_res = graph.put_photo(fb_photo,album_id,fn)
	fb_photo.close()

	del album_id

def build_1_up(photo_list,event):
	im = Image.new("RGB", (1200, 1800), "white")

	thumb = Image.open("/opt/photopops/%s/original/%s" % (event.shortname,photo_list[0]))
	thumb = thumb.resize((1034,1551))

	im.paste(thumb, (83,27))

	qr = QRCode(5, QRErrorCorrectLevel.Q)
	#TODO: Generate album URL for QR Code if it doesn't exist
	print event.facebook_album_url
	qr.addData("%s" % event.facebook_album_url)
	qr.make()
	qr_im = qr.makeImage()
	qr_im = qr_im.resize((175,175), Image.NEAREST)
	im.paste(qr_im, (83,1581))

	logo_im = Image.open("/opt/photopops/assets/fall-art-walk-2011.jpg")
	im.paste(logo_im, (270,1581))

	fn = "/opt/photopops/%s/processed/%s-%s.jpg" % (event.shortname,event.shortname,time.time())

	im.save(fn, "JPEG", quality=90)

	return fn
	

def build_4_up(photo_list,event):
	# Left, Down
	photo_coord = [(83,27), (83,804), (617, 27), (617,804)]

	im = Image.new("RGB", (1200, 1800), "white")

	for fn,coord in zip(photo_list, photo_coord):
		thumb = Image.open("/opt/photopops/%s/original/%s" % (event.shortname,fn))
		thumb = thumb.resize((500,750))

		im.paste(thumb, coord)

	qr = QRCode(10, QRErrorCorrectLevel.H)
	#TODO: Generate album URL for QR Code if it doesn't exist
	print event.facebook_album_url
	qr.addData("%s" % event.facebook_album_url)
	qr.make()
	qr_im = qr.makeImage()
	qr_im = qr_im.resize((175,175), Image.NEAREST)
	im.paste(qr_im, (83,1581))

	logo_im = Image.open("/opt/photopops/assets/fall-art-walk-2011.jpg")
	im.paste(logo_im, (270,1581))

	fn = "/opt/photopops/%s/processed/%s-%s.jpg" % (event.shortname,event.shortname,time.time())

	im.save(fn, "JPEG", quality=90)

	return fn

def print_photo(fn):
	# Print photo
	print "printing photo %s" % fn
	p = subprocess.Popen(['/usr/bin/lpr', fn], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print "Watching tubes: %s" % beanstalk.watching()
while True:
	job = beanstalk.reserve()

	tube = job.stats()['tube']
	body = json.loads(job.body)
	print body

	# Load event settings every iteration, so any changes will take effect.
	event = db(db.event).select(orderby=~db.event.id).first()

	if body['cmd'] == "fb_upload":
		# Upload photo to Facebook
		fb_upload(body['filename'],event)
	elif body['cmd'] == "print":
		# Print photo
		print body['files']

		if len(body['files']) == 4:
			fn = build_4_up(body['files'],event)
		elif len(body['files']) == 1:
			fn = build_1_up(body['files'],event)

		print_photo(fn)

		if event.upload_to_facebook:
			print "Uploading to Facebook...",
			beanstalk.put('{"cmd":"fb_upload","filename":"%s"}' % fn)

			print "done."

	job.delete()
