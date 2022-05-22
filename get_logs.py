# Windows Event Log Viewer
import datetime
import win32evtlog # requires pywin32 pre-installed
import win32con
import sqlite3


file = "db.sqlite"

try:
    conn = sqlite3.connect(file)
    print("Database file connected")
except:
    print("Database failed to connect")

c = conn.cursor()


# def print_events(event):
#     print ('Source Name:', event.SourceName)
#     print ('Time Generated:', event.TimeGenerated)
#     print ('Event Category:', event.EventCategory)
#     print ('Event Type:', evt_type)
#     print('reserverd flags', event.ReservedFlags)
#     print('event id', event.EventID)
    
#     print("end \n")


def insert_data(event):
    
    check_data = c.execute(f''' Select date_time, event_id from event_errors WHERE date_time = '{event.TimeGenerated}'
                            AND event_id = '{event.EventID}' ''')

    entry = check_data.fetchone()
   
    if entry is None:
        c.execute(f'''INSERT INTO event_errors (level, date_time, source, event_id)
                VALUES ('{evt_type}', '{event.TimeGenerated}', '{event.SourceName}', '{event.EventID}' )''')
        print("executing query")
    else:
        print("already in")

    conn.commit()   
    


evt_dict={win32con.EVENTLOG_AUDIT_FAILURE:'EVENTLOG_AUDIT_FAILURE',  # storing all levels of errors and problems
            win32con.EVENTLOG_AUDIT_SUCCESS:'EVENTLOG_AUDIT_SUCCESS',
            win32con.EVENTLOG_INFORMATION_TYPE:'EVENTLOG_INFORMATION_TYPE',
            win32con.EVENTLOG_WARNING_TYPE:'EVENTLOG_WARNING_TYPE',
            win32con.EVENTLOG_ERROR_TYPE:'EVENTLOG_ERROR_TYPE'}

error_types_to_filter = [win32con.EVENTLOG_WARNING_TYPE, win32con.EVENTLOG_ERROR_TYPE] # filter by critical and error levels


number_of_hours_to_look_back = 48
datetime_back = datetime.datetime.now() - datetime.timedelta(hours=number_of_hours_to_look_back)


while True:
    server = 'localhost' # name of the target computer to get event logs
    log_types = ["Application", "Security"]
    for log_type in log_types:
        handle = win32evtlog.OpenEventLog(server,log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ|win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = win32evtlog.GetNumberOfEventLogRecords(handle)

        count_logs = 0

        while True:
            events = win32evtlog.ReadEventLog(handle, flags,0)
            if events:
                for event in events:

                    if event.EventType in error_types_to_filter and event.TimeGenerated >= datetime_back:
                        count_logs += 1
                        evt_type = str(evt_dict[event.EventType])

                        insert_data(event)
                    
                        
                if event.TimeGenerated < datetime_back:
                    print('log type: ' + 'total: ',log_type ,count_logs)
                    break

    if log_type == log_types[len(log_types)-1]:
        break






   


    
    

    


    


    
                
