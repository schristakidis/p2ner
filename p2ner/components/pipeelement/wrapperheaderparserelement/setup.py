# -*- coding: utf-8 -*-
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


from setuptools import setup

__component_name__ = "WrapperHeaderParserElement"
__author__ = "Loris Corazza"
__author_email__ = "loox@ece.upatras.gr"
__version__ = "0.1"
__url__ = "http://nam.ece.upatras.gr/p2ner/"
__license__ = """Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License."""
__description__ = "P2ner message header parser pipeline element"
__long_description__ = """"""
__pkg_data__ = {} #__component_name__.lower(): ["template/*", "data/*"]}

setup(
    name=__component_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,
    install_requires = ['p2ner>=0.4'],
    
    packages=[__component_name__.lower()],
    package_data = __pkg_data__,

    entry_points="""
    [p2ner.components.pipeelement]
    %s = %s:%s
    """ % ((__component_name__, __component_name__.lower(), __component_name__))
)
