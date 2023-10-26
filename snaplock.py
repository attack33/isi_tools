from getpass import getpass
import argparse
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
    elif response.status_code != 200 or response.status_code != 201:
        print(
            "\nSession to "
            + uri
            + " not established. Please check your password, user name, or IP and try again.\n"
        )
        sys.exit()
    api_session.headers["referer"] = uri
    api_session.headers["X-CSRF-Token"] = api_session.cookies.get("isicsrf")
    return api_session


def locksnapshot(api_session, uri, snapid, timestamp):
    """This function will lock a snapshot or list of snapshots"""
    print("\nBe advised, a single snapshot can only have a maximum of 16 locks.\n")
    for snap in snapid:
        resourceurl = "/platform/12/snapshot/snapshots/" + snap + "/locks"
        print("\nProceeding with creation of snapshot lock...\n")
        if timestamp == 0:
            noxdata = json.dumps({"comment": "This lock was created by isi_snaplock."})
            response = api_session.post(uri + resourceurl, data=noxdata, verify=False)
            if response.status_code == 200 or response.status_code == 201:
                response = json.loads(response.content.decode(encoding="UTF-8"))
                lockid = response["id"]
                print("\nLock ID " + str(lockid) + " created.")
            elif response.status_code != 200 or response.status_code != 201:
                print("\nLock creation encountered an issue. Try again!")
        elif timestamp != 0:
            xdata = json.dumps(
                {
                    "comment": "This lock was created by snaplock.",
                    "expires": timestamp,
                }
            )
            response = api_session.post(uri + resourceurl, data=xdata, verify=False)
            if response.status_code == 200 or response.status_code == 201:
                response = json.loads(response.content.decode(encoding="UTF-8"))
                lockid = response["id"]
                print(
                    "\nLock ID " + str(lockid) + " created on snap ID " + snap + "!\n"
                )
            elif response.status_code != 200 or response.status_code != 201:
                print(
                    "\nLock creation encountered an issue on snap ID "
                    + snap
                    + ". Try again!"
                )
    return 0


def main():
    """This function is the main function that runs the snaplock"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    parser = argparse.ArgumentParser(description="Lock a list of snapshots")
    parser.add_argument("ip", help="Enter a valid IP address")
    parser.add_argument(
        "snapid",
        help="Enter a Snap ID or list of Snap IDs to lock "
        + "in the following format: <snap ID>,<snap ID> (comma separated, no spaces)",
    )
    parser.add_argument(
        "-t",
        "--timestamp",
        help="Type a date in YYYY-MM-DD-HH-MM-SS format (24h) to set lock operation",
    )
    args = parser.parse_args()

    ip = args.ip
    snapid = args.snapid
    validateinput(ip)
    snapid = snapid.split(",")
    if args.timestamp is not None:
        timestamp = datetoepoch(args.timestamp)
    elif args.timestamp is None:
        timestamp = 0

    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    api_session = getsession(uri)
    locksnapshot(api_session, uri, snapid, timestamp)


if __name__ == "__main__":
    main()
