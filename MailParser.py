import json
from datetime import datetime
from lxml import html
import regex as re
import mailparser
from dotenv import load_dotenv
import os
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import ipaddress
import base64
import hashlib

# MailDict = lambda:{
#     "subject": "",
#     "sender_email": "",
#     "sender_smtp_ip": "",
#     "sender_name": "",
#     "recipient_email": "",
#     "recipient_smtp_ip": "",
#     "recipient_name": "",
#     "attachment_names": set(),
#     "links": set()
# }
@dataclass
class ParseObject:
    subject: str = ""
    message_id: str = ""
    sender_email: str = ""
    sender_ip: str = ""
    sender_name: str = ""
    recipients_emails: set = field(default_factory=set)
    recipient_ip: str = ""
    attachments: list[dict] = field(default_factory=list[dict])
    links: set = field(default_factory=set)
    domains: set = field(default_factory=set)


ipv4_or_ipv6_regex = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|'
                                r'\b(?:'
                                r'(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}|'
                                r'(?:[A-Fa-f0-9]{1,4}:){1,7}:|'
                                r'(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}|'
                                r'(?:[A-Fa-f0-9]{1,4}:){1,5}(?::[A-Fa-f0-9]{1,4}){1,2}|'
                                r'(?:[A-Fa-f0-9]{1,4}:){1,4}(?::[A-Fa-f0-9]{1,4}){1,3}|'
                                r'(?:[A-Fa-f0-9]{1,4}:){1,3}(?::[A-Fa-f0-9]{1,4}){1,4}|'
                                r'(?:[A-Fa-f0-9]{1,4}:){1,2}(?::[A-Fa-f0-9]{1,4}){1,5}|'
                                r'[A-Fa-f0-9]{1,4}:(?:(?::[A-Fa-f0-9]{1,4}){1,6})|'
                                r':(?:(?::[A-Fa-f0-9]{1,4}){1,7}|:)'
                                r')\b'
                                )
# ipv4_or_ipv6_regex = re.compile(r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}')
extract_client_ip_regex = re.compile(r'client-ip=(.*)?;')
extract_domain_regex = re.compile(r'\b(?:[a-zA-Z0-9-]{1,63}\.)+(?:[a-zA-Z]{2,63})\b')
file_size_regex = re.compile(r'size=(.*)?;')


def type_handler(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)


env_vars = load_dotenv('mailparser_config.env')
email_file_mapping = defaultdict(ParseObject)

try:
    _eml_folder_path = os.environ["eml_folder"]
    # _msg_folder_path = os.environ["msg_folder"]
except KeyError as wrong_key:
    print(
        f"Error occured while reading environment variables.\n According to the error, you've passed an invalid environment variable key. {wrong_key}")
    exit(1)

pathlib_eml = Path(_eml_folder_path)
for eml in pathlib_eml.iterdir():
    if eml.suffix == '.eml':
        # noinspection PyStatementEffect
        email_file_mapping[eml.joinpath()]

for email, value in email_file_mapping.items():
    text = email.read_text()
    parsed = mailparser.parse_from_string(text)
    loaded_mail_json = json.loads(parsed.mail_json)

    # Mail Subject
    value.subject = loaded_mail_json["subject"]

    # recipients
    sent_to = [x for x in sum(loaded_mail_json["to"], []) if x != '']

    try:
        cc_recipients = [x for x in sum(loaded_mail_json["cc"], []) if x != ""]
        value.recipients_emails = set(sent_to).union(set(cc_recipients))
    except KeyError:
        value.recipients_emails = set(sent_to)

    # Sender Email, Sender Name
    sender_data = sum(loaded_mail_json["from"], [])
    value.sender_name, value.sender_email = sender_data[0], sender_data[1]

    # Email Message ID
    value.message_id = loaded_mail_json["message-id"].removeprefix('<').removesuffix('>')

    # Extract Semder IP from SPF Validation
    # Sort hops by hop number for efficient iteration.
    hops = sorted(loaded_mail_json["received"], key=lambda x: x["hop"])
    try:
        value.sender_ip = extract_client_ip_regex.findall(loaded_mail_json['received-spf'])[0]
        for i in hops:
            if "from" in i and value.sender_ip in i["from"]:
                reciever_ip = extract_client_ip_regex.findall(i["by"])
                reciever_domain = extract_domain_regex.findall(i["by"])
                value.recipient_ip = reciever_ip[0] if len(reciever_ip) != 0 else reciever_domain[0]
                # if len(reciever_ip) > 0:
                #     value.recipient_ip = reciever_ip[0]
                #     break
                # elif len(reciever_domain) > 0:
                #     value.recipient_ip = reciever_domain

    except KeyError:
        for i in hops:
            if "from" in i:
                sender_ip = ipv4_or_ipv6_regex.findall(i["from"])
                if len(sender_ip) > 0:
                    ip = ipaddress.ip_address(sender_ip[0])
                    if ip.is_global is True:
                        value.sender_ip = sender_ip[0]
                        reciever_ip = extract_client_ip_regex.findall(i["by"])
                        reciever_domain = extract_domain_regex.findall(i["by"])
                        value.recipient_ip = reciever_ip[0] if len(reciever_ip) != 0 else reciever_domain[0]
                        break

    # Get links from email body by parsing the html
    html_string = "".join(parsed.text_html)
    tree = html.fromstring(html_string)
    links = set(tree.xpath("//a/@href"))
    links = [x for x in links if x != ""]
    value.links = links

    # Extract linked-to domains
    link_domain_match = [extract_domain_regex.findall(link) for link in links]
    value.domains = set([x[0] for x in link_domain_match if len(x) > 0 or x != ""])

    # Handle Attachments & Extract HASH with the file base64 without downloading it or creating it on disk.
    if len(parsed.attachments) != 0:
        for attachment in parsed.attachments:
            match attachment["content_transfer_encoding"]:
                case "base64":
                    payload_as_bytes = base64.b64decode(attachment["payload"])
                case _:
                    pass
            value.attachments.append({
                "file_name": attachment["filename"],
                "file_size": file_size_regex.findall(attachment["content-disposition"])[0],
                "hashs": {
                    "md5": hashlib.md5(payload_as_bytes).hexdigest(),
                    "sha1": hashlib.sha1(payload_as_bytes).hexdigest(),
                    "sha256": hashlib.sha256(payload_as_bytes).hexdigest()
                }
            })

    #
    # output = json.dumps(asdict(value), default=type_handler, indent=4)
    # print(output)


# print(email_file_mapping)
