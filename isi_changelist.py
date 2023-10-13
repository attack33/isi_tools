from time import sleep
import base64
from getpass import getpass
import os
import ipaddress
import sys
import datetime
import json
import urllib3
import requests
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
  ____ _                            _     _     _   
 / ___| |__   __ _ _ __   __ _  ___| |   (_)___| |_ 
| |   | '_ \ / _` | '_ \ / _` |/ _ \ |   | / __| __|
| |___| | | | (_| | | | | (_| |  __/ |___| \__ \ |_ 
 \____|_| |_|\__,_|_| |_|\__, |\___|_____|_|___/\__|
                         |___/\n"""
    )


def getsession(uri):
    """This function gets a session and sets headers, returns session"""

    creds = "creds.json"
    if os.path.isfile(creds):
        f = open(creds, "r", encoding="utf-8")
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


def displaymenu():
    """This function displays the ChangeList Tool menu options"""
    print("What would you like to do?")
    userinput = input(
        "[1] List Snapshots          [2] Create ChangeList Job\n"
        + "[3] List ChangeLists        [4] Display a ChangeList\n"
        + "[5] Delete a ChangeList "
        + "    [6] Quit Program\n\n"
    )
    return userinput


def getsnapshots(api_session, uri):
    """This function lists all Snapshots,then prompts to write to csv,
    then prints the dataframe"""
    resourceurl = "/platform/1/snapshot/snapshots"
    snapresult = api_session.get(uri + resourceurl, verify=False)
    if snapresult.status_code == 200 or snapresult.status_code == 201:
        snapresult = json.loads(snapresult.content.decode(encoding="UTF-8"))
    elif snapresult.status_code != 200 or snapresult.status_code != 201:
        print(
            "\nIssue encountered with retrieving snapshots at "
            + uri
            + " Please try again.\n"
        )
        return 0
    df = pd.DataFrame(snapresult["snapshots"], columns=["id", "name", "path", "size"])
    if df.empty:
        print("There are no snapshots!")
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


def createchangelist(api_session, uri):
    """This function creates a ChangeList job, provides Job ID
    then queries status and notifies the user of completion"""
    oldsnapid = input("\nWhat is the ID of the older snapshot?  ")
    newsnapid = input("\nWhat is the ID of the newer snapshot?  ")
    oldsnapid = int(oldsnapid)
    newsnapid = int(newsnapid)
    json_str = {
        "type": "changelistcreate",
        "changelistcreate_params": {
            "retain_repstate": 4 == 1,
            "newer_snapid": newsnapid,
            "older_snapid": oldsnapid,
        },
        "priority": 5,
        "policy": "low",
        "allow_dup": 4 == 1,
    }
    resourceurl = "/platform/7/job/jobs"
    result = api_session.post(uri + resourceurl, verify=False, json=json_str).json()
    job_id = str(result.get("id"))
    print("\nJob ID is " + job_id + "\n")
    sent_status = 0
    count = 0
    while sent_status != 1:
        print("\nQuerying status of job ID " + job_id + "\n")
        jobstatusurl = "/platform/7/job/jobs/" + job_id
        result = api_session.get(uri + jobstatusurl, verify=False).json()
        if result["jobs"][0]["state"] == "succeeded":
            sent_status = 1
            print(
                "\nJob " + job_id + " has completed. You can now see this in your"
                "list of ChangeLists using [LC] option.\n"
            )
        else:
            if count == 10:
                print("\nJob " + job_id + " is taking longer than usual.\n")
                print(
                    "\nPlease check job "
                    + job_id
                    + " status manually at "
                    + str(uri)
                    + jobstatusurl
                    + ".\n"
                )
                break
            else:
                print(
                    "\nJob "
                    + job_id
                    + " is still running. Will query again in 10 seconds...\n"
                )
                count += 1
                sleep(10)
    return result


def listchangelists(api_session, uri):
    """This function list all ChangeLists"""
    resourceurl = "/platform/3/snapshot/changelists"
    result = api_session.get(uri + resourceurl, verify=False).json()
    print("List of ChangeLists:\n")
    return print(
        pd.DataFrame(
            result["changelists"], columns=["id", "job_id", "root_path", "num_entries"]
        )
    )


def getchangelist(api_session, uri):
    """This function gets the ChangeList ID the user specifies,
    then prompts to write output to csv, then prints the dataframe."""
    changelistid = input("\nWhat ChangeList would you like to see? [Enter ID]:  ")
    csvinquiry = input(
        "\nWould you also like a csv file of ChangeList ID: "
        + changelistid
        + " output written to "
        + os.getcwd()
        + " ? (y/n): "
    )
    resourceurl = "/platform/10/snapshot/changelists/" + changelistid + "/entries"
    result = api_session.get(uri + resourceurl, verify=False).json()
    entries = result["entries"]
    df = pd.DataFrame(
        entries, columns=["path", "size", "physical_size", "change_types"]
    )
    if csvinquiry == "y":
        csvpath = "changelist_id_" + changelistid + "_results.csv"
        df.to_csv(csvpath, encoding="utf-8", index=False)
        return print(df)
    elif csvinquiry == "n":
        return print(df)
    else:
        print(
            "\nYou have entered a value other than (y) or (n) as a"
            "response to writing csv file. Please try again.\n"
        )
    return


def deletechangelist(api_session, uri):
    """This function deletes a ChangeList ID specified by the user."""
    changelistid = input("What ChangeList ID would you like to delete?\n")
    resourceurl = "/platform/1/snapshot/changelists/" + changelistid
    result = api_session.delete(uri + resourceurl, verify=False)
    if 200 <= result.status_code < 299:
        print("\nChangelist successfully deleted.\n")
    else:
        print("\nOops! Something went wrong. Try again!\n")
        print("\nResult status code is: " + str(result.status_code))
    return result


def main():
    """This function is the main function that runs the Changelist Tool"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    if len(sys.argv) < 2:
        print("\nargs missing")
        sys.exit(1)
    ip = str(sys.argv[1])

    validateinput(ip)

    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    printbanner()

    api_session = getsession(uri)

    sentinel = 0
    while sentinel == 0:
        choice = displaymenu()
        if choice == "1":
            getsnapshots(api_session, uri)
            print("\n\n")
        elif choice == "2":
            createchangelist(api_session, uri)
            print("\n\n")
        elif choice == "3":
            print("\n\n")
            listchangelists(api_session, uri)
            print("\nTake note of the ChangeList ID!\n")
        elif choice == "4":
            getchangelist(api_session, uri)
            print("\n\n")
        elif choice == "5":
            deletechangelist(api_session, uri)
            print("\n\n")
        elif choice == "6":
            sentinel = 1
            break
        elif choice < "1" or choice > "6":
            print("\nERROR: Input is not a valid option. Please re-enter!\n")


if __name__ == "__main__":
    main()
