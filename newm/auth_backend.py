import os
import logging
import pam
import sys
import socket
import json

logger = logging.getLogger(__name__)

from .config import configured_value

conf_greeter_user = configured_value('greeter_user', 'greeter')

class _PAMBackend:
    def __init__(self, auth):
        self.auth = auth
        self._pam = pam.pam()
        self._user = None

    def init_auth(self, user):
        self._user = user
        self.auth._request_cred("Password?", user)

    def enter_cred(self, cred):
        res = self._pam.authenticate(self._user, cred)
        self.auth._auth_result(res)
        if not res:
            self.init_auth(self._user)

    def start_session(self):
        logger.warn("Unsupported operation")

class _GreetdBackend:
    def __init__(self, auth):
        self.auth = auth
        self._user = None
        self._socket = None

    def _open_socket(self):
        if "GREETD_SOCK" not in os.environ:
            logger.error("Not in a greetd session")
            return

        greetd_sock = os.environ["GREETD_SOCK"]
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(greetd_sock)

        logger.debug("Connected to greetd")

    def _send(self, msg):
        if self._socket is None:
            self._open_socket()
        msg_str = json.dumps(msg).encode('utf-8')
        msg_str = len(msg_str).to_bytes(4, sys.byteorder) + msg_str
        self._socket.send(msg_str)

        resp_len = int.from_bytes(self._socket.recv(4), sys.byteorder)
        resp = self._socket.recv(resp_len).decode("utf-8")
        return json.loads(resp)

    def init_auth(self, user):
        self._user = user

        result = self._send({"type":"cancel_session"})
        result = self._send({"type":"create_session", "username": user})

        if result["type"] == "auth_message":
            self.auth._request_cred(result["auth_message"], self._user)



    def enter_cred(self, cred):
        result = self._send({"type":"post_auth_message_response", "response": cred})
        if result["type"] == "auth_message":
            self.auth._request_cred(result["auth_message"], self._user)
        else:
            self.auth._auth_result(result["type"] == "success")

    def start_session(self):
        self._send({"type": "start_session", "cmd": ["start-newm"]})


class AuthBackend:
    def __init__(self, layout):
        self.layout = layout
        self._users = []
        greeter_user = conf_greeter_user()
        with open('/etc/passwd', 'r') as pwd:
            for u in pwd:
                u = u.split(":")
                if "nologin" not in u[6]:
                    self._users += [(u[0], int(u[2]), u[6], u[0] == greeter_user)] # name, uid, login shell, is_greeter

        if len([g for g in self._users if g[3]]) == 0:
            logger.warn("Could not find greeter: %s", greeter_user)
        if len([g for g in self._users if g[1] == os.getuid()]) == 0:
            logger.error("Fatal! Could not find current user: %s", greeter_user)

        """
        initial
            -> wait_user
            -> wait_cred
        """
        self._state = "initial"

        self._backend = None
        if self.is_greeter():
            self._backend = _GreetdBackend(self)
        else:
            self._backend = _PAMBackend(self)

    def is_greeter(self):
        user = [u for u in self._users if u[1] == os.getuid()]
        if len(user) == 0:
            logger.warn("Could not find current user: %d", os.getuid())
            return False
        return user[0][3]

    def init_session(self):
        self._state = "wait_user"

        possible_users = [u for u in self._users if not u[3]]
        self.layout.panel_endpoint.broadcast({
            'kind': 'auth_request_user',
            'users': [u[0] for u in possible_users]
        })

    def lock(self):
        current_user = [u for u in self._users if u[1] == os.getuid()]
        if len(current_user) > 0 and not current_user[0][3]:
            self._backend.init_auth(current_user[0][0])

    """
    Panels endpoint
    """
    def on_message(self, msg):
        if msg['kind'] == "auth_register" and self._state == "wait_user":
            self.init_session()
        elif msg['kind'] == "auth_register" and self._state == "wait_cred":
            logger.warn("Unexpected")
        elif msg['kind'] == "auth_choose_user":
            self._backend.init_auth(msg['user'])
        elif msg['kind'] == "auth_enter_cred":
            self._backend.enter_cred(msg['cred'])

    """
    Backends endpoint
    """
    def _request_cred(self, message, for_user):
        self.layout.panel_endpoint.broadcast({
            'kind': 'auth_request_cred',
            'user': for_user,
            'message': message
        })
        self._state = "wait_cred"

    def _auth_result(self, successful):

        if not successful:
            """
            Backend should retry on its own
            """
            logger.debug("Verification failed")
            return

        self._state = "initial"

        if self.is_greeter():
            logger.debug("starting session after successful verification")
            self._backend.start_session()
            self.layout.terminate()
        else:
            logger.debug("unlocking after successful verification")
            self.layout._trusted_unlock()

