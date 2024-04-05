from flask import Blueprint

tinylib = Blueprint('tinylib', __name__)

from . import views


