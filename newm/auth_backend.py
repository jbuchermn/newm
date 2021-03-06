import os
import logging
import pam

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
        pass

class _GreetdBackend:
    def __init__(self, auth):
        self.auth = auth
        self._user = None

    def init_auth(self, user):
        self._user = user
        self.auth._request_cred("Password?", user)

    def enter_cred(self, cred):
        self.auth._auth_result(True)

    def start_session(self):
        pass


class AuthBackend:
    def __init__(self, layout):
        self.layout = layout
        self._users = []
        greeter_user = self.layout.config['greeter_user'] if 'greeter_user' in self.layout.config else 'greeter'
        with open('/etc/passwd', 'r') as pwd:
            for u in pwd:
                u = u.split(":")
                if "nologin" not in u[6]:
                    self._users += [(u[0], int(u[2]), u[6], u[0] == greeter_user)] # name, uid, login shell, is_greeter

        if len([g for g in self._users if g[3]]) == 0:
            logging.warn("Could not find greeter: %s", greeter_user)
        if len([g for g in self._users if g[1] == os.getuid()]) == 0:
            logging.error("Fatal! Could not find current user: %s", greeter_user)

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
            logging.warn("Could not find current user: %d", os.getuid())
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
        if len(current_user) > 0:
            self._backend.init_auth(current_user[0][0])

    """
    Panels endpoint
    """
    def on_message(self, msg):
        if msg['kind'] == "auth_register" and self._state == "wait_user":
            self.init_session()
        elif msg['kind'] == "auth_register" and self._state == "wait_cred":
            logging.warn("Unexpected")
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
            logging.debug("Verification failed")
            return

        self._state = "initial"

        if self.is_greeter():
            logging.debug("starting session after successful verification")
            self._backend.start_session()
            self.layout.terminate()
        else:
            logging.debug("unlocking after successful verification")
            self.layout._trusted_unlock()

