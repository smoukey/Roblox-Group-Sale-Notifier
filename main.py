import requests
import json
from time import sleep

with open("config.json", "r") as file:
    config = json.load(file)

cookie = config["ROBLOX_TOKEN"]
webhook_url = config["WEBHOOK_URL"]
group_id = config["GROUP_ID"]
check_interval = config["CHECK_INTERVAL"]

headers = {'Cookie': f'.ROBLOSECURITY={cookie}'}
last_pending_robux = None

def get_pending_robux():
    try:
        url = f"https://economy.roblox.com/v1/groups/{group_id}/revenue/summary/day"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("pendingRobux", 0)
    except Exception as e:
        print(f"Error fetching pending Robux: {e}")
        return None

def get_data():
    try:
        url = f"https://economy.roblox.com/v2/groups/{group_id}/transactions?limit=100&sortOrder=Asc&transactionType=Sale"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])[0] if data.get("data") else None
    except Exception as e:
        print(f"Error fetching group transactions: {e}")
        return None

def send_webhook(data, pending_robux):
    user_id = data['agent']['id']
    username = data['agent']['name']
    product_name = data['details']['name']
    product_price = data['currency']['amount']

    description = f"""
    ```fix
Username: {username}
Product Name: {product_name}
Product Price: {product_price} Robux
    ```
    """
    
    message = {
        "content": "🎉",
        "embeds": [
            {
                "title": "Item Sold",
                "description": description,
                "color": 16776960,
                "thumbnail": {
                    "url": f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png"
                },
                "footer": {
                    "text": f"Pending Robux: {pending_robux}"
                }
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        print("Webhook sent successfully!")
    except Exception as e:
        print(f"Error sending webhook: {e}")

def start():
    global last_pending_robux
    prev_data = None

    while True:
        try:
            current_data = get_data()
            pending_robux = get_pending_robux()

            if pending_robux is None:
                print("Error fetching pending Robux. Skipping this iteration.")
                sleep(check_interval)
                continue

            if current_data and current_data != prev_data:
                send_webhook(current_data, pending_robux)
                prev_data = current_data

            if last_pending_robux is None or pending_robux != last_pending_robux:
                print(f"Pending Robux updated: {pending_robux}")
                last_pending_robux = pending_robux
            else:
                print("No changes in pending Robux.")

            sleep(check_interval)
        except Exception as e:
            print(f"An error occurred: {e}. Restarting loop...")
            continue

start()
