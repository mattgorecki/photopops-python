import json
import etc.settings

def loadconfig():
	cfgfile = open(etc.settings.CFG_FILE)
	cfg = json.load(cfgfile)
	cfgfile.close()

	return cfg

def saveconfig(cfg):
	cfgfile = open(etc.settings.CFG_FILE, 'w')
	json.dump(cfg, cfgfile, indent=4)
	cfgfile.close()
