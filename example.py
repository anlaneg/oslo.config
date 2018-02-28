
import sys
sys.path=['.'] + sys.path
print sys.path
import oslo_config.cfg as cfg

def init(args,**kwargs):
	cfg.CONF(args=args,project='udev',version='%%prog 1.1.2',**kwargs)
	print cfg.CONF.udev

if __name__ == "__main__":
	init(sys.argv[1:])
