import requests
import csv
from io import StringIO

# Map logical tab names to GID numbers
SHEET_GIDS = {
    'sheet1': '0',
}

def fetch_sheet_csv(sheet_id, tab):
    """
    Fetches CSV data from a specific tab in a public Google Sheet.

    Parameters:
        sheet_id (str): The ID of the Google Sheet.
        tab (str): A logical name like 'sheet1' or 'sheet2'.

    Returns:
        list[list[str]]: 2D array of cell values.
    """
    if tab not in SHEET_GIDS:
        raise ValueError(f"Invalid tab: '{tab}'. Must be one of {list(SHEET_GIDS.keys())}.")

    gid = SHEET_GIDS[tab]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    response = requests.get(url)
    response.raise_for_status()

    f = StringIO(response.text)
    reader = csv.reader(f)
    data = list(reader)
    return data
