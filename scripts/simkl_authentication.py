"""
Script to interact with Simkl using their API
Simkl API: https://simkl.docs.apiary.io/
"""

import os
import time
import requests
from dotenv import load_dotenv


def get_authentication_pin(client_id):
    """
    Function to request Authentication PIN
    """

    url = f"https://api.simkl.com/oauth/pin?client_id={client_id}"
    response = requests.get(url, timeout=10)

    response_data = response.json()

    user_code = response_data["user_code"]
    device_code = response_data["device_code"]
    verification_url = response_data["verification_url"]
    interval = response_data["interval"]
    expires_in = response_data["expires_in"]

    return user_code, device_code, verification_url, interval, expires_in


def get_access_token(interval, expires_in, user_code, client_id):
    """
    Poll SIMKL API until user authorizes or expires
    """

    url = f"https://api.simkl.com/oauth/pin/{user_code}?client_id={client_id}"
    start_time = time.time()

    while (time.time() - start_time) < expires_in:
        response = requests.get(url, timeout=10)

        response_data = response.json()
        result = response_data["result"]

        if result == "OK":
            return response_data["access_token"]

        if result == "KO":
            print(response_data["message"])

        time.sleep(interval)

    return None


def main():
    """
    Main controller function
    """

    load_dotenv(".env")

    client_id = os.getenv("CLIENT_ID")

    user_code, _, verification_url, interval, expires_in = get_authentication_pin(client_id)
    print(f"User Code: {user_code}")
    print(f"Verification URL: {verification_url}")

    access_token = get_access_token(interval, expires_in, user_code, client_id)
    print(f"Access Token: {access_token}")


if __name__ == '__main__':
    main()
