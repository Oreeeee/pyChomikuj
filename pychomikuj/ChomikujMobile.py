from .pychomikuj_exceptions import *
import requests
import uuid


class ChomikujMobile:
    def __init__(self, username, password):
        # Define class properties
        # Server throws Error 500 when default user-agent is provided. UUID is used for unique device fingerprinting, here it's randomly generated.
        self.USER_AGENT = f"android/3.61 ({uuid.uuid4()}; Google Pixel 6)"

        self.account_balance = dict()
        self.account_id = int()
        self.account_name = str()
        self.api_key = "0"

        # Initialize requests session
        self.req_ses = requests.Session()
        self.req_ses.headers["User-Agent"] = self.USER_AGENT
        self.req_ses.headers["api-key"] = self.api_key

        # Log into Chomikuj
        login_request = self.req_ses.post("https://mobile.chomikuj.pl/api/v3/account/login", json={
            "AccountName": username,
            "Password": password
        }, headers={"token": "57c983466c85279c51e48676f302da29"})

        # Check are login info correct
        if login_request.status_code != 200:
            if login_request.status_code == 403:
                raise IncorrectChomikPasswordException(
                    "Login info provided was incorrect")
            else:
                raise UnknownChomikErrorException(
                    f"Unknown error! Status code: {login_request.status_code}")

        # Update variables
        self.account_balance = login_request.json()["AccountBalance"]
        self.account_id = login_request.json()["AccountId"]
        self.account_name = login_request.json()["AccountName"]
        self.api_key = login_request.json()["ApiKey"]

        # Reassign API key
        self.req_ses.headers["api-key"] = self.api_key
