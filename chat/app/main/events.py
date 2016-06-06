from flask import session, request, g
from flask import current_app as app
from flask.ext.socketio import emit, join_room, leave_room
from .. import socketio
from datetime import datetime
from .utils import get_backend
from .backend import Status
from .routes import userid

import cPickle as pickle
import logging
import os
import random
import werkzeug


'''
Handles all events to and from client (browser). Interfaces with the backend (backend.py)
'''

date_fmt = '%m-%d-%Y:%H-%M-%S'
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler("/var/www/deepdialog/chat/chat.log")
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Make audio dir
curr_dir = os.path.dirname(os.getcwd())
audio_data_dir = "/var/www/deepdialog/data/audio"
if not os.path.exists(audio_data_dir):
    os.makedirs(audio_data_dir)


def userid_prefix():
    return userid()[:6]


'''
Note: the two connect() functions below are functionally exactly the same. However, there are two separate socketIO
namespaces (one for the chat template and one for all non-chat templates), so that the two have distinct event spaces,
and so two different functions are required (one for each namespace).
'''

hit_count = 0


@socketio.on('connect', namespace='/main')
def connect():
    """
    Signals backend when a user connects to the website on any template (page) other than the chat page.
    """
    print "User connected here..."
    backend = get_backend()
    backend.connect(userid())
    logger.info("User %s established connection on non-chat template" % userid_prefix())


@socketio.on('connect', namespace='/chat')
def connect():
    """
    Signals backend when a user connects to the website on the chat template.
    """
    print "User connected on chat template"
    backend = get_backend()
    backend.connect(userid())
    logger.info("User %s established connection on chat template" % userid_prefix())


@socketio.on('is_chat_valid', namespace='/chat')
def check_valid_chat(data):
    """
    Requests chat validity information from backend and returns it to the client. If the chat is invalid, the client acts
    accordingly (default is to refresh so that a new page can be served.
    :param data:
    :return: A dict containing information about the validity of the chat and a message (if any)
    that should be displayed to the user. (04/19: The message is currently not used by the client.)
    """
    backend = get_backend()

    if backend.is_chat_valid(userid()):
        logger.debug("Chat is still valid for user %s" % userid_prefix())
        return {'valid': True}
    else:
        logger.info("Chat is not valid for user %s" % userid_prefix())
        return {'valid': False, 'message': backend.get_user_message(userid())}


@socketio.on('check_status_change', namespace='/main')
def check_status_change(data):
    """
    Checks whether the user's status should be changed (from waiting to chat, chat to finished, etc), and returns
    that information to the client. If user status has changed, the client should act appropriately (default behavior
    is to refresh).
    :param data: A dict containing the current status of the user.
    :return: A dict containing a True/False value for whether the user's status should be changed or not.
    """
    backend = get_backend()
    assumed_status = Status.from_str(data['current_status'])

    if backend.is_status_unchanged(userid(), assumed_status):
        logger.debug("User %s status unchanged. Status: %s" % (userid_prefix(), Status._names[assumed_status]))
        return {'status_change': False}
    else:
        logger.info("User %s status changed from %s" % (userid_prefix(), Status._names[assumed_status]))
        return {'status_change': True}


@socketio.on('img_name', namespace='/main')
def img_name(data):
    pass



@socketio.on('submit_task', namespace='/main')
def submit_task(data):
    """
    Receives single task submission from client and sends to backend for logging.
    :param data: A dict containing the single task data.
    :return: None
    """
    print "Entering submit task..."
    global hit_count
    backend = get_backend()
    #logger.debug("User %s submitted single task. Form data: %s" % (userid_prefix(), str(data)))

    session_key = "key"#session["key"]
    session_img = "img"#session["imgs"][0]
    print "Session key: ", session_key
    #with open(audio_data_dir + '/' + session_key + "_" + session_img + "_" +
    #                  str(hit_count) + '.wav', 'wb') as f:
    #    f.write(data)
    #    hit_count += 1

    # Note "data" is a binary string of audio

    #data_log = {"session_id": session_key, "img_name": session["imgs"][0]}
    data_log = {"session_id": session_key, "img_name": "name"}
 
    print "About to submit task"
    # Modified database schema: (session_id, user_id, task_number, image_id)
    if type(data) == dict:
        backend.submit_single_task(userid(), data)
    else:
        #TODO: Handle this more cleanly
        # rand_data = {'restaurant': -1,
        #               'restaurant_index': -1,
        #                   'starter_text': 'cat',
        #                   'valid': True}
        print "data log: ", data_log
        backend.submit_single_task(userid(), data_log)
    print "Backend submitted..."


@socketio.on('get_img_dir', namespace='/main')
def send_img_dir_info(data):
    """
    Receives a ping from client-side asking for all images contained in directory and returns that
    information to client.
    :param data:
    :return:
    """
    img_dir = "/var/www/deepdialog/chat/app/static/img/"
    img_files = [img for img in os.listdir(img_dir) if os.path.isfile(os.path.join(img_dir, img))]
    rand_img = random.choice(img_files)
    try:
        session["imgs"].append(rand_img)
    except KeyError:
        print "reinitializing..."
        session["imgs"] = []
        session["imgs"].append(rand_img)
    print "emit image: ", rand_img
    emit("img_file", {"img": rand_img})


@socketio.on('img_loaded', namespace='/main')
def log_curr_img(data):
    """
    Receives the name of the image currently being loaded server
    :param data:
    :return:
    """
    pass


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    start_chat()
    join_room(session["room"])
    logger.debug("User %s joined chat room %d" % (userid_prefix(), session["room"]))
    emit_message_to_partner("Your friend has entered the room.", status_message=True)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    print "Sent message text..."
    msg = message['msg']
    write_to_file(msg)
    logger.debug("User %s said: %s" % (userid_prefix(), msg))
    emit_message_to_self("You: {}".format(msg))
    emit_message_to_partner("Friend: {}".format(msg))


@socketio.on('pick', namespace='/chat')
def pick(message):
    """
    Triggered when the user makes a selection in the chat on the client side. This function receives the selection from the client and
     sends it to the backend. The backend checks whether the user's selection matches their partner's selection. If yes,
     an 'endchat' event is emitted, telling the client that the chat has ended and that the page needs to be refreshed.
     If not, nothing happens. In both cases, the user's selection is logged to the chat window.
    :param message:
    :return:
    """
    backend = get_backend()
    chat_info = backend.get_chat_info(userid())
    # todo the variable names here probably all need to be changed to be generic
    restaurant_id = int(message['restaurant'])
    if restaurant_id == -1:
        return
    room = session["room"]
    restaurant, is_match = backend.pick_restaurant(userid(), restaurant_id)
    logger.debug("User %s in room %d selected: %s" % (userid_prefix(), room, restaurant))
    if is_match:
        logger.info("User %s selection matches with partner selection" % userid_prefix())
        emit_message_to_chat_room("Both users have selected: \"{}\"".format(restaurant), status_message=True)
        emit('endchat',
             {'message': "You've completed this task! Redirecting you..."},
             room=room)
    else:
        logger.debug("User %s selection doesn't match with partner selection" % userid_prefix())
        emit_message_to_partner("Your friend has selected: \"{}\"".format(restaurant), status_message=True)
        emit_message_to_self("You selected: \"{}\"".format(restaurant), status_message=True)
    write_outcome(restaurant_id, restaurant, chat_info)


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    """
    When a user is disconnected from the chat template, this function notifies the backend and the user is removed
    from that chat room accordingly.
    :return:
    """

    room = session["room"]

    leave_room(room)
    backend = get_backend()
    # backend.leave_room(userid())
    backend.disconnect(userid())
    logger.info("User %s disconnected from chat and left room %d" % (userid_prefix(), room))
    end_chat()


@socketio.on('disconnect', namespace='/main')
def disconnect():
    """
    Called when user disconnects from any non-chat template
    :return: No return value
    """
    backend = get_backend()
    backend.disconnect(userid())
    logger.info("User %s disconnected" % (userid_prefix()))


def emit_message_to_self(message, status_message=False):
    """
    Function to log a message to the user's own chat window.
    :param message:
    :param status_message:
    :return:
    """
    timestamp = datetime.now().strftime('%x %X')
    left_delim = "<" if status_message else ""
    right_delim = ">" if status_message else ""
    print "logging to own chat window yo", message
    emit('message', {'msg': "[{}] {}{}{}".format(timestamp, left_delim, message, right_delim)}, room=request.sid)


def emit_message_to_chat_room(message, status_message=False):
    """
    Function to log a message to the entire chat room
    :param message:
    :param status_message:
    :return:
    """
    timestamp = datetime.now().strftime('%x %X')
    left_delim = "<" if status_message else ""
    right_delim = ">" if status_message else ""
    emit('message', {'msg': "[{}] {}{}{}".format(timestamp, left_delim, message, right_delim)}, room=session["room"])


def emit_message_to_partner(message, status_message=False):
    """
    Function to log a message to the current user's partner's chat window.
    :param message:
    :param status_message:
    :return:
    """
    timestamp = datetime.now().strftime('%x %X')
    left_delim = "<" if status_message else ""
    right_delim = ">" if status_message else ""
    emit('message', {'msg': "[{}] {}{}{}".format(timestamp, left_delim, message, right_delim)}, room=session["room"],
         include_self=False)


def start_chat():
    """
    Starts the chat by creating a new file to log the chat transcript to.
    :return:
    """
    chat_info = get_backend().get_chat_info(userid())

    outfile = open('%s/ChatRoom_%s' % (app.config["user_params"]["logging"]["chat_dir"], str(session["room"])), 'a+')
    outfile.write("%s\t%s\tUser %s\tjoined\n" % (datetime.now().strftime(date_fmt),
                                                 chat_info.scenario["uuid"],
                                                 str(chat_info.agent_index)))
    outfile.write("%s\t%s\tUser %s has user ID %s\n" % (datetime.now().strftime(date_fmt),
                                                      chat_info.scenario["uuid"],
                                                      str(chat_info.agent_index),
                                                      userid()))
    outfile.close()


def end_chat():
    """
    Ends the chat
    :return:
    """
    outfile = open('%s/ChatRoom_%s' % (app.config["user_params"]["logging"]["chat_dir"], str(session["room"])), 'a+')
    outfile.write(
        "%s\t%s\n" % (datetime.now().strftime(date_fmt), app.config["user_params"]["logging"]["chat_delimiter"]))
    outfile.close()


def write_to_file(message):
    chat_info = get_backend().get_chat_info(userid())
    outfile = open('%s/ChatRoom_%s' % (app.config["user_params"]["logging"]["chat_dir"], str(session["room"])), 'a+')
    outfile.write("%s\t%s\tUser %s\t%s\n" %
                  (datetime.now().strftime(date_fmt), chat_info.scenario["uuid"],
                   str(chat_info.agent_index), message))
    outfile.close()


def write_outcome(idx, name, chat_info):
    """
    Writes the outcome (user selection) to the chat transcript.
    :param idx:
    :param name:
    :param chat_info:
    :return:
    """
    outfile = open('%s/ChatRoom_%s' % (app.config["user_params"]["logging"]["chat_dir"], str(session["room"])), 'a+')
    outfile.write("%s\t%s\tUser %s\tSelected %d:\t%s\n" %
                  (datetime.now().strftime(date_fmt), chat_info.scenario["uuid"], chat_info.agent_index, idx, name))
