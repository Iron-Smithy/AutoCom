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
SUNDAY_TAB = "sheet2"
LOCAL_TZ = pytz.timezone("America/Chicago")  # <-- Change this to your timezone

# --- DATE HANDLING ---
def handle_date(now=None):
    """
    If `now` is provided it must be a timezone-aware datetime (same tz as LOCAL_TZ).
    If not provided, uses datetime.now(LOCAL_TZ).
    Returns (target_date_str, tab_gid) or (None, None) when no action required.
    """
    if now is None:
        now = datetime.now(LOCAL_TZ)
    else:
        # ensure it's timezone-aware in LOCAL_TZ
        if now.tzinfo is None:
            # user may pass a naive datetime -> localize it
            now = LOCAL_TZ.localize(now)
        else:
            # convert to local tz if different
            now = now.astimezone(LOCAL_TZ)

    today = now.date()
    weekday = today.weekday()  # Monday=0 ... Sunday=6

    tab_gid = DEFAULT_TAB
    day_offset = 0

    if weekday == 1:  # Tuesday -> announce Wednesday
        day_offset = 1
    elif weekday == 5:  # Saturday -> Sunday tab (announce Sunday)
        day_offset = 1
        tab_gid = SUNDAY_TAB
    elif weekday == 6:  # Sunday -> Sunday tab (today)
        tab_gid = SUNDAY_TAB
    elif weekday != 2:  # Not Wednesday -> no action
        print(f"[INFO] Today ({today}) does not require processing.")
        return None, None

    target_date = today + timedelta(days=day_offset)
    print(f"[DEBUG] Target date: {target_date}, tab: {tab_gid}")
    return target_date.strftime("%Y-%m-%d"), tab_gid

# --- HELPERS ---
def is_empty(value):
    return value is None or value.strip() == "" or value.strip().lower() in {"null", "[null]", "none", "[none]", "empty", "[empty]"} 

def safe_get(row, index, default=""):
    try:
        return row[index].strip()
    except (IndexError, AttributeError):
        return default

# --- MESSAGE FORMATTING ---
def make_human_readable(date_str, data, tab):
    """Create a human-readable message from sheet data based on tab."""
    matching_row = next((row for row in data if row[0] == date_str), None)
    if not matching_row:
        return f"No data found for {date_str}"

    if tab == DEFAULT_TAB:
        activity = safe_get(matching_row, 1)
        where = safe_get(matching_row, 2)
        extra = safe_get(matching_row, 3)

        if activity.strip().lower() == "!unmarked":
            return f"{matching_row[0]} has no marked activity"

        if is_empty(activity):
            return f"No Wednesday activity is scheduled for {matching_row[0]}."

        message = f"The Wednesday activity for {matching_row[0]} is {activity}"

        if is_empty(where):
            pass
            # dont mention it
        elif where.upper() == "IDK":
            message += ". Location is unknown"
        else:
            message += f" at {where}"

        if not is_empty(extra):
            message += f". Bring {extra}"

        return message
    else:  # Sunday
        custom_message = safe_get(matching_row, 1)

        if not is_empty(custom_message):
            return f"{matching_row[0]}: {custom_message}"

        bread = safe_get(matching_row, 2)
        sacrament = safe_get(matching_row, 3)
        lesson = safe_get(matching_row, 4)
        fsy = safe_get(matching_row, 5)

        lines = [f"Responsibilities for Sunday {matching_row[0]}:"]

        if not is_empty(bread):
            lines.append(f"  {bread} has Bread")
        if not is_empty(sacrament):
            lines.append(f"  {sacrament} has Sacrament Prep")
        if not is_empty(lesson):
            if lesson.lower() == '5th sunday':
                lines.append(f"  today is 5th sunday")
            else:
                lines.append(f"  {lesson} has Lesson")
        if not is_empty(fsy):
            lines.append(f"  {fsy} has the FSY lesson")

        if len(lines) == 1:
            lines.append("  No responsibilities have been assigned yet.")

        return "\n".join(lines)


# --- MAIN PROGRAM ---
def main():
    test_date_str = None  # e.g. "2025-10-26" or other dates for testing. else set to: None
    if test_date_str:
        naive = datetime.strptime(test_date_str, "%Y-%m-%d")
        today, tab_gid = handle_date(now=naive)  # will be localized inside handle_date
    else:
        today, tab_gid = handle_date()

    if not today or not tab_gid:
        print("No returned data")
        return

    try:
        data = fetch_sheet(SHEET_ID, tab_gid)
        if not data:
            print(f"[WARNING] No data returned from sheet {tab_gid}")
            return
    except Exception as e:
        print(f"[ERROR] Failed to fetch sheet: {e}")
        return

    msg = make_human_readable(today, data, tab_gid)
    print(msg)
    try:
        send_groupme_message(msg)
    except Exception as e:
        print(f"[ERROR] Failed to send GroupMe message: {e}")

if __name__ == "__main__":
    main()
