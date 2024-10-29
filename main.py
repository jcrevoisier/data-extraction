import instaloader
import time
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from instaloader.exceptions import LoginRequiredException
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import Flask

app = Flask(__name__)

# Initialize Instaloader
L = instaloader.Instaloader()

# Add these at the beginning of your script
INSTAGRAM_USERNAME = "workbn92"
INSTAGRAM_PASSWORD = "Elenita_Es_La_Mas_Guapa_26102024"

# Instagram username to monitor
USERNAME = "workbn92"

# Email configuration
EMAIL = "bachatanow.app@gmail.com"  # This email will be used for both sending and receiving alerts

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_gmail_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def send_email(service, subject, body):
    message = MIMEText(body)
    message['to'] = EMAIL
    message['from'] = EMAIL
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    try:
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        print("Email alert sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_new_post():
    try:
        if not L.context.is_logged_in:
            L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        profile = instaloader.Profile.from_username(L.context, USERNAME)
        posts = profile.get_posts()
        return next(posts)
    except LoginRequiredException:
        print("Login required. Please check your Instagram credentials.")
        return None
    except StopIteration:
        return None

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
        print(f"Added new row to spreadsheet: {result.get('updates').get('updatedRange')}")
    except Exception as e:
        print(f"Error adding to spreadsheet: {e}")

@app.route('/')
def main():
    print(f"Monitoring Instagram account: {USERNAME}")
    last_post_id = None
    creds = get_credentials()
    gmail_service = build('gmail', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    SPREADSHEET_ID = '1u5dG4CU4bxm4pw3kEh3hZicql7ZG_XkWp7aTYddufTQ'  # Replace with your actual spreadsheet ID

    try:
        latest_post = check_new_post()

        if latest_post and latest_post.shortcode != last_post_id:
            print(f"New post detected: {latest_post.url}")
            print(f"Post ID: {latest_post.shortcode}")
            
            caption = latest_post.caption.lower() if latest_post.caption else ""
            found_days = [day for day in days if day in caption]
            
            if found_days:
                for day in found_days:
                    next_date = get_next_date(day)
                    print(f"Next {day}: {next_date}")
                    add_event_to_spreadsheet(sheets_service, SPREADSHEET_ID, day, next_date, latest_post.shortcode)
            
            subject = f"New Instagram Post from {USERNAME}"
            body = f"A new Instagram post has been detected for {USERNAME}.\n\nPost URL: {latest_post.url}\nPost ID: {latest_post.shortcode}"
            
            if found_days:
                body += "\n\nUpcoming dates:"
                for day in found_days:
                    next_date = get_next_date(day)
                    body += f"\nNext {day}: {next_date}"
            
            send_email(gmail_service, subject, body)

            last_post_id = latest_post.shortcode

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)