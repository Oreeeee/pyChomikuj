from .set_up_logging import set_up_logging
from .pychomikuj_exceptions import *
import urllib.parse
import collections
import requests
import logging
import hashlib
import uuid
import zlib
import os


class ChomikujMobile:
    def __init__(
        self, username, password, proxy_ip=None, proxy_port=None, logging_level=None
    ):
        # Set up logging
        if logging_level != None:
            set_up_logging(logging_level)

        logging.debug("Setting up the API")

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
        logging.debug(
            f"Initializing requests session proxy_ip={proxy_ip} proxy_port={proxy_port}"
        )

        self.req_ses = requests.Session()
        if proxy_port and proxy_ip != None:
            self.req_ses.proxies = {
                "http": f"http://{proxy_ip}:{proxy_port}",
                "https": f"http://{proxy_ip}:{proxy_port}",
            }
        self.req_ses.headers["User-Agent"] = self.USER_AGENT
        self.req_ses.headers["api-key"] = self.api_key

        # Log into Chomikuj

        # Additional data needs to be added for hashing process. This data will be provided
        dict_data = '{"AccountName":"ACC_NAME","Password":"PASSWD"}'
        dict_data = dict_data.replace("ACC_NAME", username)
        dict_data = dict_data.replace("PASSWD", password)

        logging.info(f"Logging in as {username}")

        endpoint = f"api/v3/account/login"
        logging.debug(f"Using endpoint {endpoint} to log in")
        login_request = self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            json={"AccountName": username, "Password": password},
            headers={"token": self.__hash_token(f"{endpoint}", dict_data=dict_data)},
        )

        # Check are login info correct
        if login_request.status_code == 403:
            raise IncorrectChomikPasswordException(username)

        logging.info(f"Logged in successfully as {username}")

        # Update variables
        # Reassign API key
        self.api_key = login_request.json()["ApiKey"]
        self.req_ses.headers["api-key"] = self.api_key
        self.get_account_balance()
        self.account_id = login_request.json()["AccountId"]
        self.account_name = login_request.json()["AccountName"]

    def get_account_balance(self):
        endpoint = "api/v3/account/info"

        logging.debug(f"Executing get_account_balance(). Endpoint={endpoint}")

        self.account_balance = self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            headers={"token": self.__hash_token(endpoint)},
        ).json()
        self.transfer = self.account_balance["Transfer"]
        self.has_unlimited_transfer = self.account_balance["HasUnlimitedTransfer"]
        self.points = self.account_balance["Points"]
        self.points_available = self.account_balance["PointsAvailable"]

    def list_directory(self, id=0, page=1, account_id=None):
        endpoint = "api/v3/folders"

        if account_id == None:
            params = {"Parent": str(id), "page": str(page)}
        else:
            params = {
                "AccountId": str(account_id),
                "Parent": str(id),
                "page": str(page),
            }

        logging.debug(
            f"Executing list_directory(). Endpoint={endpoint} param_data={params}"
        )

        list_directory_request = self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={"Token": self.__hash_token(endpoint, param_data=params)},
        )
        if list_directory_request.status_code == 401:
            raise PasswordProtectedDirectoryException(
                "This directory is password protected!"
            )

        return list_directory_request.json()

    def authenticate_password(self, account_id, folder_id, password):
        endpoint = "api/v3/folders/password"

        dict_data = '{"AccountId":"ACC_ID","FolderId":"DIR_ID","Password":"PASSWD"}'
        dict_data = dict_data.replace("ACC_ID", str(account_id))
        dict_data = dict_data.replace("DIR_ID", str(folder_id))
        dict_data = dict_data.replace("PASSWD", password)

        logging.debug(
            f"Executing authenticate_password(). Endpoint={endpoint} dict_data={dict_data}"
        )

        unlock_directory_request = self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            json={
                "AccountId": str(account_id),
                "FolderId": str(folder_id),
                "Password": password,
            },
            headers={"Token": self.__hash_token(endpoint, dict_data=dict_data)},
        )

        if unlock_directory_request.status_code == 401:
            raise IncorrectDirectoryPasswordException(folder_id)

    def get_download_url(self, file_id):
        endpoint = "api/v3/files/download"

        params = {"FileId": file_id}

        logging.debug(
            f"Executing get_download_url(). Endpoint={endpoint} param_data={params}"
        )

        get_download_url_request = self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={"Token": self.__hash_token(endpoint, param_data=params)},
        )

        if get_download_url_request.status_code == 404:
            raise FileInPasswordProtectedDirOrNotFoundException(file_id)
        if get_download_url_request.json()["Code"] == 604:
            raise FileIsADirectoryException(file_id)
        if get_download_url_request.json()["Code"] == 605:
            raise NotEnoughTransferException(
                f"User Transfer: {self.transfer}. File ID: {file_id}"
            )

        self.get_account_balance()
        return get_download_url_request.json()["FileUrl"]

    def upload_file(self, file_path=None, folder_id=0):
        endpoint = "api/v3/files/upload/partialUpload"

        dict_data = '{"Name":"FILE_NAME","Size":FILE_SIZE,"FolderId":"FOLDER_ID","Hash":"FILE_HASH"}'

        # Get a CRC32 hash
        with open(file_path, "rb") as f:
            file_hash = hex(zlib.crc32(f.read()) & 0xFFFFFFFF)[2:]

        # Get file size
        file_size = os.path.getsize(file_path)

        # Get the filename of the file
        file_name = os.path.basename(file_path)

        dict_data = dict_data.replace("FILE_NAME", file_name)
        dict_data = dict_data.replace("FILE_SIZE", str(file_size))
        dict_data = dict_data.replace("FOLDER_ID", str(folder_id))
        dict_data = dict_data.replace("FILE_HASH", str(file_hash))

        # Initialize the upload
        # TODO: Fix the token
        # Please help
        # I seriously don't know how to fix it
        upload_file_request = self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            json={
                "FolderId": str(folder_id),
                "Hash": str(file_hash),
                "Name": file_name,
                "Size": file_size,
            },
            headers={"Token": self.__hash_token(endpoint, dict_data=dict_data)},
        )

        upload_url = upload_file_request.json()["Url"]

        self.partial_file_upload(file_name=file_name, upload_url=upload_url)
        print(upload_url)

    def partial_file_upload(self, file_name, upload_url):
        pass  # TODO

    def create_directory(self, folder_name, parent_id):
        endpoint = "api/v3/folders/create"
        dict_data = '{"FolderName":"DIR_NAME","ParentId":"PRNT_ID"}'
        dict_data = dict_data.replace("DIR_NAME", folder_name)
        dict_data = dict_data.replace("PRNT_ID", str(parent_id))

        logging.debug(
            f"Executing create_directory(). Endpoint={endpoint} dict_data={dict_data}"
        )

        create_directory_request = self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            json={"FolderName": folder_name, "ParentId": str(parent_id)},
            headers={"Token": self.__hash_token(endpoint, dict_data=dict_data)},
        )

        if create_directory_request.json()["Code"] == 404:
            raise ParentFolderDoesntExistException(parent_id)

        return create_directory_request.json()["FolderId"]

    def delete_file(self, files=[], folders=[]):
        endpoint = "api/v3/files/delete"
        dict_data = '{"Files":FLS,"Folders":FLDRS}'
        dict_data = dict_data.replace("FLS", str(files).replace(" ", ""))
        dict_data = dict_data.replace("FLDRS", str(folders).replace(" ", ""))

        logging.debug(
            f"Executing delete_file(). Endpoint={endpoint} dict_data={dict_data}"
        )

        delete_file_request = self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            json={"Files": files, "Folders": folders},
            headers={"Token": self.__hash_token(endpoint, dict_data=dict_data)},
        )

        if delete_file_request.json()["Code"] == 400:
            raise CannotDeleteFileException(f"{files} {folders}")

    def query(self, query_field, page=1, media_type="All", extension=None):
        endpoint = "api/v3/files/search"

        query_for_hash = f"{urllib.parse.quote(query_field)}".replace("%20", "+")
        if media_type == "Chomiki":
            params = {"Query": query_field, "PageNumber": str(page)}
            manual_param_data = f"?Query={query_for_hash}&PageNumber={page}"
        elif extension != None:
            params = {
                "Extension": extension,
                "Query": query_field,
                "PageNumber": str(page),
                "MediaType": media_type,
            }
            manual_param_data = f"?Extension={extension}&Query={query_for_hash}&PageNumber={page}&MediaType={media_type}"
        else:
            params = {
                "Query": query_field,
                "PageNumber": str(page),
                "MediaType": media_type,
            }
            manual_param_data = (
                f"?Query={query_for_hash}&PageNumber={page}&MediaType={media_type}"
            )

        logging.debug(
            f"Executing query(). Endpoint={endpoint} query_for_hash={query_for_hash} param_data={params}"
        )

        return self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={
                "Token": self.__hash_token(endpoint, manual_data=manual_param_data)
            },
        ).json()

    def get_friend_list(self, page=1):
        endpoint = "api/v3/friends"
        params = {"PageNumber": page}

        logging.debug(
            f"Executing get_friend_list(). Endpoint={endpoint} param_data={params}"
        )

        return self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={"Token": self.__hash_token(endpoint, param_data=params)},
        ).json()

    def get_copy_list(self, page=1):
        endpoint = "api/v3/files/copies"
        params = {"Page": page}

        logging.debug(
            f"Executing get_copy_list(). Endpoint={endpoint} param_data={params}"
        )

        return self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={"Token": self.__hash_token(endpoint, param_data=params)},
        ).json()

    def get_inbox_messages(self, page=1):
        endpoint = "api/v3/messages/inbox"
        params = {"PageNumber": page}

        logging.debug(
            f"Executing get_inbox_messages(). Endpoint={endpoint} param_data={params}"
        )

        return self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={"Token": self.__hash_token(endpoint, param_data=params)},
        ).json()

    def get_outbox_messages(self, page=1):
        endpoint = "api/v3/messages/outbox"
        params = {"PageNumber": page}

        logging.debug(
            f"Executing get_outbox_messages(). Endpoint={endpoint} param_data={params}"
        )

        return self.req_ses.get(
            f"{self.API_LOCATION}{endpoint}",
            params=params,
            headers={"Token": self.__hash_token(endpoint, param_data=params)},
        ).json()

    def send_message(self, user_id, body, subject):
        # BROKEN AT THE MOMENT!
        endpoint = "api/v3/messages/send"
        dict_data = '{"Subject":"SBJCT","Body":"BDY","AccountTo":"ACC_TO"}'
        dict_data = dict_data.replace("SBJCT", subject)
        dict_data = dict_data.replace("BDY", rf"{body}")
        dict_data = dict_data.replace("ACC_TO", str(user_id))
        dict_data = dict_data.encode("unicode_escape").decode()

        print(dict_data)

        send_message_request = self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            json={"AccountTo": str(user_id), "Body": body, "Subject": subject},
            headers={"Token": self.__hash_token(endpoint, dict_data=dict_data)},
        )
        print(send_message_request.status_code)
        print(send_message_request.text)

    def mark_all_messages_as_read(self):
        endpoint = "api/v3/messages/markAllAsRead"

        logging.debug(f"Executing mark_all_messages_as_read(). Endpoint={endpoint}")

        self.req_ses.post(
            f"{self.API_LOCATION}{endpoint}",
            headers={"Token": self.__hash_token(endpoint)},
        )

    def __hash_token(self, endpoint, param_data=None, dict_data=None, manual_data=None):
        # This function will create a MD5 hash that can be used for Token header in requests
        if param_data != None:
            string_to_hash = (
                f"{endpoint}?{urllib.parse.urlencode(param_data)}{self.SALT}"
            )
        elif dict_data != None:
            # A dictionary must be a string with a proper format
            # Example:
            # dict_data = {"PageNumber":1}
            # type(dict_data) will be str
            string_to_hash = f"{endpoint}{dict_data}{self.SALT}"
        elif manual_data != None:
            string_to_hash = f"{endpoint}{manual_data}{self.SALT}"
        else:
            string_to_hash = f"{endpoint}{self.SALT}"

        logging.debug(f"Hashing token {string_to_hash}.")

        hashed_string = hashlib.md5(string_to_hash.encode("UTF-8")).hexdigest()

        logging.debug(f"Hashed token to {string_to_hash} - {hashed_string}")

        return hashed_string
