#! /usr/bin/env python

from os import listdir, chdir, uname, rename, unlink, umask
from os.path import join, dirname, isdir, abspath, exists
from distutils.core import setup
import sys

sys.path.append(join(dirname(__file__), join("src", "bonfire_cli")))

from version import VERSION

NAME = "bonfire-cli"
RELEASE=""

if __name__ == "__main__":
	chdir(abspath(dirname(__file__)))
	if isdir("build"):
		import shutil
		shutil.rmtree("build")

	is_rpm = is_sdist = is_wininst = is_zip = is_tgz = False
	scripts = map("bin/".__add__, listdir("bin"))
	package_dir = {'bonfire_cli': 'src/bonfire_cli'}
	packages=['bonfire_cli']

	for a in sys.argv:
		if a == "sdist":
			is_sdist = True
			break
		if "wininst" in a:
			is_wininst = True
		if "zip" in a:
			is_zip = True
		if "gztar" in a:
			is_tgz = True
		if "rpm" in a:
			is_rpm = True
		
	if is_sdist or is_wininst or is_zip:
		scripts += map("win/".__add__, listdir("win"))

		if is_wininst:
			package_dir.update({'bonfire': 'lib/bonfire', 'iso8601': 'lib/iso8601'})
			packages += ['bonfire', 'bonfire.broker', 'bonfire.broker.occi', 'iso8601']
			VERSION += RELEASE

	setup(name=NAME,
		version=VERSION,
		description='BonFIRE command line interface tools',
		author='Konrad Campowsky',
		author_email='konrad.campowsky@fokus.fraunhofer.de',
		url='http://portal.bonfire-project.eu',
		packages=packages,
		package_dir=package_dir,
		scripts = scripts,
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
