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


# --- MESSAGE FORMATTING ---
def make_human_readable(date_str, data, tab):
    """Create a human-readable message from sheet data based on tab."""
    matching_row = next((row for row in data if row[0] == date_str), None)
    if not matching_row:
        return f"No data found for {date_str}"

    if tab == DEFAULT_TAB:
        activity = matching_row[1]
        where = matching_row[2]
        extra_data = matching_row[3]
        extra_text = "" if extra_data == "" else f", bring {extra_data}"

        if activity == "[None]":
            return f"No activity {matching_row[0]}"
        if activity == "[Empty]":
            return f"No marked activity {matching_row[0]}"

        return f"The Wednesday activity for {matching_row[0]} is {activity}{". No marked location" if where == "IDK" else f" at {where}"}{extra_text}"
    else:
        if matching_row[1] == "Null":
            return f"{matching_row[0]} is {matching_row[2]}"
        else:
            if matching_row[3] == "Null":
                return (
                    f"Responsibilities for the Sunday of {matching_row[0]}:\n"
                    f"  {matching_row[1]} has Bread\n"
                    f"  {matching_row[2]} have Sacrament Prep\n"
                    f"  Today is {matching_row[4]}"
                )
            else:
                return (
                    f"Responsibilities for the Sunday of {matching_row[0]}:\n"
                    f"  {matching_row[1]} has Bread\n"
                    f"  {matching_row[2]} have Sacrament Prep\n"
                    f"  {matching_row[3]} has Lesson\n"
                    f"  {matching_row[4]} has the FSY lesson"
                )

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
