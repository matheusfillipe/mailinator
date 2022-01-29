# Mailinator Public API

Python wrapper for mailinator's public api. This library scrapes mailinator's websockets api and gives an abstraction layer for basic operations such as viewing the inbox, email's content and removing them.

This means that this will allow you to to view and remove emails from public inboxes of https://www.mailinator.com without the need of a headless browser. Notice there is a limit for removing emails.


## Usage

I hope it is simple enough.
```python
from mailinatorapi import PublicInbox
inbox = PublicInbox("carlos")
print(inbox.web_url)
# Iterate over the emails and print some info
for email in inbox:
    print(email.from_address)
    print(email.from_name)
    print(email.subject)
    print(email.seconds_ago)
    print(email.text)
    print(email.html)
    print([f"{link.text}: {link.url}" for link in email.links])

# remove the last email
email = inbox.get_lastest_email()
print(email.from_address)
ok, msg = email.remove()
if ok:
    print("Removal successful! ", msg)
else:
    print("Removal failed! ", msg)

```

You can access the raw json response for the email object with `email.json`.
