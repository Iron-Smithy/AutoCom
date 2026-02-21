import os
import pytz
from datetime import datetime, timedelta
from sheets import fetch_sheet_csv as fetch_sheet
from groupme_bot import send_groupme_message

# --- CONFIGURATION ---
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")  # From GitHub Secrets
if not SHEET_ID:
    raise ValueError("Environment variable GOOGLE_SHEET_ID is missing")
DEFAULT_TAB = "sheet1"
LOCAL_TZ = pytz.timezone("America/Chicago")  # <-- Change this to your timezone

# --- HELPERS ---
def is_empty(value):
    return value is None or value.strip() == "" or value.strip().lower() in {"null", "[null]", "none", "[none]", "empty", "[empty]"} 

def safe_get(row, index, default=""):
    try:
        return row[index].strip()
    except (IndexError, AttributeError):
        return default

def is_first_sunday(date_obj):
    first_of_month = date_obj.replace(day=1)
    first_sunday_offset = (6 - first_of_month.weekday()) % 7
    first_sunday = first_of_month + timedelta(days=first_sunday_offset)
    return date_obj.date() == first_sunday.date()

# --- MAIN PROGRAM ---
def main(): 
    test_date_str = None  # e.g. "2025-10-26" or other dates for testing. else set to: None
    if test_date_str:
        now = datetime.strptime(test_date_str, "%Y-%m-%d")
        # ensure it's timezone-aware in LOCAL_TZ
        if now.tzinfo is None:
            # user may pass a naive datetime -> localize it
            now = LOCAL_TZ.localize(now)
        else:
            # convert to local tz if different
            now = now.astimezone(LOCAL_TZ)
    else:
        now = datetime.now(LOCAL_TZ)

    try:
        data = fetch_sheet(SHEET_ID, DEFAULT_TAB)
        if not data:
            print(f"[WARNING] No data returned from sheet {DEFAULT_TAB}")
            return
    except Exception as e:
        print(f"[ERROR] Failed to fetch sheet: {e}")
        return
    
    msg = []

    if (is_first_sunday(now)):
        msg.append("today is fast sunday")

    for row in data[1:]: # Skips the header row
        type, date_str, name, *alertAtList = row
        alertAtList = [s for s in alertAtList if s.strip()]
        
        match type:
            case "birth":
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if date.month == now.month and date.day == now.day:
                    msg.append(f"happy birthday {name}! \nhe's turning {now.year - date.year} 🥳")
            
            case "special":
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                if target_date == now.date():
                    msg.append(f"{name} is today")
                    continue
                
                for alertAt in alertAtList:
                    alert_date = target_date - timedelta(int(alertAt))
                    
                    if alert_date == now.date():
                        time_label = "tomorrow" if int(alertAt) <= 1 else f"in {alertAt} days"
                        msg.append(f"Upcoming Event Alert for {name}! The event is {time_label} ({date_str}).")
                        continue

    print("\n".join(msg))
    if (msg):
        try:
            send_groupme_message("\n".join(msg))
        except Exception as e:
            print(f"[ERROR] Failed to send GroupMe message: {e}")

if __name__ == "__main__":
    main()
