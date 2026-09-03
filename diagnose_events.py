#!/usr/bin/env python3
"""
Diagnostic script to understand PyWin32 event object structure
"""

try:
    import win32evtlog
    
    print("Attempting to read Application log and inspect event structure...")
    
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    handle = win32evtlog.OpenEventLog(".", "Application")
    
    events_batch = win32evtlog.ReadEventLog(handle, flags, 0)
    
    if events_batch:
        event = events_batch[0]
        print(f"\nEvent type: {type(event)}")
        print(f"Event dir: {dir(event)}")
        
        print("\n--- Trying various methods ---")
        
        # Try different ways to access data
        try:
            print(f"event.GetEventID(): {event.GetEventID()}")
        except Exception as e:
            print(f"event.GetEventID() failed: {e}")
        
        try:
            print(f"event.GetType(): {event.GetType()}")
        except Exception as e:
            print(f"event.GetType() failed: {e}")
        
        try:
            print(f"event.GetSourceName(): {event.GetSourceName()}")
        except Exception as e:
            print(f"event.GetSourceName() failed: {e}")
        
        try:
            print(f"event.GetComputerName(): {event.GetComputerName()}")
        except Exception as e:
            print(f"event.GetComputerName() failed: {e}")
        
        try:
            print(f"event.GetRecordNumber(): {event.GetRecordNumber()}")
        except Exception as e:
            print(f"event.GetRecordNumber() failed: {e}")
        
        try:
            print(f"event.GetNumberOfStrings(): {event.GetNumberOfStrings()}")
        except Exception as e:
            print(f"event.GetNumberOfStrings() failed: {e}")
        
        try:
            print(f"event.GetEventCategory(): {event.GetEventCategory()}")
        except Exception as e:
            print(f"event.GetEventCategory() failed: {e}")
        
        try:
            props = event.GetEventRecordProps()
            print(f"event.GetEventRecordProps(): {props}")
        except Exception as e:
            print(f"event.GetEventRecordProps() failed: {e}")
        
        # Try tuple/list access
        print("\n--- Trying tuple/list access ---")
        try:
            print(f"event[0]: {event[0]}")
            print(f"event[1]: {event[1]}")
            print(f"event[2]: {event[2]}")
        except Exception as e:
            print(f"Tuple access failed: {e}")
        
        # Print raw event
        print(f"\n--- Raw event object ---")
        print(f"str(event): {str(event)}")
        print(f"repr(event): {repr(event)}")
    
    win32evtlog.CloseEventLog(handle)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
