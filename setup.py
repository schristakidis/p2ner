# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages
    
import p2ner

setup(name='p2ner',
      version = p2ner.__version__,
      description = 'P2P NEtworking Revisited',
      author= p2ner.__author__,
      author_email = 'loox@ece.upatras.gr',
      url = 'http://upg.iamnothere.org:8181/',
      packages = find_packages()
)
