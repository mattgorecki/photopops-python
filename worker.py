'''
worker-printing.py
RabbitMQ worker process

'''

from pp_helpers import loadconfig,saveconfig
from lib.pyQR import *
from etc import settings
from lib import facebook
import pp_rabbitmq
import json
import time
import Image
import ImageEnhance
import os
import subprocess
import sys

def print_photo(fn):
	# Print photo
	print "printing photo %s" % fn
	p = subprocess.Popen(['/usr/bin/lpr', fn], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def greenscreen(cfg, fn, background='random'):
	# Greenscreen removal
	EV_PROC_DIR = "/opt/photopops/events/%s/proc" % cfg['shortname']
	EV_ORIG_DIR = "/opt/photopops/events/%s/orig" % cfg['shortname']

	fullpath = "%s/%s" % (EV_ORIG_DIR, fn)

	orig = Image(fullpath)
	back = Image("/opt/photopops/assets/backgrounds/moon.jpg")
	back = back.scale(2336,3505)

	matte = orig.hueDistance(color=[0,220,0], minvalue = 40).binarize()
	matte.show()
	result = (orig-matte)+(back-matte.invert())
	result.save("%s/%s" % (EV_PROC_DIR, fn))

def build_1_up(cfg,photo_list):
	print "Building final photo"
	print photo_list
	im = Image.new("RGB", (1200, 1800), "white")

	# TODO: Make sure the file exists
	fileexists = False
	while fileexists == False:
		if os.path.isfile("/opt/photopops/events/%s/proc/%s" % (cfg['shortname'],photo_list[0])):
			fileexists = True
		else:
			print "file doesn't exist yet"
			time.sleep(1)

	thumb = Image.open("/opt/photopops/events/%s/proc/%s" % (cfg['shortname'],photo_list[0]))
	thumb = thumb.resize((1034,1551))

	im.paste(thumb, (83,27))

	qr = QRCode(4, QRErrorCorrectLevel.L)
	#TODO: Generate album URL for QR Code if it doesn't exist
	print cfg['photopops_fb_album_url']
	qr.addData("%s" % cfg['photopops_fb_album_url'])
	qr.make()
	qr_im = qr.makeImage()
	qr_im = qr_im.resize((175,175), Image.NEAREST)
	im.paste(qr_im, (83,1581))

	logo_im = Image.open("/opt/photopops/assets/helena-bridal-fair-2012.jpg")
	im.paste(logo_im, (270,1581))

	fn = "/opt/photopops/events/%s/final/%s-%s.jpg" % (cfg['shortname'],cfg['shortname'],time.time())

	im.save(fn, "JPEG", quality=90)

	return fn

def fb_upload(cfg,fn):
	print "Uploading %s to facebook" % fn
	graph = facebook.GraphAPI(settings.FB_APP_TOKEN)

	if len(cfg['photopops_fb_album_id']) == 0:
		print "no album"
		fb_res = graph.put_object(settings.FB_PHOTOPOPS_PAGE_ID, "albums", name=cfg['title'], message=cfg['title'])
		cfg['photopops_fb_album_id'] = fb_res['id']
		album_id = fb_res['id']
	else:
		album_id = cfg['photopops_fb_album_id']

	saveconfig(cfg)

	photo = Image.open("/opt/photopops/events/%s/proc/%s" % (cfg['shortname'], fn))
	photo = photo.resize((800,1200))
	photo_fn = "fb-%s" % fn

	mark = Image.open("/opt/photopops/assets/logo-angled-240x102.png")
	if mark.mode != 'RGBA':
		print "Converting %s/%s" % (EV_ORIG_DIR, fn)
		mark = mark.convert('RGBA')

	# Set opacity on watermark 
	alpha = mark.split()[3]
	alpha = ImageEnhance.Brightness(alpha).enhance(0.7)
	mark.putalpha(alpha)

	# Create a new transparent layer the size of the original image
	layer = Image.new('RGBA', photo.size, (0,0,0,0))
	layer.paste(mark, (photo.size[0]-mark.size[0]-25,photo.size[1]-mark.size[1]-25))

	# Add watermark layer to original image and save in processed directory
	proc = Image.composite(layer, photo, layer)
	proc.save("/opt/photopops/events/%s/proc/%s" % (cfg['shortname'], photo_fn), 'JPEG', quality=70)

	fb_photo = open("/opt/photopops/events/%s/proc/%s" % (cfg['shortname'], photo_fn), "rb")
	fb_res = graph.put_photo(fb_photo,album_id,photo_fn)
	fb_photo.close()

	del album_id

def callback(ch, method, properties, body):
	print " [x] Received %r" % body
	m = json.loads(body)
	cfg = loadconfig()

	if m['action'] == "greenscreen":
		#greenscreen(cfg, m['filename'])
		print "process green screen"

	if m['action'] == "build_1_up":
		fn = build_1_up(cfg,m['files'])
		if cfg['send_to_printer'] == "True":
			print_photo(fn)

	if m['action'] == "fb_upload":
		fb_upload(cfg, m['filename'])
	
	ch.basic_ack(delivery_tag = method.delivery_tag)

print ' [*] Waiting for messages. To exit press CTRL+C'
pp_rabbitmq.channel.basic_qos(prefetch_count=1)
pp_rabbitmq.channel.basic_consume(callback, queue="photopopsqueue")
pp_rabbitmq.channel.start_consuming()
