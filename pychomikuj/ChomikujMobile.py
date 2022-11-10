from .pychomikuj_exceptions import *
import requests
import uuid


class ChomikujMobile:
    def __init__(self, username, password):
        # Define class properties
        # Server throws Error 500 when default user-agent is provided. UUID is used for unique device fingerprinting, here it's randomly generated.
        self.USER_AGENT = f"android/3.61 ({uuid.uuid4()}; Google Pixel 6)"

        self.account_balance = dict()
        self.transfer = int()
        self.has_unlimited_transfer = bool()
        self.points = int()
        self.points_available = bool()
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
        }, headers={"token": ""})

        # Check are login info correct
        if login_request.status_code != 200:
            if login_request.status_code == 403:
                raise IncorrectChomikPasswordException(
                    "Login info provided was incorrect")
            else:
                raise UnknownChomikErrorException(
                    f"Unknown error! Status code: {login_request.status_code}")

        # Update variables
        # Reassign API key
        self.api_key = login_request.json()["ApiKey"]
        self.req_ses.headers["api-key"] = self.api_key  
        self.get_account_balance()
        self.account_id = login_request.json()["AccountId"]
        self.account_name = login_request.json()["AccountName"]

    def get_account_balance(self):
        self.account_balance = self.req_ses.get("https://mobile.chomikuj.pl/api/v3/account/info", headers={"token": "22dbb80e516477793934fa0add1b8929"}).json()
        self.transfer = self.account_balance["Transfer"]
        self.has_unlimited_transfer = self.account_balance["HasUnlimitedTransfer"]
        self.points = self.account_balance["Points"]
        self.points_available = self.account_balance["PointsAvailable"]

    def query(self, query_field, page_number, media_type):
        return self.req_ses.get("https://mobile.chomikuj.pl/api/v3/files/search", params={
            "Query": query_field,
            "PageNumber": str(page_number),
            "MediaType": media_type
        }, headers={"Token": ""}).json()
