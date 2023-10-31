from getpass import getpass
import argparse
import logging
import base64
import sys
import os
import datetime
import ipaddress
import json
import requests
import urllib3
import pandas as pd


def validateinput(ip, unit, csv):
    """This function checks for valid input"""
    units = ["M", "G", "T"]
    csvlst =["y","n"]
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        print("\nPlease enter a valid IP address!\n")
        sys.exit()

    if unit not in units:
        print(
            "\nPlease enter a valid unit of measurement: M for MB, G for GB, or T for TB\n"
        )
        sys.exit()
    if csv not in csvlst:
        print(
            "\nPlease enter a valid response of 'y' or 'n' to output a csv.\n"
        )
        sys.exit()
    


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


def createquotareport(result, unit, csv):
    """This function creates a quota report with user defined measurement unit"""
    df = pd.json_normalize(result["quotas"])
    if df.empty:
        print("There are no quotas!")
        return 0
    else:
        pd.set_option("display.max_rows", None)
        df = pd.DataFrame(
            df,
            columns=[
                "path",
                "description",
                "usage.fsphysical",
                "usage.fslogical",
                "usage.applogical",
            ],
        )
        if unit == "M":
            df["usage.fsphysical"] = round(((df["usage.fsphysical"]) / 1024 / 1024), 2)
            df["usage.fslogical"] = round(((df["usage.fslogical"]) / 1024 / 1024), 2)
            df["usage.applogical"] = round(((df["usage.applogical"]) / 1024 / 1024), 2)
            df.columns.values[2] = "FSphysical(MB)"
            df.columns.values[3] = "FSlogical(MB)"
            df.columns.values[4] = "APPphysical(MB)"
        elif unit == "G":
            df["usage.fsphysical"] = round(
                ((df["usage.fsphysical"]) / 1024 / 1024 / 1024), 2
            )
            df["usage.fslogical"] = round(
                ((df["usage.fslogical"]) / 1024 / 1024 / 1024), 2
            )
            df["usage.applogical"] = round(
                ((df["usage.applogical"]) / 1024 / 1024 / 1024), 2
            )
            df.columns.values[2] = "FSphysical(GB)"
            df.columns.values[3] = "FSlogical(GB)"
            df.columns.values[4] = "APPphysical(GB)"
        elif unit == "T":
            df["usage.fsphysical"] = round(
                ((df["usage.fsphysical"]) / 1024 / 1024 / 1024 / 1024), 2
            )
            df["usage.fslogical"] = round(
                ((df["usage.fslogical"]) / 1024 / 1024 / 1024 / 1024), 2
            )
            df["usage.applogical"] = round(
                ((df["usage.applogical"]) / 1024 / 1024 / 1024 / 1024), 2
            )
            df.columns.values[2] = "FSphysical(TB)"
            df.columns.values[3] = "FSlogical(TB)"
            df.columns.values[4] = "APPphysical(TB)"

        todaysdate = str(datetime.date.today())
        if csv == "y":
            csvpath = "quota_report_" + todaysdate + ".csv"
            df.to_csv(csvpath, encoding="utf-8", index=False)
            print("\nList of Quotas:\n\n")
            return print(df.to_string(index=False) + "\n")
        elif csv == "n":
            print("\nList of Quotas:\n\n")
            return print(df.to_string(index=False) + "\n")
        else:
            print("You have entered a value for csv that is not 'y' or 'n'. Try again!\n")
        return 0


def getquotareport(api_session, uri, unit, csv):
    """This function gets a quota report and passes it to createquotareport"""
    resourceurl = "/platform/15/quota/quotas"
    result = api_session[0].get(uri + resourceurl, verify=False)
    if result.status_code == 200 or result.status_code == 201:
        result = json.loads(result.content.decode(encoding="UTF-8"))
        logging.info("GET request by " + api_session[1] + " at " + uri + resourceurl + " successful")
        createquotareport(result, unit, csv)
    elif result.status_code != 200 or result.status_code != 201:
        logging.info("GET request  by " + api_session[1] + " at " + uri + resourceurl + " unsuccessful")
        print(
            "\nIssue encountered with retrieving quotas at "
            + uri
            + " Please try again.\n"
        )
        return 0


def main():
    """This function is the main function that runs the isi_quotareport"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    parser = argparse.ArgumentParser(description="Generate a Quota Report")
    parser.add_argument("ip", help="Enter a valid IP address")
    parser.add_argument("unit", help="Enter an M for MB, G for GB, or T for TB")
    parser.add_argument(
        "-o",
        "--outputcsv",
        help="Type 'y' for yes, and 'n' for no to output a csv",
    )
    args = parser.parse_args()
    ip = args.ip
    unit = args.unit

    if args.outputcsv is not None:
        csv = args.outputcsv
    elif args.outputcsv is None:
        csv = 'n'

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="isi_tools.log",
        level=logging.INFO,
    )

    validateinput(ip, unit, csv)


    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    api_session = getsession(uri)
    getquotareport(api_session, uri, unit, csv)


if __name__ == "__main__":
    main()
