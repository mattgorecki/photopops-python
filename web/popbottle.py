import sys
sys.path.append("../lib")
from bottle import route, run, static_file, template, view, install
from bottle_sqlite import SQLitePlugin

install(SQLitePlugin(dbfile='/opt/photopops/db/popdb.sqlite',dictrows=True))

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

	row = db.execute('SELECT id,title,shortname from event').fetchone()
	print row
	if row:
		values["row"] = row

	return template('admin', values)

run(host='localhost', port=8080, debug=True)
