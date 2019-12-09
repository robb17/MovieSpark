from app import db
import sys

from app import create_app

if __name__ == '__main__':
	if len(sys.argv) > 2:
		print("usage: python3 run.py [init?]")
	serve = True

	if len(sys.argv) == 2 and sys.argv[1] == 'init':
		serve = False

	app = db.create_all(app=create_app())