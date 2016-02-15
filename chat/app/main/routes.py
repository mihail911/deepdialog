from flask import session, render_template, request
from flask import current_app as app
from . import main
from .utils import get_backend
import uuid
from .backend import Status

pairing_wait_ctr = 0
validation_wait_ctr = 0


def set_or_get_userid():
    if "sid" in session and session["sid"]:
        return userid()
    session["sid"] = request.cookies.get(app.session_cookie_name)
    if not session["sid"]:
        session["sid"] = str(uuid.uuid4().hex)
    return session["sid"]


def userid():
    return session["sid"]


@main.route('/', methods=['GET', 'POST'])
@main.route('/game', methods=['GET', 'POST'])
def main():
    """Chat room. The user's name and room must be stored in
    the session."""

    set_or_get_userid()
    # clear all chat session data
    # session["chat_session"] = None
    backend = get_backend()
    backend.create_user_if_necessary(userid())

    status = backend.get_updated_status(userid())
    session["mturk"] = True if request.args.get('mturk') else None
    if status == Status.Waiting:
        waiting_info = backend.get_waiting_info(userid())
        return render_template('waiting.html',
                               seconds_until_expiration=waiting_info.num_seconds,
                               waiting_message=waiting_info.message)
    elif status == Status.SingleTask:
        single_task_info = backend.get_single_task_info(userid())
        presentation_config = app.config["user_params"]["status_params"]["chat"]["presentation_config"]
        return render_template('single_task.html',
                               scenario=single_task_info.scenario,
                               agent=single_task_info.agent_info,
                               config=presentation_config,
                               num_seconds=single_task_info.num_seconds)
    elif status == Status.Finished:
        finished_info = backend.get_finished_info(userid(), from_mturk=session["mturk"])
        session["__clear__"] = True
        mturk_code = finished_info.mturk_code if session["mturk"] else None
        clear_session()
        return render_template('finished.html',
                               finished_message=finished_info.message,
                               mturk_code=mturk_code)
    elif status == Status.Chat:
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
    if "__clear__" in session and session["__clear__"]:
        session["room"] = -1
        session["mturk"] = None
        session["__clear__"] = False