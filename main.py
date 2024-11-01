import time
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from accounts_config.mapping import Mapping
import logging
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(filename='script.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Add these at the beginning of your script
INSTAGRAM_USERNAME = "workbn92"
INSTAGRAM_PASSWORD = "Elenita_Es_La_Mas_Guapa_26102024"

ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_ACCOUNT_ID')

# Email configuration
EMAIL = "bachatanow.app@gmail.com"  # This email will be used for both sending and receiving alerts

import os
from google.oauth2 import service_account
from google.auth import exceptions

def get_instagram_account_info():
    url = f"https://graph.instagram.com/v12.0/{INSTAGRAM_ACCOUNT_ID}?fields=id,username,account_type&access_token={ACCESS_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f'account info ok : {response.json()}')
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_sheets_credentials():
    try:
        # Create a dictionary with the service account info
        service_account_info = {
            "type": "service_account",
            "project_id": os.environ.get("bachatanow"),
            "private_key_id": os.environ.get("PRIVATE_KEY_ID"),
            "private_key": os.environ.get("PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.environ.get("CLIENT_EMAIL"),
            "client_id": os.environ.get("CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/gmail-api-access%40bachatanow.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return creds
    except exceptions.MalformedError as e:
        logging.info(f"Error creating credentials: {e}")
        return None

def get_gmail_credentials():
    creds = None

    # Hardcoded client configuration
    client_config = {
        "installed": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "project_id": "bachatanow",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": ["http://localhost"]
        }
    }

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                client_config,
                scopes=['https://www.googleapis.com/auth/gmail.send'],
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            auth_url, _ = flow.authorization_url(prompt='consent')

            logging.info(f"Please visit this URL to authorize the application: {auth_url}")
            code = input("Enter the authorization code: ")

            flow.fetch_token(code=code)
            creds = flow.credentials

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def send_email(service, subject, body):
    message = MIMEText(body)
    message['to'] = EMAIL
    message['from'] = EMAIL
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    try:
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logging.info("Email alert sent successfully")
    except Exception as e:
        logging.info(f"Failed to send email: {e}")

def get_instagram_business_account_id(username):
    url = f"https://graph.instagram.com/v12.0/{INSTAGRAM_ACCOUNT_ID}"
    params = {
        "fields": "id,username",
        "access_token": ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('id')
    else:
        print(f"Error: {response.text}")
        return None

def check_new_post(username):
    url = f"https://graph.instagram.com/v12.0/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username",
        "access_token": ACCESS_TOKEN,
        "limit": 1
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            most_recent_post = data['data'][0]
            return {
                'id': most_recent_post['id'],
                'caption': most_recent_post.get('caption', ''),
                'media_type': most_recent_post['media_type'],
                'media_url': most_recent_post.get('media_url', most_recent_post.get('thumbnail_url', '')),
                'permalink': most_recent_post['permalink'],
                'timestamp': most_recent_post['timestamp'],
                'username': most_recent_post['username']
            }
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return None

    # except requests.exceptions.RequestException as e:
    #     print(f"Error fetching posts for account {username}: {str(e)}")
    #     return None

def get_next_date(day):
    days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    today = datetime.now()
    day_index = days.index(day)
    days_ahead = day_index - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

def add_event_to_spreadsheet(service, spreadsheet_id, day, date, post_id):
    range_ = 'Sheet1!A:J'  # Use 'Sheet1' instead of 'events'
    values = [
        ["The host", "Calle Ferraz, 38, Madrid", date, day, "22.00 - 03.00",
         "X Lokura", "12, 20", "15", "thehostclub.38", post_id]
    ]
    body = {'values': values}
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body).execute()
        logging.info(f"Added new row to spreadsheet: {result.get('updates').get('updatedRange')}")
    except Exception as e:
        logging.info(f"Error adding to spreadsheet: {e}")

def main():
    last_post_id = None
    gmail_creds = get_gmail_credentials()
    sheets_creds = get_sheets_credentials()
    gmail_service = build('gmail', 'v1', credentials=gmail_creds)
    sheets_service = build('sheets', 'v4', credentials=sheets_creds)
    days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    SPREADSHEET_ID = '1u5dG4CU4bxm4pw3kEh3hZicql7ZG_XkWp7aTYddufTQ'  # Replace with your actual spreadsheet ID

    accounts = ['workbn92']
    account_info = get_instagram_account_info()
    print(f'account_info : {account_info}')
    try:
        for account in accounts:
            logging.info(f"Monitoring Instagram account: {account}")
            print(f"Monitoring Instagram account: {account}")
            latest_post = check_new_post(account)
            print(f'latest_post : {latest_post}')
            # if latest_post and latest_post.shortcode != last_post_id:
            #     logging.info(f"New post detected: {latest_post.url}")
            #     logging.info(f"Post ID: {latest_post.shortcode}")
            #
            #     caption = latest_post.caption.lower() if latest_post.caption else ""
            #     found_days = [day for day in days if day in caption]
            #
            #     if found_days:
            #         for day in found_days:
            #             next_date = get_next_date(day)
            #             logging.info(f"Next {day}: {next_date}")
            #             add_event_to_spreadsheet(sheets_service, SPREADSHEET_ID, day, next_date, latest_post.shortcode)
            #
            #     subject = f"New Instagram Post from {account}"
            #     body = f"A new Instagram post has been detected for {account}.\n\nPost URL: {latest_post.url}\nPost ID: {latest_post.shortcode}"
            #
            #     if found_days:
            #         body += "\n\nUpcoming dates:"
            #         for day in found_days:
            #             next_date = get_next_date(day)
            #             body += f"\nNext {day}: {next_date}"
            #
            #     send_email(gmail_service, subject, body)
            #
            #     last_post_id = latest_post.shortcode

    except Exception as e:
        logging.info(f"An error occurred: {e}")

    time.sleep(60)

if __name__ == "__main__":
    main()