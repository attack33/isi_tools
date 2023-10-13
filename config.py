from getpass import getpass
import base64
import sys
import json
import ipaddress
import requests
import urllib3


def printbanner():
    """This function prints a banner"""
    print(
        """
Welcome to
  ____             __ _       
 / ___|___  _ __  / _(_) __ _ 
| |   / _ \| '_ \| |_| |/ _` |
| |__| (_) | | | |  _| | (_| |
 \____\___/|_| |_|_| |_|\__, |
                        |___/\n"""
    )


def getsession(user, p, uri):
    """This function gets a session and sets headers, returns session"""
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


def validateinput(ip):
    """This function checks for valid input"""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        print("\nPlease enter a valid IP address!\n")
        sys.exit()


def configureenvironment():
    """This function configures environment credentials and address info
    for the cluster."""

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    printbanner()

    # Get Creds
    user = input("Please provide your user name? \n")
    print("\nPlease provide the password for your user account...\n")
    p = getpass()
    ip = input("\nPlease provide a node IP or DNS name:  ")

    validateinput(ip)

    port = 8080
    uri = "https://" + str(ip) + ":" + str(port)

    # Data to be written to file
    dictionary = {
        "username": user,
        "password": base64.b64encode(p.encode("utf-8")).decode("utf-8"),
    }

    # Serializing json
    json_object = json.dumps(dictionary, indent=4)

    # Writing json to creds.json
    with open("creds.json", "w", encoding="UTF-8") as f:
        f.write(json_object)
    f.close()

    print("\nValidating credentials against provided address...")
    api_session = getsession(user, p, uri)
    if api_session.cookies:
        print("\nEnvironment configured w/ valid credentials. Enjoy!\n")
        sys.exit()
    else:
        print("\nError encountered. Please check credentials.\n")
    sys.exit()


def main():
    """This is the main function that runs configureenvironment()"""
    configureenvironment()


if __name__ == "__main__":
    main()
