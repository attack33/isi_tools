from getpass import getpass
import base64
import os
import sys
import json
import urllib3
import requests
import pandas as pd


def printbanner():
    """This function prints a banner"""
    print(
        """
Welcome to
 _               _                  _ _   _     
| |    ___   ___| | _____ _ __ ___ (_) |_| |__  
| |   / _ \ / __| |/ / __| '_ ` _ \| | __| '_ \ 
| |__| (_) | (__|   <\__ \ | | | | | | |_| | | |
|_____\___/ \___|_|\_\___/_| |_| |_|_|\__|_| |_|\n"""
    )


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
        print("Session to " + uri + " established.")
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


def getiplist(ipinput):
    """This function builds a list of IPs from user input"""
    result = []
    for item in ipinput.split(","):
        if "-" in item:
            start, end = map(lambda x: int(x.split(".")[-1]), item.split("-"))
            start_ip = ".".join(item.split("-")[0].split(".")[:-1])
            result += [start_ip + "." + str(i) for i in range(start, end + 1)]
        else:
            result.append(item)
    return result


def getfileid(api_session, uri, ip, filename):
    """This function gets a list of open files"""
    print("\nGathering related openfiles on " + uri + "...\n")
    opfuri = "/platform/1/protocols/smb/openfiles"
    fileslist = []
    opfinfo = api_session.get(uri + opfuri, verify=False)
    if opfinfo.status_code == 200 or opfinfo.status_code == 201:
        opfinfo = json.loads(opfinfo.content.decode(encoding="UTF-8"))
        for item in opfinfo["openfiles"]:
            if filename in item.get("file"):
                item["node_ip"] = ip
                fileslist.append(item)
    elif opfinfo.status_code != 200 or opfinfo.status_code != 201:
        print(
            "\nIssue encountered with listing openfiles on "
            + uri
            + " Please try again.\n"
        )
        exit()
    return fileslist


def breaklock(closelocksession, uri, fileid, answer):
    """This function breaks a lock by file ID"""
    closeuri = "/platform/1/protocols/smb/openfiles/" + fileid
    response = closelocksession.delete(uri + closeuri, verify=False)
    if response.status_code == 204:
        print("\nThe file associated with ID " + fileid + " has been closed.\n")
        exit()
    elif response.status_code != 204:
        print("\nIssue encountered closing the file. Please try again.\n")
    return None


def main():
    """This function is the main function that runs the Locksmith Tool"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    if len(sys.argv) < 3:
        print("\nargs missing")
        sys.exit(1)
    ip = str(sys.argv[1])
    filename = str(sys.argv[2])
    iplist = input(
        "Please provide a list of IP addresses to check for open files!\n"
        + "Example: 10.x.x.x,10.x.x.x-x (comma separated, no spaces, use"
        + "'-' for a range of IP's):\n"
    )
    iplist = getiplist(iplist)
    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    api_session = getsession(uri)

    listoffiles = []
    for ip in iplist:
        uri = "https://" + str(ip) + ":" + str(port)
        api_session = getsession(uri)
        files = getfileid(api_session, uri, ip, filename)
        if files is not None:
            listoffiles.extend(files)
        elif listoffiles is None:
            break
    print(
        "\nHere is a list of files similar to your filename across the node IPs you provided.\n"
    )
    print("Please take note of the ID you would like to close.\n")
    pd.set_option("display.max_rows", None)
    df = pd.DataFrame(listoffiles)
    print(df)
    fileid = input(
        "\n\nPlease provide the ID of the file you would like to close from the table above: \n"
    )
    answer = str(
        input(
            "\nAre you absolutely sure that ID "
            + fileid
            + " is what you would like to close? Enter 'y' or "
            "'n'...\n"
        )
    )
    if answer == "n":
        print("\nYou have selected no. Please run the script again")
        sys.exit()
    elif answer == "y":
        for index in enumerate(listoffiles):
            if int(listoffiles[index]["id"]) == int(fileid):
                nodeip = str(listoffiles[index]["node_ip"])
                uri = "https://" + str(nodeip) + ":" + str(port)
                closelocksession = getsession(uri)
                breaklock(closelocksession, uri, fileid, answer)
            else:
                continue
        if nodeip is None:
            print("You have input an ID that does not exist. Please try again.")
            sys.exit()
    elif answer != "y" and answer != "n":
        print(
            "\nYou input a character outside of allowed options. Please run the script again.\n"
        )
        sys.exit()


if __name__ == "__main__":
    printbanner()
    main()
