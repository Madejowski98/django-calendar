from django.apps import AppConfig
from datetime import datetime, timedelta
from djangocalendar import settings
import requests


def get_events():
    # Define the API endpoint
    url = f"{settings.BASE_URL}/events/"
    headers = {
        'api-key': settings.API_KEY  # Include the API key in the request headers
    }

    # Make the GET request to the API
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        events = response.json()  # This should be the list of events

        # Convert start_time to datetime objects
        for event in events:
            event['start_time'] = datetime.fromisoformat(event['start_time'])  # Parse start_time to datetime

        print("Fetched events data:", events)  # Print for debugging
        return events  # Return the list of events directly
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []  # Return an empty list if the API call fails


class CalConfig(AppConfig):
    name = 'cal'
    def ready(self):
        from .models import Event
        events = get_events()

        for event in events:
            enddate = event['start_time'] + timedelta(hours=int(event['duration']))
            Event.objects.create(title=event['name'], start_time=event['start_time'] ,end_time=enddate, description=event['short_description'])
