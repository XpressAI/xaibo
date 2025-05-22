"""
Google Calendar tools for Xaibo agents.

This module provides comprehensive tools for interacting with Google Calendar API,
enabling agents to manage calendar events and retrieve calendar information.

Features:
- List upcoming events with flexible time ranges and result limits
- Create new calendar events with full details (title, time, location, description)
- Retrieve primary calendar metadata and settings

Authentication:
All tools require Google Calendar API authentication via OAuth 2.0. On first use,
the system will open a browser window for user authentication. Credentials are
automatically saved for future use.

Required Setup:
1. Enable Google Calendar API in Google Cloud Console
2. Download OAuth 2.0 credentials as 'credentials.json'
3. Place credentials.json in the same directory as this script

Available Tools:
- list_events(): Get upcoming events from primary calendar
- create_event(): Create new calendar events
- get_calendar_info(): Retrieve calendar metadata and settings

Example Usage:
    # List next week's events
    events = list_events(days_ahead=7, max_results=10)
    
    # Create a meeting
    event = create_event(
        summary="Team Meeting",
        start_datetime="2025-05-25T10:00:00",
        end_datetime="2025-05-25T11:00:00",
        location="Conference Room A"
    )
    
    # Get calendar info
    info = get_calendar_info()
"""

import os
import pickle
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from xaibo.primitives.modules.tools.python_tool_provider import tool

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def _get_calendar_service():
    """
    Get authenticated Google Calendar service.
    
    This function handles OAuth authentication automatically.
    On first run, it will open a browser for authentication.
    """
    creds = None
    token_file = 'token.pickle'
    credentials_file = 'credentials.json'
    
    # Check if we have stored credentials
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Credentials file '{credentials_file}' not found. "
                    "Please download your OAuth 2.0 credentials from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)


@tool
def list_events(days_ahead: int = 7, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Lists upcoming events from the user's primary Google Calendar.
    
    Retrieves events starting from the current time up to the specified number of days ahead,
    ordered by start time. Each event includes essential details like title, timing, and location.

    Examples:
        # Get next 5 events in the next 3 days
        events = list_events(days_ahead=3, max_results=5)
        print(f"Found {len(events)} events")
        for event in events:
            print(f"- {event['summary']} at {event['start']}")
        
        # Get all events for the next week (using defaults)
        events = list_events()
        
        # Get today's events only
        today_events = list_events(days_ahead=1, max_results=50)
        
        # Get next month's events (limited to 20 results)
        monthly_events = list_events(days_ahead=30, max_results=20)
    
    :param days_ahead: Number of days from today to look ahead for events. Must be a positive integer.
    :type days_ahead: int
    :param max_results: Maximum number of events to return. Must be a positive integer. The API may return fewer events if there aren't enough in the time range.
    :type max_results: int
    :returns: List of event dictionaries, each containing:
        - 'id' (str): Unique event identifier
        - 'summary' (str): Event title/name
        - 'start' (str): Start date/time in ISO format
        - 'end' (str): End date/time in ISO format
        - 'description' (str): Event description (empty string if none)
        - 'location' (str): Event location (empty string if none)
    :rtype: list[dict[str, Any]]
        
    :raises ValueError: If days_ahead or max_results are not positive integers
    :raises FileNotFoundError: If Google Calendar credentials file is not found
    :raises RuntimeError: If there's an error communicating with Google Calendar API
    """
    # Validate input parameters
    if days_ahead <= 0:
        raise ValueError("days_ahead must be a positive integer")
    
    if max_results <= 0:
        raise ValueError("max_results must be a positive integer")
    
    try:
        service = _get_calendar_service()
        
        # Calculate time range
        now = datetime.now(timezone.utc)
        time_max = now + timedelta(days=days_ahead)
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for better readability
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'start': start,
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'description': event.get('description', ''),
                'location': event.get('location', '')
            })
        
        return formatted_events
        
    except Exception as e:
        raise RuntimeError(f"Failed to list events: {str(e)}") from e


@tool
def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = '',
    location: str = ''
) -> Dict[str, Any]:
    """
    Creates a new event in the user's primary Google Calendar.
    
    Creates a calendar event with the specified title, time range, and optional details.
    The event will be immediately visible in Google Calendar and can be shared with others.
    All times are treated as UTC unless timezone information is included in the datetime strings.

    Examples:
        # Create a simple 1-hour meeting
        event = create_event(
            summary="Team Standup",
            start_datetime="2025-05-25T09:00:00",
            end_datetime="2025-05-25T10:00:00"
        )
        print(f"Created event: {event['htmlLink']}")
        
        # Create a detailed event with location and description
        event = create_event(
            summary="Project Review Meeting",
            start_datetime="2025-05-25T14:00:00-07:00",
            end_datetime="2025-05-25T15:30:00-07:00",
            description="Quarterly review of Project Alpha progress.\n\nAgenda:\n- Status update\n- Budget review\n- Next steps",
            location="Conference Room B, 2nd Floor"
        )
        
        # Create an all-day event (use date format)
        event = create_event(
            summary="Company Holiday",
            start_datetime="2025-12-25T00:00:00",
            end_datetime="2025-12-26T00:00:00",
            description="Christmas Day - Office Closed"
        )
        
        # Create a virtual meeting
        event = create_event(
            summary="Remote Client Call",
            start_datetime="2025-05-25T16:00:00Z",
            end_datetime="2025-05-25T17:00:00Z",
            location="https://meet.google.com/abc-defg-hij",
            description="Weekly check-in with Client XYZ"
        )
    
    :param summary: Title/name of the event. Cannot be empty or whitespace-only.
    :type summary: str
    :param start_datetime: Event start time in ISO 8601 format. Examples: "2025-05-25T10:00:00", "2025-05-25T10:00:00Z", "2025-05-25T10:00:00-07:00"
    :type start_datetime: str
    :param end_datetime: Event end time in ISO 8601 format. Must be after start_datetime. Same format requirements as start_datetime.
    :type end_datetime: str
    :param description: Detailed description or notes for the event. Can include formatting and links.
    :type description: str
    :param location: Event location (address, room name, or virtual meeting link).
    :type location: str
    :returns: Created event information containing:
        - 'id' (str): Unique Google Calendar event ID for future reference
        - 'summary' (str): Event title as created
        - 'start' (str): Actual start datetime as stored in calendar
        - 'end' (str): Actual end datetime as stored in calendar
        - 'htmlLink' (str): Direct URL to view/edit the event in Google Calendar
        - 'status' (str): Creation status (always 'created' on success)
    :rtype: dict[str, Any]
    
        
    :raises ValueError: If summary is empty, datetime formats are invalid, or end time is before start time
    :raises FileNotFoundError: If Google Calendar credentials file is not found
    :raises RuntimeError: If there's an error communicating with Google Calendar API
    """
    # Validate required parameters
    if not summary or not summary.strip():
        raise ValueError("Event summary cannot be empty")
    
    if not start_datetime or not end_datetime:
        raise ValueError("Both start_datetime and end_datetime are required")
    
    # Validate datetime format
    try:
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError(f"Invalid datetime format. Use ISO format (e.g., '2025-05-25T10:00:00'): {str(e)}") from e
    
    # Validate that end time is after start time
    if end_dt <= start_dt:
        raise ValueError("End datetime must be after start datetime")
    
    try:
        service = _get_calendar_service()
        
        # Create event object
        event = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'UTC',
            },
        }
        
        # Create the event
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return {
            'id': created_event['id'],
            'summary': created_event.get('summary'),
            'start': created_event['start'].get('dateTime'),
            'end': created_event['end'].get('dateTime'),
            'htmlLink': created_event.get('htmlLink'),
            'status': 'created'
        }
        
    except Exception as e:
        raise RuntimeError(f"Failed to create event: {str(e)}") from e


@tool
def get_calendar_info() -> Dict[str, Any]:
    """
    Retrieves metadata and settings information about the user's primary Google Calendar.
    
    Fetches basic information about the primary calendar including its display name,
    timezone settings, and other configuration details. This is useful for understanding
    the calendar context before creating events or for displaying calendar information to users.
    
    Examples:
        # Get basic calendar information
        cal_info = get_calendar_info()
        print(f"Calendar: {cal_info['summary']}")
        print(f"Timezone: {cal_info['timeZone']}")
        print(f"Calendar ID: {cal_info['id']}")
        
        # Check timezone before creating events
        cal_info = get_calendar_info()
        if cal_info['timeZone'] != 'UTC':
            print(f"Note: Calendar uses {cal_info['timeZone']} timezone")
        
        # Display calendar details to user
        cal_info = get_calendar_info()
        if cal_info['summary']:
            print(f"Working with calendar: '{cal_info['summary']}'")
        if cal_info['description']:
            print(f"Description: {cal_info['description']}")

    :returns: Calendar metadata containing:
        - 'id' (str): Calendar ID (typically the user's email address for primary calendar)
        - 'summary' (str): Calendar display name/title (empty string if not set)
        - 'description' (str): Calendar description (empty string if not set)
        - 'timeZone' (str): Calendar's default timezone (e.g., 'America/Los_Angeles')
        - 'location' (str): Calendar's default location (empty string if not set)
    :rtype: dict[str, Any]
        
    :raises FileNotFoundError: If Google Calendar credentials file is not found
    :raises RuntimeError: If there's an error communicating with Google Calendar API
    """
    try:
        service = _get_calendar_service()
        
        # Get primary calendar info
        calendar = service.calendars().get(calendarId='primary').execute()
        
        return {
            'id': calendar['id'],
            'summary': calendar.get('summary', ''),
            'description': calendar.get('description', ''),
            'timeZone': calendar.get('timeZone', ''),
            'location': calendar.get('location', '')
        }
        
    except Exception as e:
        raise RuntimeError(f"Failed to get calendar info: {str(e)}") from e