import argparse
import csv
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import tz

BASE_URL = "https://re-publica.com"
LANGUAGE = "en"
DATA_URL = f"{BASE_URL}/{LANGUAGE}/schedule"
TZ_NAME = "Europe/Berlin"
TZ = tz.gettz(TZ_NAME)


def get_dates():
    url = DATA_URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    date_elements = soup.find_all("input", class_="form-radio copy")
    dates = [element["value"] for element in date_elements]

    return dates


def scrape_republica_schedule_for_date(date):
    url = f"{DATA_URL}?day={date}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    session_elements = soup.find_all("div", class_="session")
    scraped_data = []

    for session_element in session_elements:
        time_element = session_element.find("div", class_="time")
        start_time = time_element.find("span", class_="start").text.strip()
        end_time = time_element.find("span", class_="end").text.strip()
        start_datetime = datetime.fromisoformat(f"{date}T{start_time}+02:00")
        end_datetime = datetime.fromisoformat(f"{date}T{end_time}+02:00")

        session_duration = end_datetime - start_datetime
        session_duration_hours, _seconds = divmod(session_duration.seconds, 3600)
        session_duration_minutes = _seconds // 60

        session_type = session_element.find("div", class_="session-type").text.strip()

        middle_element = session_element.find("div", class_="middle")
        session_title = middle_element.find("h3", class_="session-title").text.strip()
        session_url = middle_element.find("a")["href"]

        session_id = int(re.findall(r'\d+/?$', session_url)[0])

        speakers_element = middle_element.find("span", class_="speakers")
        speaker_links = speakers_element.find_all("a")
        session_speakers = [
            {
                "id": int(re.search(r"\d+", speaker.get("href")).group()),
                "public_name": speaker.text.strip()
            }
            for speaker in speaker_links
        ]

        description_element = session_element.find("div", class_="description")
        session_description = description_element.find("div", class_="inner").text.strip()

        right_element = session_element.find("div", class_="right")
        stage = right_element.find("h4", class_="stage-title").text.strip()
        session_format = right_element.find("span", class_="format").text.strip()
        session_language = right_element.find("span", class_="language").text.strip()

        track_element = right_element.find("div", class_="track")
        session_track = track_element.find("a").text.strip()

        is_partner_session = session_element.find("span", class_="session-has-partner") is not None

        session_data = {
            "id": session_id,
            "url": f"{BASE_URL}{session_url}",
            "start_datetime": start_datetime,
            "start_date": date,
            "start_time": start_time,
            "end_datetime": end_datetime,
            "end_date": date,
            "end_time": end_time,
            "duration": f"{session_duration_hours}:{session_duration_minutes:02}",
            "room": stage,
            "slug": generate_slug(session_title),
            "title": session_title,
            "track": session_track,
            "type": session_format,
            "language": session_language[:2].lower(),
            "abstract": shorten_description(session_description),
            "description": session_description,
            "translation": (stage in ["Stage 1", "Stage 2"] and not is_partner_session),
            "persons": session_speakers,
            "is_partner_session": is_partner_session
        }

        scraped_data.append(session_data)

    return scraped_data


def generate_slug(title):
    slug = re.sub(r"'", "", title)
    slug = re.sub(r"[^\w\d]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)  # Replace consecutive hyphens with a single hyphen
    slug = slug.strip("-")  # Remove leading and trailing hyphens
    return slug.lower()


def save_csv(data, output_file):
    keys = [x for x in list(data[0].keys()) if x not in ["persons"]] + ["speakers"]
    with open(output_file, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        for session in data:
            row = session.copy()
            row["speakers"] = ", ".join(person["public_name"] for person in session.get("persons", []))
            row["translation"] = session.get("translation", False)
            row.pop("persons", None)
            writer.writerow(row)


def save_json(data, output_file):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4, default=str)


def save_json_frab(data, output_file):
    # see https://c3voc.de/schedule/schema.json
    schedule = {
        "version": output_file.split('/')[1].split('.')[0],
        "base_url": f"{BASE_URL}/",
        "conference": {
            "acronym": "rp23",
            "title": "re:publica 2023",
            "start": data[0]["start_date"],
            "end": data[-1]["end_date"],
            "daysCount": 0,  # Using the number of scraped days
            "timeslot_duration": "00:15",  # Placeholder for timeslot duration
            "time_zone_name": TZ_NAME,
            "days": []
        }
    }

    day_groups = group_data_by_day(data)
    schedule["conference"]["daysCount"] = len(day_groups)

    for index, day_group in enumerate(day_groups, start=1):
        day_start = min(session["start_datetime"] for session in day_group)
        day_end = max(datetime.strptime(session["end_time"], "%H:%M").astimezone(tz=TZ).time() for session in day_group)
        rooms_data = group_data_by_room(day_group)
        rooms = {}
        for room, room_data in rooms_data.items():
            room_sessions = []
            for session in room_data:
                row = session.copy()
                row["start"] = row.pop("start_datetime").isoformat()
                row["guid"] = row["url"]
                row["logo"] = ""
                row.pop("start_date")
                row.pop("start_time")
                row.pop("end_datetime")
                row.pop("end_date")
                row.pop("end_time")
                row.pop("is_partner_session")
                row["do_not_record"] = False
                row["answers"] = []
                row["links"] = []
                row["attachments"] = []
                row["recording_license"] = "Unknown"
                room_sessions.append(row)
            rooms[room] = room_sessions

        day_data = {
            "index": index,
            "date": day_start.strftime("%Y-%m-%d"),
            "day_start": day_start.strftime("%H:%M"),
            "day_end": day_end.strftime("%H:%M"),
            "rooms": rooms
        }
        schedule["conference"]["days"].append(day_data)

    with open(output_file, "w") as file:
        json.dump(schedule, file, indent=4)


def group_data_by_day(data):
    day_groups = []
    current_day = None
    for session in data:
        session_day = session["start_date"]
        if session_day != current_day:
            current_day = session_day
            day_groups.append([])
        day_groups[-1].append(session)
    return day_groups


def group_data_by_room(data):
    room_groups = {}
    for session in data:
        room = session["room"]
        if room not in room_groups:
            room_groups[room] = []
        room_groups[room].append(session)
    return room_groups


def shorten_description(description, max_sentence_length=1, max_word_count=20):
    sentences = re.split(r'[.!?]\s+', description)
    abstract = sentences[0]
    if len(sentences) > max_sentence_length:
        abstract = ' '.join(sentences[:max_sentence_length])
    if len(abstract.split()) > max_word_count:
        abstract = ' '.join(abstract.split()[:max_word_count]) + '...'

    return abstract


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="re:publica Scraper")
    parser.add_argument("--csv", action="store_true", help="Output data in CSV format (default)")
    parser.add_argument("--json", action="store_true", help="Output data in JSON format")
    parser.add_argument("--frab", action="store_true", help="Output data in Frab schedule format")
    args = parser.parse_args()

    os.makedirs("scrapes", exist_ok=True)

    timestamp = datetime.now(TZ).strftime("%Y-%m-%dT%H%M%S%z")
    filename = f"scrapes/{timestamp}"

    dates = get_dates()

    print(f"Scraping {DATA_URL} for dates {', '.join(dates)}...")

    scraped_data = []
    for date in dates:
        print(f"\rDate {date}", end="")
        scraped_data.extend(scrape_republica_schedule_for_date(date))
    print("\r", end="")

    if args.frab:
        save_json_frab(scraped_data, f"{filename}-frab.json")
        print(f"Saved as {filename}-frab.json")
    if args.json:
        save_json(scraped_data, f"{filename}.json")
        print(f"Saved as {filename}.json")
    if args.csv or (not args.frab and not args.json):
        save_csv(scraped_data, f"{filename}.csv")
        print(f"Saved as {filename}.csv")
