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
import pandas as pd


def validateinput(ip):
    """This function checks for valid input"""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        print("\nPlease enter a valid IP address!\n")
        sys.exit()


def printbanner():
    """This function prints a banner"""
    print(
        """
Welcome to
 ____                    _            _    
/ ___| _ __   __ _ _ __ | | ___   ___| | __
\___ \| '_ \ / _` | '_ \| |/ _ \ / __| |/ /
 ___) | | | | (_| | |_) | | (_) | (__|   < 
|____/|_| |_|\__,_| .__/|_|\___/ \___|_|\_\\
                  |_|\n"""
    )


def datetoepoch():
    """This function converts a datetime, checks validity, then returns epoch time"""
    date_entry = input(
        "\nType a date in YYYY-MM-DD-HH-MM-SS format (24h) or "
        + "leave blank for the lock to never expire and hit <enter>: \n"
    )
    if date_entry:
        year, month, day, hour, minute, second = map(int, date_entry.split("-"))
        expirydate = int(
            datetime.datetime(year, month, day, hour, minute, second).timestamp()
        )
        currentdate = int(datetime.datetime.now().timestamp())
    else:
        return 0
    if expirydate < currentdate:
        print("\nDate entered must be greater than current date!\n")
        datetoepoch()
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
        logging.info("API session created successfully at " + uri)
        print("Session to " + uri + " established.\n")
    elif response.status_code != 200 or response.status_code != 201:
        logging.info("Creation of API session  at " + uri + " unsuccessful")
        print(
            "\nSession to "
            + uri
            + " not established. Please check your password, user name, or IP and try again.\n"
        )
        sys.exit()
    api_session.headers["referer"] = uri
    api_session.headers["X-CSRF-Token"] = api_session.cookies.get("isicsrf")
    return api_session


def getsnapshots(api_session, uri):
    """This function lists all Snapshots,then prompts to write to csv,
    then prints the dataframe"""
    resourceurl = "/platform/1/snapshot/snapshots"
    snapresult = api_session.get(uri + resourceurl, verify=False)
    if snapresult.status_code == 200 or snapresult.status_code == 201:
        logging.info("GET request at " + uri + resourceurl + " successful")
        snapresult = json.loads(snapresult.content.decode(encoding="UTF-8"))
    elif snapresult.status_code != 200 or snapresult.status_code != 201:
        logging.info("GET request at " + uri + resourceurl + " unsuccessful")
        print(
            "\nIssue encountered with retrieving snapshots at "
            + uri
            + " Please try again.\n"
        )
        return 0
    df = pd.DataFrame(
        snapresult["snapshots"], columns=["id", "name", "path", "size", "has_locks"]
    )
    if df.empty:
        print("\nThere are no snapshots!")
        return 0
    else:
        csvinquiry = input(
            "\nWould you also like a csv file of snapshots written to "
            + os.getcwd()
            + " ? (y/n):  "
        )
        todaysdate = str(datetime.date.today())
        if csvinquiry == "y":
            csvpath = "snapshot_list_results_" + todaysdate + ".csv"
            df.to_csv(csvpath, encoding="utf-8", index=False)
            print("\n\nList of Snapshots:")
            return print(df.to_string(index=False))
        elif csvinquiry == "n":
            print("\n\nList of Snapshots:")
            return print(df.to_string(index=False))
        else:
            print(
                "\nYou have entered a value other than (y) or (n) as a"
                "response to writing csv file. Please try again.\n"
            )
        return 0


def locksnapshot(api_session, uri):
    """This function will lock a snapshot"""
    print("\nBe advised, a single snapshot can only have a maximum of 16 locks.\n")
    snapid = input("\nWhat is the ID of the snapshot you would like to lock?\n")
    epoch = datetoepoch()
    resourceurl = "/platform/12/snapshot/snapshots/" + snapid + "/locks"
    lockcount = api_session.get(uri + resourceurl, verify=False)
    if lockcount.status_code == 200 or lockcount.status_code == 201:
        logging.info("GET request at " + uri + resourceurl + " successful")
        lockcount = json.loads(lockcount.content.decode(encoding="UTF-8"))
    elif lockcount.status_code != 200 or lockcount.status_code != 201:
        logging.info("GET request at " + uri + resourceurl + " unsuccessful")
        print(
            "\nIssue encountered with retrieving the # of locks currently on Snapshot ID: "
            + snapid
            + " Please try again.\n"
        )
        displaymenu()
    lockcount = lockcount["total"]
    print(
        "\nThere are currently "
        + str(lockcount)
        + " locks on Snapshot ID: "
        + snapid
        + ".\n"
    )
    if lockcount < 16:
        print(
            "\nYou can create "
            + str(16 - lockcount)
            + " more locks on the provided snapshot ID.\n"
        )
        print("\nProceeding with creation of snapshot lock...\n")
        if epoch == 0:
            noxdata = json.dumps({"comment": "This lock was created by isi_snaplock."})
            response = api_session.post(uri + resourceurl, data=noxdata, verify=False)
            if response.status_code == 200 or response.status_code == 201:
                logging.info("POST request at " + uri + resourceurl + " successful")
                response = json.loads(response.content.decode(encoding="UTF-8"))
                lockid = response["id"]
                print("\nLock ID " + str(lockid) + " created.")
            elif response.status_code != 200 or response.status_code != 201:
                logging.info("POST request at " + uri + resourceurl + " unsuccessful")
                print("\nLock creation encountered an issue. Try again!")
        elif epoch != 0:
            xdata = json.dumps(
                {"comment": "This lock was created by isi_snaplock.", "expires": epoch}
            )
            response = api_session.post(uri + resourceurl, data=xdata, verify=False)
            if response.status_code == 200 or response.status_code == 201:
                logging.info("POST request at " + uri + resourceurl + " successful")
                response = json.loads(response.content.decode(encoding="UTF-8"))
                lockid = response["id"]
                print("\nLock ID " + str(lockid) + " created.\n")
            elif response.status_code != 200 or response.status_code != 201:
                logging.info("POST request at " + uri + resourceurl + " unsuccessful")
                print("\nLock creation encountered an issue. Try again!")
    elif lockcount >= 16:
        print(
            "\nSnapshot ID: "
            + snapid
            + " has reached the maximum # of allowed locks.\n"
        )
        displaymenu()


def listlocks(api_session, uri):
    """This function will list all locks for a snapshot"""
    snapid = input(
        "\nWhat is the ID of the snapshot that you want to list all locks?\n"
    )
    resourceurl = "/platform/12/snapshot/snapshots/" + snapid + "/locks"
    locklist = api_session.get(uri + resourceurl, verify=False)
    if locklist.status_code == 200 or locklist.status_code == 201:
        logging.info("GET request at " + uri + resourceurl + " successful")
        locklist = json.loads(locklist.content.decode(encoding="UTF-8"))
    elif locklist.status_code != 200 or locklist.status_code != 201:
        logging.info("GET request at " + uri + resourceurl + " unsuccessful")
        print(
            "\nIssue encountered with retrieving the list of locks currently on Snapshot ID: "
            + snapid
            + " Please try again.\n"
        )
        displaymenu()
    df = pd.DataFrame(locklist["locks"], columns=["id", "expires", "comment", "count"])
    if df.empty:
        print("\nThere are no locks for Snapshot ID " + str(snapid) + "!\n")
    else:
        df["expires"] = pd.to_datetime(df["expires"], unit="s")
        df.columns.values[1] = "expires(GMT)"
        print("\n\nList of Locks for Snapshot ID " + str(snapid) + ": \n")
        print(df.to_string(index=False))
        print("\n\nTake note of the Lock ID!")


def delete1lock(api_session, uri):
    """This function will delete a snapshot lock"""
    snapid = input("\nWhat is the ID of the snapshot that you want to delete a lock?\n")
    lockid = input(
        "\nWhat is the ID of the lock you want to delete for Snapshot ID "
        + str(snapid)
        + "?\n"
    )
    resourceurl = "/platform/12/snapshot/snapshots/" + snapid + "/locks/" + lockid
    response = api_session.delete(uri + resourceurl, verify=False)
    if response.status_code == 200 or response.status_code == 204:
        logging.info("DELETE request at " + uri + resourceurl + " successful")
        print("\nLock ID " + str(lockid) + " deleted.")
    elif response.status_code != 200 or response.status_code != 204:
        logging.info("DELETE request at " + uri + resourceurl + " unsuccessful")
        print("\nLock deletion encountered an issue. Try again!\n")


def deletealllocks(api_session, uri):
    """This function will delete all locks for a snapshot"""
    snapid = input(
        "\nWhat is the ID of the snapshot that you want to delete ALL locks?\n"
    )
    resourceurl = "/platform/12/snapshot/snapshots/" + snapid + "/locks"
    response = api_session.delete(uri + resourceurl, verify=False)
    if response.status_code == 200 or response.status_code == 204:
        logging.info("DELETE request at " + uri + resourceurl + " successful")
        print("\nAll locks deleted for Snapshot ID " + str(snapid))
    elif response.status_code != 200 or response.status_code != 204:
        logging.info("DELETE request at " + uri + resourceurl + " unsuccessful")
        print("\nLock deletion encountered an issue. Try again!\n")


def displaymenu():
    """This function displays the ChangeList Tool menu options"""
    print("\nWhat would you like to do? (Type a number, hit <Enter>)")
    userinput = input(
        "[1] List ALL Snapshots                      [2] Lock a Snapshot\n"
        "[3] List Locks for a Snapshot               [4] Delete a Snapshot Lock\n"
        "[5] Delete ALL Locks from a Snapshot        [6] Quit Snaplock\n"
    )
    return userinput


def main():
    """This function is the main function that runs the isi_snaplock"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    parser = argparse.ArgumentParser(description="Menu driven snaplock tool")
    parser.add_argument("ip", help="Enter a valid IP address")
    args = parser.parse_args()
    ip = args.ip

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="isi_tools.log",
        level=logging.INFO,
    )

    validateinput(ip)
    printbanner()

    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    api_session = getsession(uri)

    sentinel = 0
    while sentinel == 0:
        choice = displaymenu()
        if choice == "1":
            getsnapshots(api_session, uri)
            print("\n\n")
        elif choice == "2":
            locksnapshot(api_session, uri)
            print("\n\n")
        elif choice == "3":
            listlocks(api_session, uri)
            print("\n\n")
        elif choice == "4":
            delete1lock(api_session, uri)
            print("\n\n")
        elif choice == "5":
            deletealllocks(api_session, uri)
            print("\n\n")
        elif choice == "6":
            sentinel = 1
            break
        elif choice < "1" or choice > "6":
            print("\nERROR: Input is not a valid option. Please re-enter!\n")


if __name__ == "__main__":
    main()
