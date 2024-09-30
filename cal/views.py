from datetime import datetime, timedelta, date
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views import generic
from django.urls import reverse
from django.utils.safestring import mark_safe
import calendar
import requests
from django.conf import settings

from .models import Event
from .utils import Calendar
from .forms import EventForm


# Ensure these settings are in settings.py
# BASE_URL = 'https://rekrutacja.teamwsuws.pl'
# API_KEY = 'your_actual_api_key'

def index(request):
    return HttpResponse('hello')


class CalendarView(generic.ListView):
    model = Event
    template_name = 'cal/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        d = get_date(self.request.GET.get('month', None))
        cal = Calendar(d.year, d.month)
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)

        # Fetch events and add to context
        context['events'] = get_events()  # Fetch events here

        return context


def get_date(req_month):
    if req_month:
        year, month = (int(x) for x in req_month.split('-'))
        return date(year, month, day=1)
    return datetime.today()


def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month


def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month


def event(request, event_id=None):
    instance = Event()
    if event_id:
        instance = get_object_or_404(Event, pk=event_id)
    else:
        instance = Event()

    form = EventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('cal:calendar'))
    return render(request, 'cal/event.html', {'form': form})


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

def calendar_view(request):
    # Fetch the events from the API
    events = get_events()  # Call the function to get events

    # Render your calendar template and pass the events
    return render(request, 'cal/calendar.html', {'events': events})

def check_api_key(request):
    url = f"{settings.BASE_URL}/events/"  # Use the base URL and events endpoint
    headers = {
        'api-key': settings.API_KEY  # Use the API key from settings.py
    }

    response = requests.get(url, headers=headers)  # Make a GET request to the API

    if response.status_code == 200:
        # API key is valid, return the data
        return JsonResponse({'status': 'success', 'data': response.json()})
    else:
        # API key is invalid or there's another error
        return JsonResponse({'status': 'error', 'message': 'Invalid API key or request failed'},
                            status=response.status_code)