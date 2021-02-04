import json
from lbrc_flask.forms.dynamic import init_dynamic_forms
import pytest
from flask import Response, Flask, Blueprint, render_template_string, url_for, redirect
from flask.testing import FlaskClient
from flask_login import login_required
from faker import Faker
from bs4 import BeautifulSoup
from ..database import db
from ..config import BaseTestConfig
from ..json import DateTimeEncoder
from .. import init_lbrc_flask
from ..security import init_security, User, Role
from .faker import LbrcFlaskFakerProvider, LbrcDynaicFormFakerProvider


class CustomResponse(Response):
    def __init__(self, baseObject):
        self.__class__ = type(
            baseObject.__class__.__name__, (self.__class__, baseObject.__class__), {}
        )
        self.__dict__ = baseObject.__dict__
        self._soup = None

    def get_json(self):
        return json.loads(self.get_data().decode("utf8"))

    @property
    def soup(self):
        if not self._soup:
            self._soup = BeautifulSoup(self.data, "html.parser")

        return self._soup


class CustomClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        super(CustomClient, self).__init__(*args, **kwargs)

    def post_json(self, *args, **kwargs):

        kwargs["data"] = json.dumps(kwargs.get("data"), cls=DateTimeEncoder)
        kwargs["content_type"] = "application/json"

        return CustomResponse(super(CustomClient, self).post(*args, **kwargs))

    def get(self, *args, **kwargs):
        return CustomResponse(super(CustomClient, self).get(*args, **kwargs))

    def post(self, *args, **kwargs):
        return CustomResponse(super(CustomClient, self).post(*args, **kwargs))


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    app.config.from_object(BaseTestConfig)
    ui_blueprint = Blueprint("ui", __name__)


    @ui_blueprint.route('/')
    @login_required
    def index():
        return render_template_string('{% extends "lbrc_flask/page.html" %}')


    with app.app_context():
        init_lbrc_flask(app, title='Requests')
        init_security(app, user_class=User, role_class=Role)
        init_dynamic_forms(app)
        app.register_blueprint(ui_blueprint)


    @app.route('/get_with_login')
    @login_required
    def get_with_login():
        return render_template_string('{% extends "lbrc_flask/page.html" %}')

    @app.route('/get_without_login')
    def get_without_login():
        return render_template_string('{% extends "lbrc_flask/page.html" %}')

    @app.route('/post_with_login', methods=["POST"])
    @login_required
    def post_with_login():
        return render_template_string('{% extends "lbrc_flask/page.html" %}')

    @app.route('/post_without_login', methods=["POST"])
    def post_without_login():
        return redirect(url_for("ui.index"))

    return app


@pytest.fixture(scope="function")
def initialised_app(request, app):
    app_crsf = request.node.get_closest_marker("app_crsf")
    if app_crsf is not None:
        app.config['WTF_CSRF_ENABLED'] = app_crsf.args[0]

    app.test_client_class = CustomClient
    context = app.test_request_context()
    context.push()
    db.create_all()

    yield app

    context.pop()


@pytest.fixture(scope="function")
def client(initialised_app):
    client = initialised_app.test_client()
    client.get('/') # Allow initialisation on first request

    yield client


@pytest.fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(LbrcFlaskFakerProvider)
    result.add_provider(LbrcDynaicFormFakerProvider)

    yield result
