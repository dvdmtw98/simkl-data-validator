"""
Script to interact with Simkl using their API
Simkl API: https://api.simkl.org/
"""

import os
import time
import requests
from dotenv import load_dotenv


def get_simkl_request_headers():
    """
    Function to set the required headers
    """

    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "simkl-data-validator/1.0"
    }


def get_authentication_pin(client_id):
    """
    Function to request Authentication PIN
    """

    url = "https://api.simkl.com/oauth2/device"

    headers = get_simkl_request_headers()

    data = {
        "client_id": f"{client_id}",
        "scope": "media:read"
    }

    response = requests.post(url, headers=headers, data=data, timeout=10)

    response_data = response.json()

    user_code = response_data["user_code"]
    device_code = response_data["device_code"]
    verification_url = response_data["verification_uri_complete"]
    interval = response_data["interval"]
    expires_in = response_data["expires_in"]

    return user_code, device_code, verification_url, interval, expires_in


def get_access_token(interval, expires_in, device_code, client_id):
    """
    Poll SIMKL API until user authorizes or expires
    """

    url = "https://api.simkl.com/oauth2/token"

    headers = get_simkl_request_headers()

    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": f"{client_id}",
        "device_code": f"{device_code}"
    }

    start_time = time.time()

    while (time.time() - start_time) < expires_in:
        time.sleep(interval)
        response = requests.post(url, headers=headers, data=data, timeout=10)

        response_data = response.json()
        # print(response_data)

        if response.status_code == 200:
            return response_data["access_token"], response_data["refresh_token"]

        error = response_data.get("error")
        if error == "authorization_pending":
            continue

        if error == "slow_down":
            interval += 5
        elif error == "expired_token":
            print("Device code expired, start over.")
        elif error == "invalid_client":
            print("Invalid Client — Fix Registration, do not retry.")

    return None, None


def get_refresh_token(client_id, refresh_token):
    """
    Function to generate refresh token
    """

    url = "https://api.simkl.com/oauth2/token"

    headers = get_simkl_request_headers()

    data = {
        "grant_type": "refresh_token",
        "client_id": f"{client_id}",
        "refresh_token": f"{refresh_token}",
    }

    response = requests.post(url, headers=headers, data=data, timeout=10)
    response.raise_for_status()

    return response.json()


def main():
    """
    Main controller function
    """

    load_dotenv(".env")

    client_id = os.getenv("CLIENT_ID")

    user_code, device_code, verification_url, interval, expires_in = get_authentication_pin(client_id)
    print(f"User Code: {user_code}")
    print(f"Verification URL: {verification_url}")

    access_token, refresh_token = get_access_token(interval, expires_in, device_code, client_id)
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")


if __name__ == '__main__':
    main()
