"""
Script to check if any item has been removed from Simkl
"""

import sys
import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

API_URL = "https://api.simkl.com"


def set_github_env(key, value):
    """Set Environment Variable in GitHub Action"""

    env_file = os.getenv("GITHUB_ENV")

    if not env_file:
        return

    with open(env_file, "a", encoding="utf-8") as virtual_file:
        virtual_file.write(f"{key}={value}\n")


def fetch_activities(access_token, client_id):
    """Function to fetch Simkl activities dates"""

    url = f"{API_URL}/sync/activities"
    response = requests.post(url, headers=build_headers(access_token, client_id), timeout=10)

    response.raise_for_status()
    return response.json()


def extract_activity_timestamps(data):
    """Fetch necessary dates from the activity data"""

    return {
        "shows": data.get("tv_shows", {}).get("all"),
        "anime": data.get("anime", {}).get("all"),
        "movies": data.get("movies", {}).get("all"),
    }


def build_headers(access_token, client_id):
    """
    Build the header required by Simkl API
    """

    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "simkl-api-key": client_id,
    }


def fetch_all_items(access_token, client_id):
    """
    Fetch all items data from Simkl
    """

    url = f"{API_URL}/sync/all-items"
    response = requests.get(url, headers=build_headers(access_token, client_id), timeout=10)

    response.raise_for_status()
    return response.json()


def extract_ids(data):
    """Extract Simkl IDs along with item type"""

    items_map = {}

    for category in ["shows", "anime", "movies"]:
        items = data.get(category, [])

        for item in items:
            if "show" in item:
                simkl_id = item["show"]["ids"]["simkl"]

                if category == "shows":
                    items_map[str(simkl_id)] = "tv"
                elif category == "anime":
                    items_map[str(simkl_id)] = "anime"
            elif "movie" in item:
                simkl_id = item["movie"]["ids"]["simkl"]
                items_map[str(simkl_id)] = "movies"

    return items_map


def load_json_data(file_name):
    """Function to load data from disk"""

    if not os.path.exists(file_name):
        return {}

    with open(file_name, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def save_json_data(data, file_name):
    """Function to write data to disk"""

    with open(file_name, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, sort_keys=True)


def fetch_details(simkl_id, media_type, access_token, client_id):
    """Fetch detail about missing item"""

    url = f"{API_URL}/{media_type}/{simkl_id}"
    response = requests.get(url, headers=build_headers(access_token, client_id), timeout=10)

    if response.status_code == 404:
        return {
            "title": "Unknown (Deleted)", "year": None, "type": media_type,
            "ids": {"simkl": simkl_id, "slug": "deleted"}
        }

    response.raise_for_status()
    return response.json()


def format_details(details, simkl_id, media_type):
    """Function to return only required fields"""

    title = details.get("title")
    year = details.get("year")
    slug = details.get("ids", {}).get("slug")

    result = {
        "title": title,
        "year": year,
        "type": media_type,
        "ids": {
            "simkl": simkl_id,
            "slug": slug
        }
    }

    if slug:
        result["url"] = f"https://simkl.com/{media_type}/{simkl_id}/{slug}"

    return result


def build_html_table(items):
    """Function to build Email body"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not items:
        return f"""
        <html>
        <body style="font-family: Arial; background:#f4f6f8; padding:20px;">
            <table align="center" width="600" cellpadding="10" cellspacing="0"
                   style="background:white; border-radius:8px; border:1px solid #ddd;">
                <tr>
                    <td align="center" style="font-size:20px; font-weight:bold; color:#2d3748;">
                        Simkl Check Report
                    </td>
                </tr>
                <tr>
                    <td align="center" style="color:#718096;">
                        {now}
                    </td>
                </tr>
                <tr>
                    <td align="center" style="padding:30px;">
                        <div style="font-size:18px; color:#38a169; font-weight:bold;">
                            Nothing was Deleted 🎉
                        </div>
                        <div style="color:#718096; margin-top:10px;">
                            Your list is intact. No changes detected.
                        </div>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td style="padding:8px;">
                <a href="{item['url']}" style="color:#3182ce; text-decoration:none; font-weight:bold;">
                   {item['title']}
                </a>
            </td>
            <td style="text-align:center; color:#4a5568;">
                {item['year']}
            </td>
            <td style="text-align:center; color:#718096;">
                {item['type']}
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family: Arial; background:#f4f6f8; padding:20px;">

        <table align="center" width="700" cellpadding="10" cellspacing="0"
               style="background:white; border-radius:8px; border:1px solid #ddd;">
            <tr>
                <td align="center" style="font-size:22px; font-weight:bold; color:#2d3748;">
                    Simkl Removal Report
                </td>
            </tr>
            <tr>
                <td align="center" style="color:#718096;">
                    {now}
                </td>
            </tr>
            <tr>
                <td style="padding:10px;">
                    <b>Total Removed:</b> {len(items)}
                </td>
            </tr>
            <tr>
                <td>
                    <table width="100%" border="1" cellpadding="6" cellspacing="0"
                           style="border-collapse:collapse; border-color:#e2e8f0;">
                        <tr style="background:#edf2f7;">
                            <th align="left">Title</th>
                            <th>Year</th>
                            <th>Type</th>
                        </tr>
                        {rows}
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def main():
    """Main Driver Function"""

    if os.path.exists(".env"):
        load_dotenv(".env")

    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    if not client_id or not access_token:
        print("Missing required Tokens. Existing...")
        sys.exit(1)

    simkl_id_file = os.path.join("data", "simkl_ids.json")
    old_data = load_json_data(simkl_id_file)
    print("Reading Old JSON...")

    if not old_data:
        data = fetch_all_items(access_token, client_id)
        current_data = extract_ids(data)
        save_json_data(current_data, simkl_id_file)
        print("Saving Initial State. Only executed on 1st Run...")
        return

    old_ids = set(old_data.keys())
    # print(old_ids)

    data = fetch_all_items(access_token, client_id)
    current_data = extract_ids(data)
    current_ids = set(current_data.keys())
    # print(current_ids)

    print("Comparing Old and New Data...")
    missing_ids = old_ids - current_ids
    print(f"Missing IDs: {'None' if not missing_ids else missing_ids}")
    set_github_env("REMOVED_COUNT", len(missing_ids))

    missing_items = []

    for simkl_id in missing_ids:
        media_type = old_data[str(simkl_id)]

        details = fetch_details(simkl_id, media_type, access_token, client_id)
        cleaned = format_details(details, simkl_id, media_type)
        missing_items.append(cleaned)

    print("Saving New JSON...")
    save_json_data(current_data, simkl_id_file)

    html_content = build_html_table(missing_items)
    print("Generating HTML Body...")
    with open(os.path.join("data", "email.html"), "w", encoding="utf-8") as html_file:
        html_file.write(html_content)


if __name__ == "__main__":
    main()
