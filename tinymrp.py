import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)   


COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import sys
import click
from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)