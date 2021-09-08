
from flask import Flask

import os
from config import basedir



app = Flask(__name__)
app.config.from_object('config')

from app import views


