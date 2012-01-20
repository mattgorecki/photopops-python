import sys
sys.path.append("../lib")
from bottle import route, run, static_file, template, view, install

@route('/static/<filename:path>')
def send_static(filename):
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

run(host='localhost', port=8080, debug=True)
