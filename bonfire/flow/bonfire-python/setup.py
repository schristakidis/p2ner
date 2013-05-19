#! /usr/bin/env python

from os import listdir, uname, rename, unlink
from os.path import dirname, join, exists
from distutils.core import setup

import sys

sys.path.append(join(dirname(__file__), join("src", "bonfire")))

from version import VERSION

NAME = "bonfire-python"

if __name__ == "__main__":
	is_wininst = is_zip = is_rpm = is_tgz = False

	for a in sys.argv:
		if "rpm" in a:
			is_rpm = True
			NAME = "python26-bonfire"
		if "wininst" in a:
			is_wininst = True
		if "zip" in a:
			is_zip = True
		if "gztar" in a:
			is_tgz = True

	setup(name=NAME,
		version=VERSION,
		description='client library for various BonFIRE services',
		author='Konrad Campowsky',
		author_email='konrad.campowsky@fokus.fraunhofer.de',
		url='http://portal.bonfire-project.eu',
		py_modules=['six'],
		packages=['bonfire', 'bonfire.authz', 'bonfire.broker', 'bonfire.broker.occi',
				'bonfire.em', 'bonfire.userapi', 'bonfire.elen', 
				'bonfire.http'
		],
		package_dir={'bonfire': 'src/bonfire'},
	)

	uname = uname()
	if uname[0].lower() == "linux":
		if is_wininst:
			oldname = "%s-%s.%s-%s.exe" % (NAME, VERSION, uname[0].lower(), uname[4])
			newname = "%s-%s.win32.exe" % (NAME, VERSION)
			rename(join("dist", oldname), join("dist", newname))
		if is_zip:
			oldname = "%s-%s.%s-%s.zip" % (NAME, VERSION, uname[0].lower(), uname[4])
			newname = "%s-%s.zip" % (NAME, VERSION)
			rename(join("dist", oldname), join("dist", newname))
		if is_tgz:
			oldname = "%s-%s.%s-%s.tar.gz" % (NAME, VERSION, uname[0].lower(), uname[4])
			newname = "%s-%s.tar.gz" % (NAME, VERSION)
			rename(join("dist", oldname), join("dist", newname))
	if is_rpm:
		oldname = "%s-%s.tar.gz" % (NAME, VERSION)
		oldpath = join("dist", oldname)
		if exists(oldpath):
			unlink(oldpath)

