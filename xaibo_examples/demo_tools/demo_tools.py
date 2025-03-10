from datetime import datetime, timezone, timedelta

from xaibo.primitives.modules.tools.python_tool_provider import tool


@tool
def current_time():
    """Gets the current time in UTC"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@tool
def weather(city: str, country: str = "Germany"):
    """Gets the weather for the city and country
    :param city: The city name
    :param country: The country name
    """
    if country == "Germany":
        raise Exception("Something went wrong")
    return "Cold. Always."


@tool
def calendar(date: str):
    """ Returns the calendar entries for the given date

    :param date: Date in YYYY-MM-DD format
    """
    today = datetime.today().strftime("%Y-%m-%d")
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    utc = 'utc'
    data = {
        today: [
            {
                'start': {
                    'date': today,
                    'timezone': utc,
                    'time': '09:00'
                },
                'end': {
                    'date': today,
                    'timezone': utc,
                    'time': '10:00'
                },
                'subject': "Daily Standup",
                'participants': ["Eduardo", "Paul", "Fahreza", "Mansour"],
                'description': None
            },
            {
                'start': {
                    'date': today,
                    'timezone': utc,
                    'time': '10:00'
                },
                'end': {
                    'date': today,
                    'timezone': utc,
                    'time': '11:00'
                },
                'subject': "Breakfast",
                'participants': [],
                'description': None
            },
            {
                'start': {
                    'date': today,
                    'timezone': utc,
                    'time': '11:00'
                },
                'end': {
                    'date': today,
                    'timezone': utc,
                    'time': '18:00'
                },
                'subject': "Focus Time",
                'participants': [],
                'description': "Do the work."
            }
        ],
        tomorrow: [
            {
                'start': {
                    'date': tomorrow,
                    'timezone': utc,
                    'time': '14:00'
                },
                'end': {
                    'date': tomorrow,
                    'timezone': utc,
                    'time': '16:00'
                },
                'subject': "Talk: How to build AI Agents with Xpress AI",
                'participants': [],
                'description': "Give the talk on how to create useful AI agents."
            }
        ]
    }

    return data[date]