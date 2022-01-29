import asyncio
import json
import random
import string

import requests
import websockets

ID_LEN = 29
BASE_URL = "mailinator.com"
MAILINATOR_WSS_URL = f"wss://{BASE_URL}/ws/fetchinbox?zone=public&query=%s"
MAILINATOR_GET_EMAIL_URL = f"https://{BASE_URL}/fetch_email?msgid=%s&zone=public"
MAILINATOR_WEB_URL = f"https://{BASE_URL}/v3/index.jsp?zone=public&query=%s"
TIMEOUT = 2  # seconds


def _generate_random_id():
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(ID_LEN)
    )


class Link:
    """Link."""

    def __init__(self, link: str = "", text: str = ""):
        """Basic html link abstraction.

        :param link: Address of the link.
        :type link: str
        :param text: Text of the <a> tag
        :type text: str
        """
        self.link = self.url = link
        self.text = text

    def __repr__(self):
        return f'<a href="{self.link}">{self.text}</a>'


class Email:
    """Email."""

    def __init__(self, msgid: str, jsessionid: str = None):
        """Email object

        :param msgid: message id that can be obtained from the Inbox object's email_info_list['id']
        :type msgid: str
        :param jsessionid: Optional. Jsessionid cookie.
        :type jsessionid: str
        """
        self.msgid = msgid
        self.jsessionid = jsessionid if jsessionid else _generate_random_id()
        obj = self._fetch_email()["data"]
        self.json = obj
        self.from_address = obj.get("fromfull")
        self.from_name = obj.get("from")
        self.username = self.to = obj.get("to")
        self.time = int(obj.get("time"))
        self.headers = obj.get("headers")
        self.subject = obj.get("subject")
        self.ip = obj.get("ip")
        self.seconds_ago = int(obj.get("seconds_ago"))

        self.links = [Link(**link) for link in obj.get("clickablelinks") or []]
        self.html = None
        self.text = None
        for part in obj.get("parts") or []:
            if "text/html" in part["headers"]["content-type"]:
                self.html = part.get("body")
            if "text/plain" in part["headers"]["content-type"]:
                self.text = part.get("body")

    def _fetch_email(self):
        """Fetches email data from mailinator"""
        request = requests.get(MAILINATOR_GET_EMAIL_URL % self.msgid)
        return request.json()

    async def _remove_message(self):
        """Coroutine to remove email from inbox"""
        remove_msg = {"id": self.msgid, "cmd": "trash", "zone": "public"}
        async with websockets.connect(
            MAILINATOR_WSS_URL % self.username,
            extra_headers={"Cookie": f"JSESSIONID={self.jsessionid}"},
        ) as ws:
            while True:
                try:
                    await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
                except asyncio.TimeoutError:
                    break
            # The message has to be minified
            await ws.send(json.dumps(remove_msg).replace(" ", ""))
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
            except asyncio.TimeoutError:
                return
            try:
                obj = json.loads(msg)
                if obj["channel"] in ["error", "status"]:
                    return obj
            except json.JSONDecodeError:
                return

    def remove(self) -> (bool, str):
        """Removes email from inbox

        :return: True if successful, False if not and message
        :rtype: (bool, str)
        """
        response = asyncio.run(self._remove_message())
        if response is None:
            msg = "Failed to remove email"
        else:
            msg = response.get("msg") or "Failed to remove email"
        return ("message deleted" in msg, msg)


class PublicInbox:
    """Creates a new public mailbox instance and fetch its emails"""

    def __init__(self, username: str, message_fetch_timeout: float = TIMEOUT):
        """Creates a new public mailbox instance and fetch its emails

        :param username: The username of the public mailbox
        :type username: str
        :param message_fetch_timeout:
        :type message_fetch_timeout: The timeout for fetching individual messages. You may want to increase this if you have a slow internet connection. If you call this too many times and have a good connection you can try to decrease this. Defaults to 2 seconds
        """
        self.username = username
        self.address = f"{username}@{BASE_URL}"
        self.web_url = MAILINATOR_WEB_URL % self.username
        self.jsessionid = f"node01{_generate_random_id()}.node0"
        self.email_info_list = []
        self.fetch_emails()

    async def _get_messages(self):
        """Coroutine that fetches the messages from the public mailbox using the websockets stream"""
        received = []
        async with websockets.connect(
            MAILINATOR_WSS_URL % self.username,
            extra_headers={"Cookie": f"JSESSIONID={self.jsessionid}"},
        ) as ws:
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
                except asyncio.TimeoutError:
                    break
                try:
                    obj = json.loads(msg)
                    if "fromfull" in obj:
                        received.append(obj)
                except json.JSONDecodeError:
                    continue
        return received

    def fetch_emails(self) -> list:
        """Updates and Populates the email_info_list attribute with a list of the emails from the public mailbox

        :return: A list of the emails information dicts from the public mailbox. These do not contain the actual body of the emails.
        :rtype: list
        """
        self.email_info_list = asyncio.run(self._get_messages())
        return self.email_info_list

    def __iter__(self):
        """Iterates over the emails in the public mailbox"""
        for email in self.email_info_list:
            yield Email(email["id"], self.jsessionid)

    def get_lastest_email(self) -> Email:
        """Returns the last email in the public mailbox

        :return: The last email in the public mailbox
        :rtype: Email
        """
        if self.email_info_list:
            # TODO: This is a bit of a hack. We should probably just fetch the emails and sort them by time
            # but it works
            return Email(self.email_info_list[-1]["id"], self.jsessionid)
