from flask import Flask
from flask.views import MethodView
import marshmallow as ma
from flask_rest_api import Api, Blueprint, abort

app = Flask('My API')
app.config['OPENAPI_VERSION'] = '3.0.2'
api = Api(app)