import sys
import time
sys.path.append("/opt/photopops/lib")
from bottle import route, run, static_file, template, view, install, response

@route('/static/<filename:path>')
def send_static(filename):
	response.set_header('cache-control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
	response.set_header('pragma', 'no-cache')
	response.set_header('expires', time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime()))
	return static_file(filename, root='/opt/photopops/web')

@route('/tv')
def tv():
	values = dict()
	values["title"] = "TV Display - Photopops"
	values["name"] = "TV Screen Template"
	return template('tvscreen', values)

@route('/admin')
def admin(db):
	values = dict()
	values["title"] = "Administration - Photopops"
	values["name"] = "Admin Screen"

	return template('admin', values)

run(host='0.0.0.0', port=8080, debug=True)
