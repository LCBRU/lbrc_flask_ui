#!/usr/bin/env python

from distutils.core import setup

setup(name='lbrc_flask',
      version='1.0',
      description='NIHR Leicester BRC Flask Components and Theme',
      author='Richard Bramley',
      author_email='rabramley@gmail.com',
      url='https://github.com/LCBRU/lbrc_flask/',
      packages=['lbrc_flask'],
      install_requires=[
            'Flask',
            'flask_mail',
            'flask_admin',
            'flask_sqlalchemy',
            'python-dotenv',
            'email_validator',
            'flask_security',
            'markdown',
      ],
     )