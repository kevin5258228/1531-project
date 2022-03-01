"""
Server.py -- contains all routes for Slackr app.
H11A-quadruples, April 2020.
"""

import sys
import time
import threading
from json import dumps
from flask import Flask, request, send_from_directory
from flask_cors import CORS
from funcs.auth import (
    auth_login,
    auth_logout,
    auth_register,
    auth_passwordreset_request,
    auth_passwordreset_reset
)
from funcs.channel import (
    channel_invite,
    channel_details,
    channel_messages,
    channel_leave,
    channel_join,
    channel_addowner,
    channel_removeowner
)
from funcs.channels import channels_list, channels_listall, channels_create
from funcs.message import (
    message_send,
    message_sendlater,
    message_react,
    message_unreact,
    message_pin,
    message_unpin,
    message_remove,
    message_edit
)
from funcs.user import (
    user_profile,
    user_profile_setname,
    user_profile_setemail,
    user_profile_sethandle
)
from funcs.user_profile_uploadphoto import user_profile_uploadphoto
from funcs.other import (
    users_all,
    search,
    workspace_reset,
    standup_start,
    standup_active,
    standup_send,
    admin_userpermission_change,
    admin_user_remove
)
from database.database import (
    AUTH_DATABASE,
    CHANNELS_DATABASE,
    MESSAGES_DATABASE,
    update_database,
    get_database
)
from database.helpers_auth import is_user_slackr_owner
from constants import (
    AUTH_DB_PATH, CHANNELS_DB_PATH, MESSAGES_DB_PATH,
    SAVE_INTERVAL, PFP_FOLDER, LOCALHOST_URL, DEFAULT_PFP
)

def defaultHandler(err):
    response = err.get_response()
    print("response", err, err.get_response())
    response.data = dumps({
        "code": err.code,
        "name": "System Error",
        "message": err.get_description(),
    })
    response.content_type = "application/json"
    return response

APP = Flask(__name__)
CORS(APP)

APP.config["TRAP_HTTP_EXCEPTIONS"] = True
APP.register_error_handler(Exception, defaultHandler)


####################################################################
##                          auth routes                           ##
####################################################################

@APP.route("/auth/login", methods=["POST"])
def route_auth_login():
    data = request.get_json()
    return dumps(auth_login(data["email"], data["password"]))

@APP.route("/auth/logout", methods=["POST"])
def route_auth_logout():
    data = request.get_json()
    return dumps(auth_logout(data["token"]))

@APP.route("/auth/register", methods=["POST"])
def route_auth_register():
    data = request.get_json()
    ## Register user and then serve the default pfp if it is the first user to register
    output = auth_register(
        data["email"], data["password"], data["name_first"], data["name_last"]
    )
    if is_user_slackr_owner(output["u_id"]):
        user_profile_uploadphoto(output["token"], DEFAULT_PFP, 0, 0, 400, 400)
    return dumps(output)

@APP.route("/auth/passwordreset/request", methods=["POST"])
def route_auth_passwordreset_request():
    data = request.get_json()
    return dumps(auth_passwordreset_request(data["email"]))

@APP.route("/auth/passwordreset/reset", methods=["POST"])
def route_auth_passwordreset_reset():
    data = request.get_json()
    return dumps(auth_passwordreset_reset(
        data["reset_code"], data["new_password"]
    ))


####################################################################
##                        channel routes                          ##
####################################################################

@APP.route("/channel/invite", methods=["POST"])
def route_channel_invite():
    data = request.get_json()
    return dumps(channel_invite(
        data["token"], int(data["channel_id"]), int(data["u_id"])
    ))

@APP.route("/channel/details", methods=["GET"])
def route_channel_details():
    data = request.args
    return dumps(channel_details(data["token"], int(data["channel_id"])))

@APP.route("/channel/messages", methods=["GET"])
def route_channel_messages():
    data = request.args
    return dumps(channel_messages(
        data["token"], int(data["channel_id"]), int(data["start"])
    ))

@APP.route("/channel/leave", methods=["POST"])
def route_channel_leave():
    data = request.get_json()
    return dumps(channel_leave(data["token"], int(data["channel_id"])))

@APP.route("/channel/join", methods=["POST"])
def route_channel_join():
    data = request.get_json()
    return dumps(channel_join(data["token"], int(data["channel_id"])))

@APP.route("/channel/addowner", methods=["POST"])
def route_channel_addowner():
    data = request.get_json()
    return dumps(channel_addowner(
        data["token"], int(data["channel_id"]), int(data["u_id"])
    ))

@APP.route("/channel/removeowner", methods=["POST"])
def route_channel_removeowner():
    data = request.get_json()
    return dumps(channel_removeowner(
        data["token"], int(data["channel_id"]), int(data["u_id"])
    ))


####################################################################
##                       channels routes                          ##
####################################################################

@APP.route("/channels/list", methods=["GET"])
def route_channels_list():
    data = request.args
    return dumps(channels_list(data["token"]))

@APP.route("/channels/listall", methods=["GET"])
def route_channels_listall():
    data = request.args
    return dumps(channels_listall(data["token"]))

@APP.route("/channels/create", methods=["POST"])
def route_channels_create():
    data = request.get_json()
    return dumps(channels_create(
        data["token"], data["name"], data["is_public"]
    ))


####################################################################
##                        message routes                          ##
####################################################################

@APP.route("/message/send", methods=["POST"])
def route_message_send():
    data = request.get_json()
    return dumps(message_send(
        data["token"], int(data["channel_id"]), data["message"]
    ))

@APP.route("/message/sendlater", methods=["POST"])
def route_message_sendlater():
    data = request.get_json()
    return dumps(message_sendlater(
        data["token"], int(data["channel_id"]), data["message"], int(data["time_sent"])
    ))

@APP.route("/message/react", methods=["POST"])
def route_message_react():
    data = request.get_json()
    return dumps(message_react(
        data["token"], int(data["message_id"]), int(data["react_id"])
    ))

@APP.route("/message/unreact", methods=["POST"])
def route_message_unreact():
    data = request.get_json()
    return dumps(message_unreact(
        data["token"], int(data["message_id"]), int(data["react_id"])
    ))

@APP.route("/message/pin", methods=["POST"])
def route_message_pin():
    data = request.get_json()
    return dumps(message_pin(data["token"], int(data["message_id"])))

@APP.route("/message/unpin", methods=["POST"])
def route_message_unpin():
    data = request.get_json()
    return dumps(message_unpin(data["token"], int(data["message_id"])))

@APP.route("/message/remove", methods=["DELETE"])
def route_message_remove():
    data = request.get_json()
    return dumps(message_remove(data["token"], int(data["message_id"])))

@APP.route("/message/edit", methods=["PUT"])
def route_message_edit():
    data = request.get_json()
    return dumps(message_edit(
        data["token"], int(data["message_id"]), data["message"]
    ))


####################################################################
##                          user routes                           ##
####################################################################

@APP.route("/user/profile", methods=["GET"])
def route_user_profile():
    data = request.args
    return dumps(user_profile(data["token"], int(data["u_id"])))

@APP.route("/user/profile/setname", methods=["PUT"])
def route_user_profile_setname():
    data = request.get_json()
    return dumps(user_profile_setname(
        data["token"], data["name_first"], data["name_last"]
    ))

@APP.route("/user/profile/setemail", methods=["PUT"])
def route_user_profile_setemail():
    data = request.get_json()
    return dumps(user_profile_setemail(data["token"], data["email"]))

@APP.route("/user/profile/sethandle", methods=["PUT"])
def route_user_profile_sethandle():
    data = request.get_json()
    return dumps(user_profile_sethandle(data["token"], data["handle_str"]))

@APP.route("/user/profile/uploadphoto", methods=["POST"])
def route_user_profile_uploadphoto():
    data = request.get_json()
    return dumps(user_profile_uploadphoto(
        data["token"], data["img_url"],
        int(data["x_start"]), int(data["y_start"]),
        int(data["x_end"]), int(data["y_end"])
    ))

@APP.route("/imgurl/<img_name>")
def upload_img(img_name):
    """
    Uploads an image with title f"{img_name}" taken from PFP_FOLDER
    to the route f"/imgurl/{img_name}".

    Args:
        img_name (str): Name of the image being served.
    """
    return send_from_directory(PFP_FOLDER, f"{img_name}", mimetype="image/jpg")


####################################################################
##                         other routes                           ##
####################################################################

@APP.route("/users/all", methods=["GET"])
def route_users_all():
    data = request.args
    return dumps(users_all(data["token"]))

@APP.route("/search", methods=["GET"])
def route_search():
    data = request.args
    return dumps(search(data["token"], data["query_str"]))

@APP.route("/standup/start", methods=["POST"])
def route_standup_start():
    data = request.get_json()
    return dumps(standup_start(
        data["token"], int(data["channel_id"]), int(data["length"])
    ))

@APP.route("/standup/active", methods=["GET"])
def route_standup_active():
    data = request.args
    return dumps(standup_active(data["token"], int(data["channel_id"])))

@APP.route("/standup/send", methods=["POST"])
def route_standup_send():
    data = request.get_json()
    return dumps(standup_send(
        data["token"], int(data["channel_id"]), data["message"]
    ))

@APP.route("/admin/userpermission/change", methods=["POST"])
def route_admin_userpermission_change():
    data = request.get_json()
    return dumps(admin_userpermission_change(
        data["token"], int(data["u_id"]), int(data["permission_id"])
    ))

@APP.route("/admin/user/remove", methods=["DELETE"])
def route_admin_user_remove():
    data = request.args
    return dumps(admin_user_remove(data["token"], int(data["u_id"])))

@APP.route("/workspace/reset", methods=["POST"])
def route_workspace_reset():
    return dumps(workspace_reset())

#####################################################################
#####################################################################

def data_reload():
    """
    Load pickled databases.
    """
    AUTH_DATABASE.update(get_database(AUTH_DB_PATH))
    CHANNELS_DATABASE.update(get_database(CHANNELS_DB_PATH))
    MESSAGES_DATABASE.update(get_database(MESSAGES_DB_PATH))

def data_save():
    """
    Pickle dump all databases.
    """
    update_database(AUTH_DB_PATH, AUTH_DATABASE.get())
    update_database(CHANNELS_DB_PATH, CHANNELS_DATABASE.get())
    update_database(MESSAGES_DB_PATH, MESSAGES_DATABASE.get())

def data_save_regularly():
    """
    Save data every 30 seconds.
    """
    while True:
        time.sleep(SAVE_INTERVAL)
        data_save()

#####################################################################
#####################################################################

if __name__ == "__main__":
    try:
        ## reload persisted data on server start
        data_reload()
    except FileNotFoundError:
        ## pickled files don't exist, so initialise them
        data_save()

    ## save port settings
    PORT = int(sys.argv[1]) if len(sys.argv) == 2 else 8080
    FILE = open("port_settings.py", "w")
    FILE.write(
        f"PORT = '{PORT}'\n"
        f"BASE_URL = '{LOCALHOST_URL}:' + '{PORT}'"
    )
    FILE.close()

    ## start a daemon thread to pickle data every 30 seconds
    TIMER = threading.Thread(target=data_save_regularly, daemon=True)
    TIMER.start()

    ## run app
    APP.run(port=PORT)
