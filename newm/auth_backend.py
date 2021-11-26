from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING

import os
import logging
import pam # type: ignore
import sys
import socket
import json

from .config import configured_value

if TYPE_CHECKING:
    from .layout import Layout

logger = logging.getLogger(__name__)

conf_greeter_user = configured_value('greeter_user', 'greeter')

class _Backend:
    def init_auth(self, user: str) -> None:
        pass
    def enter_cred(self, cred: str) -> None:
        pass
    def start_session(self) -> None:
        pass


class _PAMBackend(_Backend):
    def __init__(self, auth: AuthBackend) -> None:
        self.auth = auth
        self._pam = pam.pam()
        self._user: Optional[str] = None

    def init_auth(self, user: str) -> None:
        self._user = user
        self.auth._request_cred("Password?", user)

    def enter_cred(self, cred: str) -> None:
        res = self._pam.authenticate(self._user, cred)
        self.auth._auth_result(res)
        if not res and self._user is not None:
            self.init_auth(self._user)

    def start_session(self) -> None:
        logger.warn("Unsupported operation")

class _GreetdBackend(_Backend):
    def __init__(self, auth: AuthBackend) -> None:
        self.auth = auth
        self._user: Optional[str] = None
        self._socket: Optional[socket.socket] = None

    def _open_socket(self) -> None:
        if "GREETD_SOCK" not in os.environ:
            logger.error("Not in a greetd session")
            return

        greetd_sock = os.environ["GREETD_SOCK"]
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(greetd_sock)

        logger.debug("Connected to greetd")

    def _send(self, msg: Any) -> dict[str, Any]:
        if self._socket is None:
            self._open_socket()
        if self._socket is None:
            return {}

        msg_str = json.dumps(msg).encode('utf-8')
        msg_str = len(msg_str).to_bytes(4, sys.byteorder) + msg_str
        self._socket.send(msg_str)

        resp_len = int.from_bytes(self._socket.recv(4), sys.byteorder)
        resp = self._socket.recv(resp_len).decode("utf-8")
        return json.loads(resp)

    def init_auth(self, user: str) -> None:
        self._user = user

        result = self._send({"type":"cancel_session"})
        result = self._send({"type":"create_session", "username": user})

        if result["type"] == "auth_message":
            self.auth._request_cred(result["auth_message"], self._user)

    def enter_cred(self, cred: str) -> None:
        result = self._send({"type":"post_auth_message_response", "response": cred})
        if result["type"] == "auth_message":
            self.auth._request_cred(result["auth_message"], self._user)
        else:
            self.auth._auth_result(result["type"] == "success")

    def start_session(self) -> None:
        self._send({"type": "start_session", "cmd": ["start-newm"]})


class AuthBackend:
    def __init__(self, layout: Layout) -> None:
        self.layout = layout
        self._users: list[tuple[str, int, str, bool]] = []
        greeter_user = conf_greeter_user()
        with open('/etc/passwd', 'r') as pwd:
            for user in pwd:
                u = user.split(":")
                if "nologin" not in u[6]:
                    self._users += [(u[0], int(u[2]), u[6], u[0] == greeter_user)] # name, uid, login shell, is_greeter

        if len([g for g in self._users if g[3]]) == 0:
            logger.warn("Could not find greeter: %s", greeter_user)
        if len([g for g in self._users if g[1] == os.getuid()]) == 0:
            logger.error("Fatal! Could not find current user")

        """
        initial
            -> wait_user
            -> wait_cred
        """
        self._state = "initial"
        self._waiting_cred: dict[str, Any] = {}

        self._backend: _Backend = _GreetdBackend(self) if self.is_greeter() else _PAMBackend(self)

    def is_greeter(self) -> bool:
        user = [u for u in self._users if u[1] == os.getuid()]
        if len(user) == 0:
            logger.warn("Could not find current user: %d", os.getuid())
            return False
        return user[0][3]

    def init_session(self) -> None:
        self._state = "wait_user"

        possible_users = [u for u in self._users if not u[3]]
        logger.debug("Requesting user")
        self.layout.panel_endpoint.broadcast({
            'kind': 'auth_request_user',
            'users': [u[0] for u in possible_users]
        })

    def lock(self) -> None:
        current_user = [u for u in self._users if u[1] == os.getuid()]
        logger.debug("Locking for user %s" % current_user)
        if len(current_user) > 0 and not current_user[0][3]:
            self._backend.init_auth(current_user[0][0])

    """
    Panels endpoint
    """
    def on_message(self, msg: dict[str, Any]) -> None:
        logger.debug("Received kind=%s" % msg['kind'])
        if msg['kind'] == "auth_register":
            logger.debug("New auth client")
            if self._state == "wait_user":
                self.init_session()
            elif self._state == "wait_cred":
                self._request_cred()
            else:
                logger.debug("Acking register")
                self.layout.panel_endpoint.broadcast({ 'kind': 'auth_ack' })

        elif msg['kind'] == "auth_choose_user":
            logger.debug("Received user %s" % msg['user'])
            self._backend.init_auth(msg['user'])
        elif msg['kind'] == "auth_enter_cred":
            logger.debug("Received credentials")
            self._backend.enter_cred(msg['cred'])

    """
    Backends endpoint
    """
    def _request_cred(self, message: Optional[str]=None, for_user: Optional[str]=None) -> None:
        if message is not None and for_user is not None:
            self._waiting_cred = {
                'kind': 'auth_request_cred',
                'user': for_user,
                'message': message
            }

        logger.debug("Requesting credentials")
        self.layout.panel_endpoint.broadcast(self._waiting_cred)
        self._state = "wait_cred"

    def _auth_result(self, successful: bool) -> None:

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
