import sys
sys.path.insert(0, "/var/www/deep-dialog/")
sys.path.insert(0, "/var/www/deep-dialog/chat")
sys.stdout = sys.stderr

from chat import app as application
