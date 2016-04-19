from flask import session, render_template, request, redirect, url_for
from flask import current_app as app
from . import main
from .utils import get_backend
import uuid
from .backend import Status
import logging

'''
Decides what template to render based on user's current status, etc. by interfacing with backend.
'''

pairing_wait_ctr = 0
validation_wait_ctr = 0

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler("chat.log")
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)


def set_or_get_userid():
    if "sid" in session and session["sid"]:
        return userid()
    session["sid"] = request.cookies.get(app.session_cookie_name)
    if not session["sid"]:
        session["sid"] = str(uuid.uuid4().hex)
    return session["sid"]


def userid():
    return session["sid"]


def generate_unique_key():
    """
    Generates a unique key for the user's current session. This is used to make sure that user's can't open multiple
    sessions of the website in the same browser (this causes strange socketIO behavior so we want to prevent it).
    :return:
    """
    return str(uuid.uuid4().hex)


@main.route('/index', methods=['GET', 'POST'])
@main.route('/', methods=['GET', 'POST'])
def index():
    """Chat room. The user's name and room must be stored in
    the session."""

    set_or_get_userid()

    # if there's no key in the URL, generate a key and add it to the URL
    if not request.args.get('key'):
        if request.args.get('mturk'):
            return redirect(url_for('main.index', key=generate_unique_key(), mturk=request.args.get('mturk')))
        else:
            return redirect(url_for('main.index', key=generate_unique_key()))

    backend = get_backend()
    backend.create_user_if_necessary(userid())

    key = request.args.get('key')
    # Check the key stored in the 'session' dict and compare it against the key in the URL. If they're not the same and
    # the user is still in a 'connected' state, then show an error message telling users they cannot open multiple tabs
    # of the website.
    # If the user is not connected, this means that they're starting a new session, so replace the key in the dict
    # with the new key.
    if 'key' in session and session['key'] != key:
        if backend.is_connected(userid()):
            return render_template('error.html')
        else:
            session['key'] = key
    elif 'key' not in session:
        # otherwise, simply add the key to the session dict
        session['key'] = key

    # get status for user
    status = backend.get_updated_status(userid())
    logger.info("Got updated status %s for user %s" % (Status._names[status], userid()[:6]))
    # check whether user is accessing the link from Turk or not
    session["mturk"] = True if request.args.get('mturk') and int(request.args.get('mturk')) == 1 else None
    if session["mturk"]:
        logger.debug("User %s is from Mechanical Turk" % userid()[:6])
    if status == Status.Waiting:
        # get waiting information (time left, message to display) from backend and show the waiting template
        logger.info("Getting waiting information for user %s" % userid()[:6])
        waiting_info = backend.get_waiting_info(userid())
        return render_template('waiting.html',
                               seconds_until_expiration=waiting_info.num_seconds,
                               waiting_message=waiting_info.message)
    elif status == Status.SingleTask:
        # get single task info (scenario, other configs) and render single task template
        logger.info("Getting single task information for user %s" % userid()[:6])
        single_task_info = backend.get_single_task_info(userid())
        presentation_config = app.config["user_params"]["status_params"]["chat"]["presentation_config"]
        return render_template('single_task.html',
                               scenario=single_task_info.scenario,
                               agent=single_task_info.agent_info,
                               config=presentation_config,
                               num_seconds=single_task_info.num_seconds)
    elif status == Status.Finished:
        # render finished template
        logger.info("Getting finished information for user %s" % userid()[:6])
        finished_info = backend.get_finished_info(userid(), from_mturk=session["mturk"])
        session["__clear__"] = True
        mturk_code = finished_info.mturk_code if session["mturk"] else None
        clear_session()
        return render_template('finished.html',
                               finished_message=finished_info.message,
                               mturk_code=mturk_code)
    elif status == Status.Chat:
        # render chat template after getting chat information (scenario, room number, etc.) from backend
        logger.info("Getting chat information for user %s" % userid()[:6])
        chat_info = backend.get_chat_info(userid())
        presentation_config = app.config["user_params"]["status_params"]["chat"]["presentation_config"]
        session["room"] = chat_info.room_id
        return render_template('chat.html',
                               room=chat_info.room_id,
                               scenario=chat_info.scenario,
                               agent=chat_info.agent_info,
                               num_seconds=chat_info.num_seconds,
                               config=presentation_config)


def clear_session():
    """
    Resets all user session info.
    :return:
    """
    if "__clear__" in session and session["__clear__"]:
        session["room"] = -1
        session["mturk"] = None
        session["__clear__"] = False
