from collections import defaultdict
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

        # Fetch events from the API and add to context
        context['events'] = get_events()  # Call to fetch events from the API

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


def create_month_calendar(year, month):
    # Create a month calendar as a matrix
    month_calendar = calendar.monthcalendar(year, month)

    # Convert the calendar into a more usable format
    calendar_structure = []
    for week in month_calendar:
        week_days = []
        for day in week:
            if day == 0:  # Day is zero if it's not in the month
                week_days.append(None)  # Represent empty days with None
            else:
                week_days.append(datetime(year, month, day))
        calendar_structure.append(week_days)

    return calendar_structure


def calendar_view(request):
    now = datetime.now()
    year = now.year
    month = now.month

    calendar = create_month_calendar(year, month)  # Your function to create the calendar structure

    # Fetch events for the current month
    events_by_date = get_events()  # Fetch events organized by date

    return render(request, 'cal/calendar.html', {
        'events_by_date': events_by_date,
        'calendar': calendar,
        'year': year,
        'month': month,
    })


def get_events():
    # Define the API endpoint
    url = f"{settings.BASE_URL}/events/"
    headers = {
        'api-key': settings.API_KEY  # Include the API key in the request headers
    }

    # Make the GET request to the API
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()  # Parse the JSON response
        events_by_date = defaultdict(list)  # Create a dictionary to store events by date

        for event in data:
            start_time = datetime.fromisoformat(event['start_time'])
            event['start_time'] = start_time  # Store as datetime
            events_by_date[start_time.date()].append(event)  # Group events by their date

        return events_by_date  # Return the dictionary of events organized by date
    else:
        return {}  # Return an empty dictionary if the API call fails

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