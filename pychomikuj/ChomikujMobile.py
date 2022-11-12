from .pychomikuj_exceptions import *
import urllib.parse
import requests
import hashlib
import uuid


class ChomikujMobile:
    def __init__(self, username, password):
        # Define class properties
        # Server throws Error 500 when default user-agent is provided. UUID is used for unique device fingerprinting, here it's randomly generated.
        self.USER_AGENT = f"android/3.61 ({uuid.uuid4()}; Google Pixel 6)"
        self.API_LOCATION = "https://mobile.chomikuj.pl/"
        self.SALT = "wzrwYua$.DSe8suk!`'2"  # String used by Chomikuj to salt MD5

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

        # Additional data needs to be added for hashing process. This data will be provided
        additional_endpoint_data = r'{"AccountName":"ACC_NAME","Password":"PASSWD"}'
        additional_endpoint_data = additional_endpoint_data.replace(
            "ACC_NAME", username)
        additional_endpoint_data = additional_endpoint_data.replace(
            "PASSWD", password)

        endpoint = f'api/v3/account/login'
        login_request = self.req_ses.post(f"{self.API_LOCATION}{endpoint}", json={
            "AccountName": username,
            "Password": password
        }, headers={"token": self.__hash_token(f"{endpoint}", additional_endpoint_data)})

        # Check are login info correct
        if login_request.status_code == 403:
            raise IncorrectChomikPasswordException(username)

        # Update variables
        # Reassign API key
        self.api_key = login_request.json()["ApiKey"]
        self.req_ses.headers["api-key"] = self.api_key
        self.get_account_balance()
        self.account_id = login_request.json()["AccountId"]
        self.account_name = login_request.json()["AccountName"]

    def get_account_balance(self):
        endpoint = "api/v3/account/info"

        self.account_balance = self.req_ses.get(f"{self.API_LOCATION}{endpoint}", headers={
                                                "token": self.__hash_token(endpoint)}).json()
        self.transfer = self.account_balance["Transfer"]
        self.has_unlimited_transfer = self.account_balance["HasUnlimitedTransfer"]
        self.points = self.account_balance["Points"]
        self.points_available = self.account_balance["PointsAvailable"]

    def list_directory(self, parent_id=0, page=1, account_id=None):
        endpoint = "api/v3/folders"

        if account_id == None:
            additional_endpoint_data = f"?Parent={parent_id}&page={page}"
            params = {
                "Parent": str(parent_id),
                "page": str(page)
            }
        else:
            additional_endpoint_data = f"?AccountId={account_id}&Parent={parent_id}&page={page}"
            params = {
                "AccountId": str(account_id),
                "Parent": str(parent_id),
                "page": str(page)
            }

        list_directory_request = self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params=params, headers={
                                                  "Token": self.__hash_token(endpoint, additional_endpoint_data)})
        if list_directory_request.status_code == 401:
            raise PasswordProtectedDirectoryException(
                "This directory is password protected!")
        return list_directory_request.json()

    def authenticate_password(self, account_id, folder_id, password):
        endpoint = "api/v3/folders/password"

        additional_endpoint_data = r'{"AccountId":"ACC_ID","FolderId":"DIR_ID","Password":"PASSWD"}'
        additional_endpoint_data = additional_endpoint_data.replace(
            "ACC_ID", str(account_id))
        additional_endpoint_data = additional_endpoint_data.replace(
            "DIR_ID", str(folder_id))
        additional_endpoint_data = additional_endpoint_data.replace(
            "PASSWD", password)

        unlock_directory_request = self.req_ses.post(f"{self.API_LOCATION}{endpoint}", json={
            "AccountId": str(account_id),
            "FolderId": str(folder_id),
            "Password": password
        }, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)})

        if unlock_directory_request.status_code == 401:
            raise IncorrectDirectoryPasswordException(
                folder_id)

    def get_download_url(self, file_id):
        endpoint = "api/v3/files/download"

        additional_endpoint_data = f"?FileId={file_id}"

        get_download_url_request = self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params={
                                                    "FileId": file_id}, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)})

        if get_download_url_request.status_code == 404:
            raise FileInPasswordProtectedDirOrNotFoundException(
                file_id)
        if get_download_url_request.json()["Code"] == 604:
            raise FileIsADirectoryException(file_id)
        if get_download_url_request.json()["Code"] == 605:
            raise NotEnoughTransferException(
                f"User Transfer: {self.transfer}. File ID: {file_id}")

        self.get_account_balance()
        return get_download_url_request.json()["FileUrl"]

    def create_directory(self, folder_name, parent_id):
        endpoint = "api/v3/folders/create"
        additional_endpoint_data = '{"FolderName":"DIR_NAME","ParentId":"PRNT_ID"}'
        additional_endpoint_data = additional_endpoint_data.replace(
            "DIR_NAME", folder_name)
        additional_endpoint_data = additional_endpoint_data.replace(
            "PRNT_ID", str(parent_id))

        create_directory_request = self.req_ses.post(f"{self.API_LOCATION}{endpoint}", json={
            "FolderName": folder_name,
            "ParentId": str(parent_id)
        }, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)})

        if create_directory_request.json()["Code"] == 404:
            raise ParentFolderDoesntExistException(parent_id)

        return create_directory_request.json()["FolderId"]

    def query(self, query_field, page=1, media_type="All", extension=None):
        endpoint = "api/v3/files/search"

        query_for_hash = f"{urllib.parse.quote(query_field)}".replace(
            "%20", "+")
        if media_type == "Chomiki":
            additional_endpoint_data = f"?Query={query_for_hash}&PageNumber={page}"
            params = {
                "Query": query_field,
                "PageNumber": str(page)
            }
        elif extension != None:
            additional_endpoint_data = f"?Extension={extension}&Query={query_for_hash}&PageNumber={page}&MediaType={media_type}"
            params = {
                "Extension": extension,
                "Query": query_field,
                "PageNumber": str(page),
                "MediaType": media_type
            }
        else:
            additional_endpoint_data = f"?Query={query_for_hash}&PageNumber={page}&MediaType={media_type}"
            params = {
                "Query": query_field,
                "PageNumber": str(page),
                "MediaType": media_type
            }

        return self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params=params, headers={"Token": self.__hash_token(f"{endpoint}", additional_endpoint_data)}).json()

    def get_friend_list(self, page=1):
        endpoint = "api/v3/friends"
        additional_endpoint_data = f"?PageNumber={page}"
        return self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params={"PageNumber": page}, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)}).json()

    def get_copy_list(self, page=1):
        endpoint = "api/v3/files/copies"
        additional_endpoint_data = f"?Page={page}"
        return self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params={"Page": page}, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)}).json()

    def get_inbox_messages(self, page=1):
        endpoint = "api/v3/messages/inbox"
        additional_endpoint_data = f"?PageNumber={page}"
        return self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params={"PageNumber": page}, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)}).json()

    def get_outbox_messages(self, page=1):
        endpoint = "api/v3/messages/outbox"
        additional_endpoint_data = f"?PageNumber={page}"
        return self.req_ses.get(f"{self.API_LOCATION}{endpoint}", params={"PageNumber": page}, headers={"Token": self.__hash_token(endpoint, additional_endpoint_data)}).json()

    def mark_all_messages_as_read(self):
        endpoint = "api/v3/messages/markAllAsRead"
        self.req_ses.post(f"{self.API_LOCATION}{endpoint}")

    def __hash_token(self, endpoint, additional_endpoint_data=None):
        if additional_endpoint_data == None:
            string_to_hash = f"{endpoint}{self.SALT}"
        else:
            string_to_hash = f"{endpoint}{additional_endpoint_data}{self.SALT}"
        return hashlib.md5(string_to_hash.encode("UTF-8")).hexdigest()
