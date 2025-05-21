import json
import socket
from datetime import datetime
import regex as re
import mailparser
from dotenv import load_dotenv
import os
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import ipaddress
import validators
import dns.resolver

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
    attachment_names: set = field(default_factory=set)
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
extract_client_ip_regex = re.compile(r'client-ip=(.*)?;')
extract_domain_regex = re.compile(r'\b(?:[a-zA-Z0-9-]{1,63}\.)+(?:[a-zA-Z]{2,63})\b')


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
        print(cc_recipients)
        value.recipients_emails = set(sent_to).union(set(cc_recipients))
    except KeyError:
        value.recipients_emails = set(sent_to)


    # Sender Email, Sender Name
    sender_data = sum(loaded_mail_json["from"], [])
    value.sender_name, value.sender_email = sender_data[0], sender_data[1]

    # Email Message ID
    value.message_id = loaded_mail_json["message-id"].removeprefix('<').removesuffix('>')
    hops = sorted(loaded_mail_json["received"], key= lambda x: x["hop"])
    print(hops)
    print(json.dumps(loaded_mail_json, indent=4))

    # Extract Semder IP from SPF Validation
    try:
        value.sender_ip = extract_client_ip_regex.findall(loaded_mail_json['received-spf'])[0]
        for i in hops:
            if "from" in i and value.sender_ip in i["from"]:
                reciever_ip = extract_client_ip_regex.findall(i["by"])
                reciever_domain = extract_domain_regex.findall(i["by"])
                if len(reciever_ip) > 0:
                    value.recipient_ip = reciever_ip
                    break
                elif len(reciever_domain) > 0:
                    value.recipient_ip = reciever_domain

    except KeyError:
        for i in hops:
            if "from" in i:
                reciever_ip = extract_client_ip_regex.findall(i["from"])

                if len(reciever_ip) > 0:
                    ip = ipaddress.ip_address(reciever_ip[0])
                    if not ip.is_private:
                        value.recipient_ip = reciever_ip[0]
                        reciever_ip = extract_client_ip_regex.findall(i["by"])
                        reciever_domain = extract_domain_regex.findall(i["by"])

                        break

    # for d in recipient_domains:
    #     if "from" in



    # print(parsed.headers_json)
    # print(parsed.headers)
    # print(parsed.attachments)
    # print(parsed.body)
    # print(parsed.date)
    # print(parsed.date_json)
    # print(parsed.defects)
    # print(parsed.defects_categories)
    # print(parsed.headers_json)
    # print(parsed.received_json)

    # print(json.dumps(value, indent=4, default=type_handler))

# print(email_file_mapping)
