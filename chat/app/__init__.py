from flask import Flask
from flask.ext.socketio import SocketIO

from flask import g

socketio = SocketIO()


#@app.teardown_appcontext
def close_connection(exception):
    backend = getattr(g, '_backend', None)
    if backend is not None:
        backend.close()


def create_app(debug=False, templates_dir='templates'):
    """Create an application."""
    app = Flask(__name__, template_folder=templates_dir)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    app.teardown_appcontext_funcs = [close_connection]

    socketio.init_app(app)
    return app

