import email
import mailparser
from dotenv import load_dotenv
import os
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class ParseObject:
    subject: str = ""
    sender_email: str = ""
    sender_smtp_ip: str = ""
    sender_name: str = ""
    recipient_email: str = ""
    recipient_smtp_ip: str = ""
    recipient_name: str = ""
    attachment_names: set = field(default_factory=set)
    links: set = field(default_factory=set)
    domains: set = field(default_factory=set)


env_vars = load_dotenv('mailparser_config.env')
email_file_mapping = defaultdict(ParseObject)

try:
    _eml_folder_path = os.environ["eml_folder"]
    # _msg_folder_path = os.environ["msg_folder"]
except KeyError as wrong_key:
    print(f"Error occured while reading environment variables.\n According to the error, you've passed an invalid environment variable key. {wrong_key}")
    exit(1)

pathlib_eml = Path(_eml_folder_path)
for eml in pathlib_eml.iterdir():
    if eml.suffix == '.eml':
        # noinspection PyStatementEffect
        email_file_mapping[eml.joinpath()]

print(email_file_mapping)
test =
for email in email_file_mapping.keys():
    text = email.read_text()
    parsed = mailparser.parse_from_string(text)
    # print(parsed.message)
    # print(parsed.mail)
    # print(parsed.headers)
    # print(parsed.attachments)
    # print(parsed.body)
    # print(parsed.date)
    # print(parsed.date_json)
    # print(parsed.defects)
    # print(parsed.defects_categories)
    # print(parsed.headers_json)
    # print()
    # print()
