# Activity & Responsibility Announcement Bot

**Google Sheets → GroupMe**

---

## 1. What This Program Does

This program automatically:

1. **Checks today’s date**
2. **Decides whether a message should be sent**
3. **Pulls information from a Google Sheet**
4. **Formats that information into a human-readable message**
5. **Posts the message to a GroupMe group**

It is designed for **weekly announcements**, specifically:

* **Wednesday activities**
* **Sunday responsibilities**

The program is typically run **once per day** (for example, using GitHub Actions).

---

## 2. Required Setup

### A. Google Sheet

You need a Google Sheet with **two tabs**:

| Purpose                 | Tab Name in Code |
| ----------------------- | ---------------- |
| Wednesday activities    | `sheet1`         |
| Sunday responsibilities | `sheet2`         |

> ⚠️ The tab names in the sheet **must match** the values used in the code.

---

### B. Environment Variables (Very Important)

The program **will not run** unless these environment variables are set.

#### Required Variables

```
GOOGLE_SHEET_ID
GROUPME_BOT_ID
```

| Variable Name     | Purpose                                    |
| ----------------- | ------------------------------------------ |
| `GOOGLE_SHEET_ID` | Identifies which Google Sheet to read      |
| `GROUPME_BOT_ID`  | Allows the bot to post messages to GroupMe |

These are usually stored in:

* GitHub Secrets
* Server environment variables
* A `.env` file for local testing

If either variable is missing, the program **fails fast and exits** (this is intentional).

---

### C. GroupMe Bot Setup (Required)

This program posts messages using a **GroupMe Bot**, not a user account.

#### 1. Create a GroupMe Bot

1. Visit the GroupMe developer site.
2. Create a new bot.
3. Attach the bot to the desired GroupMe group.
4. Copy the **Bot ID** (not an access token).

#### 2. Store the Bot ID

Set the bot ID as an environment variable:

```
GROUPME_BOT_ID
```

> ⚠️ If this value is missing, message sending will fail.

#### 3. How Messages Are Sent

Messages are sent using:

```python
send_groupme_message(text)
```

Internally, this:

* Calls the GroupMe Bot API
* Sends messages **as the bot**
* Logs success or failure to stdout

---

### D. Google Sheets Access Requirements

#### Sheet Must Be Public

The Google Sheet **must be publicly readable**.

Required sharing setting:

* **Anyone with the link → Viewer**

Why this is required:

* The program fetches data using Google’s **CSV export endpoint**
* No authentication is used

If the sheet is private:

* Requests will fail
* No data will be returned

---

### E. Sheets Helper Configuration (`sheets.py`)

The program uses `sheets.py` to fetch CSV data.

#### Tab → GID Mapping

```python
SHEET_GIDS = {
    'sheet1': '0',
    'sheet2': '779562486'
}
```

Important notes:

* GIDs **must match** the actual Google Sheet tab GIDs
* Renaming a tab does **not** change its GID
* Deleting and recreating a tab **does** change its GID

#### How to Find a Tab’s GID

1. Open the Google Sheet
2. Click the desired tab
3. Look at the URL for:

   ```
   gid=########
   ```

If the GID is wrong:

* The wrong tab will be read
* Or the request will fail

---

### F. Required Python Dependencies

Install the required packages:

```
requests
pytz
```

Example:

```bash
pip install requests pytz
```

(Standard library modules such as `os`, `datetime`, and `csv` are already included with Python.)

---

## 3. When Messages Are Sent (Date Logic)

The program **only sends messages on specific days**.

| Today Is      | What Happens                                  |
| ------------- | --------------------------------------------- |
| **Tuesday**   | Announces **Wednesday** activity              |
| **Wednesday** | Announces **today’s** Wednesday activity      |
| **Saturday**  | Announces **Sunday** responsibilities         |
| **Sunday**    | Announces **today’s** Sunday responsibilities |
| Any other day | **No message is sent**                        |

This logic lives in the `handle_date()` function.

---

## 4. Time Zone (Very Important)

```python
LOCAL_TZ = pytz.timezone("America/Chicago")
```

This controls **what day the program thinks it is**.

This ensures:

* Tuesday means *your* Tuesday
* Sunday means *your* Sunday

Even if the server runs in a different time zone.

---

## 5. Google Sheet Format

> ⚠️ **Dates must exactly match the format `YYYY-MM-DD`.**
> If the format does not match, the row will not be found.

---

### A. Wednesday Tab (`sheet1`)

| Column | Meaning                         |
| ------ | ------------------------------- |
| A      | Date (`YYYY-MM-DD`)             |
| B      | Activity name                   |
| C      | Location                        |
| D      | Extra items to bring (optional) |

**Behavior examples:**

* Empty activity → “No Wednesday activity scheduled”
* Location = `IDK` → “Location is unknown”
* Blank location → location is ignored

---

### B. Sunday Tab (`sheet2`)

| Column | Meaning                   |
| ------ | ------------------------- |
| A      | Date (`YYYY-MM-DD`)       |
| B      | Custom message (optional) |
| C      | Bread assignment          |
| D      | Sacrament prep            |
| E      | Lesson                    |
| F      | FSY lesson                |

**Important rule:**

* If **Column B (custom message)** is filled in, **all other columns are ignored**, and that message is posted instead.

---

## 6. What the Program Prints vs Sends

* `print(msg)` → outputs the message to logs (for debugging)
* `send_groupme_message(msg)` → sends the message to GroupMe

---

## 7. Testing Without Waiting for the Actual Date

You can simulate running on a specific day.

### Step 1: Set a Test Date

In `main()`:

```python
test_date_str = None
```

Change to:

```python
test_date_str = "2025-10-26"
```

This makes the program treat that date as “today”.

---

### Step 2: Disable Message Sending

While testing, **prevent real messages**:

```python
# send_groupme_message(msg)
```

---

### Step 3: Reset After Testing

When finished:

* Set `test_date_str = None`
* Re-enable `send_groupme_message(msg)`

---

## 8. Error Handling

The program:

* Exits early if no message is required
* Catches Google Sheet fetch errors
* Catches GroupMe API errors
* Safely handles missing or empty cells

---

## 9. Common Maintenance Tasks

### Change the time zone

```python
LOCAL_TZ = pytz.timezone("America/Chicago")
```

---

### Rename Google Sheet tabs

```python
DEFAULT_TAB = "sheet1"
SUNDAY_TAB = "sheet2"
```

---

### Change message wording

Edit only:

```python
make_human_readable()
```

No date logic or API code changes required.

---

## 10. What NOT to Change Unless You Know What You’re Doing

* `handle_date()` logic
* `fetch_sheet()` calls
* `send_groupme_message()`
* Environment variable handling

These control **when** and **where** messages are sent.

---

## 11. Google Sheet Value Reference

Explains **special values** recognized by the program.

### Special Keywords

#### `!unmarked`

* Indicates an **error or missing entry**
* Signals the value has not been intentionally set
* Distinguishes between “not filled out” and “intentionally blank”

> ⚠️ Only meaningful in the Wednesday activity column.

#### `IDK`

* Shorthand for **“I don’t know”**
* Used when a value (such as location) is unknown
* Message will note that the detail is unknown

---

### Null / Empty Values

The following values are treated as **empty** and ignored:

* `null`, `[null]`
* `none`, `[none]`
* `empty`, `[empty]`
* Blank cells

---

### Notes

* Values are **case-insensitive**
* Extra whitespace is trimmed
* Blank cells behave the same as null values
