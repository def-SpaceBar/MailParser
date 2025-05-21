Please configure the env file accordingly.

at the first execution, 'setup_mapping' should be equal to 'true' (not case sensitive)
The script will iterate over the configure emails folder files, currently supports .eml files.

after data extraction from all emails, the data will be sent over to elasticsearch.

Parsed Email Example:
```json
{
    "subject": "test mail of different attachments",
    "message_id": "SJ2PR19MB7344DCAE7016782C6D7B4505F89EA@SJ2PR19MB7344.namprd19.prod.outlook.com",
    "sender_email": "spacebar.post@gmail.com",
    "sender_ip": "2603:1036:307:540d::5",
    "sender_name": "bar revah",
    "recipients_emails": [
        "test@example.com"
    ],
    "recipient_ip": "smtp.gmail.com" , # If IP not found, gets the domain
    "attachments": [
        {
            "file_name": "Shared2.kdbx",
            "file_size": 12859,
            "hashs": {
                "md5": "77d4d6453582722ca70fc23f7e311d2e",
                "sha1": "86d912b082f82bac5aee110b44f2e6ab53f5cbdf",
                "sha256": "c60cd253626c02d74552d31bc913431ab1631b13015ce3b20f19912a89d54cf7"
                # Obtained file hashs without downloading the actual file to disk.
            }
        },
        {
            "file_name": "Binance.lnk",
            "file_size": 2100,
            "hashs": {
                "md5": "d00ffc1987e222b6b23f021b9ce75c50",
                "sha1": "3c837ed42d11e768e6128a35df692305990a976e",
                "sha256": "a2266938d8624bef43c5dfca0b370c9b788b42da1c80c945baa590c33847ab17"
            }
        },
        {
            "file_name": "headers.json",
            "file_size": 7026,
            "hashs": {
                "md5": "e06b3f4b1497c9f09884e738bf073fca",
                "sha1": "c0a0da8e8c9c90d750883eb4adad968a7ad5b653",
                "sha256": "714e035edb8271732a9c165cff2eed760488e4e3471df2e2699ace2360040d50"
            }
        },
        {
            "file_name": "slack.exe",
            "file_size": 307696,
            "hashs": {
                "md5": "5460128374e368df8363e05d1adff51c",
                "sha1": "e761e5998e73cafeb0e7a35b09fd0e5cb3fbeb63",
                "sha256": "e8ed6a316ce311ff205d9561c59b3f98ab2870ebaebe0518a2e8103e835e881e"
            }
        }
    ],
    "links": [], # Will remain empty unless <a> tags exists in the email body. --> unique links
    "domains": [] # unique domains from the links array
}
```
