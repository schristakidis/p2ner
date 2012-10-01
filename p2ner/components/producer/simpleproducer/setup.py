# -*- coding: utf-8 -*-

from setuptools import setup

__component_name__ = "SimpleProducer"
__author__ = "Loris Corazza"
__author_email__ = "loox@ece.upatras.gr"
__version__ = "0.1"
__url__ = ""
__license__ = ""
__description__ = "P2ner simple producer scheduler component"
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

    packages=[__component_name__.lower(), __component_name__.lower() + ".messages"],
    package_data = __pkg_data__,

    entry_points="""
    [p2ner.components.producer]
    %s = %s:%s
    """ % ((__component_name__, __component_name__.lower(), __component_name__))
)
