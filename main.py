import os
import pytz
from datetime import datetime, timedelta
from sheets import fetch_sheet_csv as fetch_sheet
from groupme_bot import send_groupme_message

# --- CONFIGURATION ---
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")  # From GitHub Secrets
DEFAULT_TAB = "sheet1"
SUNDAY_TAB = "sheet2"
LOCAL_TZ = pytz.timezone("America/Chicago")  # <-- Change this to your timezone

# --- DATE HANDLING ---
def handle_date():
    """Determine the correct date and Google Sheet tab based on local weekday."""
    today = datetime.now(LOCAL_TZ).date()
    tab_gid = DEFAULT_TAB
    weekday = today.weekday()  # Monday=0 ... Sunday=6

    print(f"[DEBUG] Local date: {today}, weekday: {weekday}")

    if weekday == 1:  # Tuesday → use Wednesday
        today += timedelta(days=1)
    elif weekday == 5:  # Saturday → use Sunday tab
        today += timedelta(days=1)
        tab_gid = SUNDAY_TAB
    elif weekday == 6:  # use Sunday tab
        tab_gid = SUNDAY_TAB
    elif weekday != 2:  # Not Wednesday → skip
        print("Did not match special days:", today)
        return None, None

    return today.strftime("%Y-%m-%d"), tab_gid

# --- MESSAGE FORMATTING ---
def make_human_readable(date_str, data, tab):
    """Create a human-readable message from sheet data based on tab."""
    matching_row = next((row for row in data if row[0] == date_str), None)
    if not matching_row:
        return f"No data found for {date_str}"

    if tab == DEFAULT_TAB:
        activity = matching_row[1]
        time = matching_row[2]
        extra = matching_row[3]
        extra_text = "" if extra == "" else f", bring {extra}"
        return f"The Wednesday activity for {matching_row[0]} is {activity} at {time}{extra_text}"
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
    today, tab_gid = handle_date()
    if not today or not tab_gid:
        print("No returned data")
        return

    data = fetch_sheet(SHEET_ID, tab_gid)
    msg = make_human_readable(today, data, tab_gid)
    print(msg)
    send_groupme_message(msg)

if __name__ == "__main__":
    main()
