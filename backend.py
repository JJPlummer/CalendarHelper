from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# Load Google Calendar credentials
CLIENT_ID = 'your-client-id'
CLIENT_SECRET = 'your-client-secret'
SCOPES = ['https://www.googleapis.com/auth/calendar']

@app.route('/schedule-task', methods=['POST'])
def schedule_task():
    data = request.json
    task_description = data['task']
    task_duration = int(data['duration'])

    # Load user credentials
    creds = Credentials.from_authorized_user_file('credentials.json', SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    # Get free/busy info
    now = datetime.utcnow().isoformat() + 'Z'
    end_of_day = (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + 'Z'

    events_result = service.freebusy().query(
        body={
            "timeMin": now,
            "timeMax": end_of_day,
            "items": [{"id": "primary"}]
        }
    ).execute()

    busy_times = events_result['calendars']['primary']['busy']
    free_times = calculate_free_times(busy_times, task_duration)

    if free_times:
        start_time = free_times[0]['start']
        end_time = (datetime.fromisoformat(start_time) + timedelta(minutes=task_duration)).isoformat()

        # Insert the task into the calendar
        event = {
            'summary': task_description,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'}
        }
        service.events().insert(calendarId='primary', body=event).execute()
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'No available slots'})

def calculate_free_times(busy_times, task_duration):
    now = datetime.utcnow()
    free_times = []
    for i in range(len(busy_times)):
        if i == 0 and now < datetime.fromisoformat(busy_times[0]['start'][:-1]):
            free_times.append({
                'start': now.isoformat(),
                'end': busy_times[0]['start']
            })
    return free_times

if __name__ == '__main__':
    app.run(debug=True)
