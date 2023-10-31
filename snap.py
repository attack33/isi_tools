from getpass import getpass
import argparse
import logging
import sys
import base64
import os
import datetime
import ipaddress
import json
import requests
import urllib3


def validateinput(ip):
    """This function checks for valid input"""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        print("\nPlease enter a valid IP address!\n")
        sys.exit()


def datetoepoch(timestamp):
    """This function converts a datetime, checks validity, then returns epoch time"""
    if timestamp:
        year, month, day, hour, minute, second = map(int, timestamp.split("-"))
        expirydate = int(
            datetime.datetime(year, month, day, hour, minute, second).timestamp()
        )
        currentdate = int(datetime.datetime.now().timestamp())
    else:
        return 0
    if expirydate < currentdate:
        print("\nDate entered must be greater than current date!\n")
        sys.exit()
    else:
        return expirydate


def getsession(uri):
    """This function gets a session and sets headers, returns session"""
    creds = "creds.json"
    if os.path.isfile(creds):
        with open(creds, "r", encoding="utf-8") as f:
            data = json.load(f)
            user = data["username"]
            p = base64.b64decode(data["password"]).decode("utf-8")
    elif os.path.isfile(creds) is False:
        user = input("Please provide your user name? \n")
        print("\nPlease provide the password for your user account...\n")
        p = getpass()

    print("\n\nAttempting session to " + uri + " ...\n")
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"username": user, "password": p, "services": ["platform"]})
    api_session = requests.Session()
    response = api_session.post(
        uri + "/session/1/session", data=data, headers=headers, verify=False
    )
    if response.status_code == 200 or response.status_code == 201:
        print("Session to " + uri + " established.\n")
        logging.info("API session created successfully by " + user + " at " + uri)
    elif response.status_code != 200 or response.status_code != 201:
        print(
            "\nSession to "
            + uri
            + " not established. Please check your password, user name, or IP and try again.\n"
        )
        logging.info("Creation of API session by " + user + " at " + uri + " unsuccessful")
        sys.exit()
    api_session.headers["referer"] = uri
    api_session.headers["X-CSRF-Token"] = api_session.cookies.get("isicsrf")
    return api_session, user

def createsnapshot(api_session, uri, path, name, snapexpires):
    """This function will create a snapshot on path/expiration provided"""
    resourceurl = "/platform/1/snapshot/snapshots"
    if name == 0 and snapexpires == 0:
        data = json.dumps({"path": path})
    elif snapexpires == 0 and name != 0:
        data = json.dumps({"path": path, "name": name})
    elif snapexpires != 0 and name == 0:
        data = json.dumps({"path": path, "snapexpires": snapexpires})
    else:
        data = json.dumps({"path": path, "expires": snapexpires, "name": name})
    response = api_session[0].post(uri + resourceurl, data=data, verify=False)
    if response.status_code == 200 or response.status_code == 201:
        logging.info("POST request by " + api_session[1] + " at "  + uri + resourceurl + " successful")
        response = json.loads(response.content.decode(encoding="UTF-8"))
        snapid = response["id"]
        print(
                    "\nSnapshot ID " + str(snapid) + " created!\n"
                )
        return snapid
    elif response.status_code != 200 or response.status_code != 201:
        logging.info("POST request by " + api_session[1] + " at "  + uri + resourceurl + " unsuccessful")
        print("\nSnapshot creation encountered an issue. Try again!")
        sys.exit()

def main():
    """This function is the main function that runs the snapandlock"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    parser = argparse.ArgumentParser(description="Lock a list of snapshots")
    parser.add_argument("ip", help="Enter a valid IP address")
    parser.add_argument(
        "path",
        help="Enter a path to take a snapshot "
        + "Example: /ifs/data/path",
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Type a custom name for the snapshot.",
    )
    parser.add_argument(
        "-sx",
        "--snapexpires",
        help="Type a date in YYYY-MM-DD-HH-MM-SS format (24h) to expire snapshot",
    )

    args = parser.parse_args()

    ip = args.ip
    path = args.path


    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="isi_tools.log",
        level=logging.INFO,
    )

    validateinput(ip)

    if args.snapexpires is not None:
        snapexpires = datetoepoch(args.snapexpires)
    elif args.snapexpires is None:
        snapexpires = 0

    if args.name is not None:
        name = args.name
    elif args.name is None:
        name= 0

    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    api_session = getsession(uri)

    createsnapshot(api_session, uri, path, name, snapexpires)


if __name__ == "__main__":
    main()
