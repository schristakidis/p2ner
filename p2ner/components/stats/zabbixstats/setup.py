# -*- coding: utf-8 -*
#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
__component_name__ = "ZabbixStats" 
__author__ = "Loris Corazza" 
__author_email__ = "loox@ece.upatras.gr" 
__version__ = "0.1" 
__url__ = "http://nam.ece.upatras.gr/p2ner" 
__license__ = """Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.""" 
__description__ = "P2ner statistics plugin for BonFIRE Aggregator" 
__long_description__ = """""" 
__pkg_data__ = {} 
__entry_point__ = "p2ner.components.stats" 
__requirements__ = ['p2ner>=0.4']
###
# DO NOT EDIT BELOW IF YOU DON'T KNOW WHAT YOU ARE DOING
###

if __name__ == "__main__":
    import sys, os
    if len(sys.argv)>1:
        if sys.argv[1] == "bootstrap": 
            print "Bootstapping component \"%s\".\nChecking if directory exists." % __component_name__
            if not os.path.exists(__component_name__.lower()):
                print "Creating directory and __init__.py" 
                os.makedirs(__component_name__.lower())
                f = open(__component_name__.lower()+"/__init__.py", "w")
                f.write("# -*- coding: utf-8 -*-\r\n# Properly define here the class '%s' for %s\r\n" % (__component_name__, __description__))
                f.close()
                print "Done." 
            else:
                print "Directory exists, nothing to do." 
            sys.exit(0)

    from setuptools import setup
    setup(
        name=__component_name__,
        version=__version__,
        description=__description__,
        author=__author__,
        author_email=__author_email__,
        url=__url__,
        license=__license__,
        long_description=__long_description__ if __long_description__ else __description__,
        install_requires = __requirements__, 

        packages=[__component_name__.lower(), __component_name__.lower()+".ZabbixSender"], 
        package_data = __pkg_data__,

        entry_points=""" 
        [%s]
        %s = %s:%s
        """ % ((__entry_point__, __component_name__, __component_name__.lower(), __component_name__))
    )

