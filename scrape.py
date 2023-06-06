#!/usr/bin/env python

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
LANGUAGE = "de"
DATA_URL = f"{BASE_URL}/{LANGUAGE}/sessions"
FIRST_DAY = "2023-06-05"
LAST_DAY = "2023-06-07"
TZ_NAME = "Europe/Berlin"
TZ = tz.gettz(TZ_NAME)


def get_page_count():
    response = requests.get(DATA_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    pagination = soup.find("nav", class_="pager layout--content-medium")
    last_page_elem = pagination.find("li", class_="pager__item--last")
    last_page_url = last_page_elem.find("a")["href"]
    last_page_number = parse_qs(urlparse(last_page_url).query)["page"][0]
    last_page = int(last_page_number)
    return last_page


def scrape_republica_page(page):
    url = f"{DATA_URL}?page={page}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    articles = soup.find_all("article", class_="node--type-session-conference")
    data = []
    for article in articles:
        session_title_element = article.find("h2", class_="node__title")
        session_title = session_title_element.text.strip()
        session_url = session_title_element.find("a").get("href")
        # session_id = re.search(r"\d+", session_url).group() if session_url else ""
        session_id = 0
        session_cancelled = "rp-cancelled" in article["class"]
        session_speakers = [
            {
                "id": int(re.search(r"\d+", speaker.get("href")).group()),
                "public_name": speaker.text.strip()
            }
            for speaker in article.find("p", class_="big-speaker-list").find_all("a")
        ]
        session_description = article.find("div", class_="field--name-field-teaser").find("div", class_="field__item").text.strip()
        session_tag = article.find("div", class_="field--name-field-tag").find("a").text.strip()
        session_room_element = article.find("div", class_="field--name-field-room")
        session_room = session_room_element.text.strip() if session_room_element else ""
        session_date_element = article.find("div", class_="field--name-field-date")
        if session_date_element:
            session_date_start = datetime.fromisoformat(session_date_element.find_all("time")[0].get("datetime")).astimezone(tz=TZ)
            session_date_end = datetime.fromisoformat(session_date_element.find_all("time")[1].get("datetime")).astimezone(tz=TZ)
        else:
            session_date_start = datetime.fromisoformat(f"{FIRST_DAY}T06:00:00Z").astimezone(tz=TZ)
            session_date_end = datetime.fromisoformat(f"{LAST_DAY}T16:00:00Z").astimezone(tz=TZ)
        session_format = article.find("div", class_="field--name-field-format").text.strip()
        session_language = article.find("div", class_="field--name-field-language").text.strip()[:2].lower()
        session_translation_element = article.find("div", class_="field--name-field-translation")
        session_translation = session_translation_element.text.strip() != "" if session_translation_element else False

        session_duration = session_date_end - session_date_start
        session_duration_hours, _seconds = divmod(session_duration.seconds, 3600)
        session_duration_minutes = _seconds // 60

        is_partner_session = article.find("span", class_="session-has-partner") is not None

        session_data = {
            "url": f"{BASE_URL}{session_url}",
            "id": int(session_id),
            "start_datetime": session_date_start,
            "start_date": session_date_start.strftime("%Y-%m-%d"),
            "start_time": session_date_start.strftime("%H:%M"),
            "end_datetime": session_date_end,
            "end_date": session_date_end.strftime("%Y-%m-%d"),
            "end_time": session_date_end.strftime("%H:%M"),
            "duration": f"{session_duration_hours}:{session_duration_minutes:02}",
            "room": session_room,
            "slug": generate_slug(session_title),
            "title": session_title,
            "persons": session_speakers,
            "track": session_tag,
            "type": session_format,
            "language": session_language,
            "abstract": shorten_description(session_description),
            "description": session_description,
            "translation": session_translation,
            "translation_derived": (session_room in ["Stage 1", "Stage 2"] and not is_partner_session),
            "is_partner_session": is_partner_session,
            "is_cancelled": session_cancelled,
        }
        data.append(session_data)

    return data


def generate_slug(title):
    slug = re.sub(r"[^\w\d]+", "-", title)
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
    sentences = re.split(r'[.:!?]\s+', description)
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

    last_page = get_page_count()
    print(f"Scraping {last_page+1} pages from {DATA_URL}...")

    scraped_data = []
    for page in range(last_page + 1):
        print(f"\rPage {page+1}/{last_page+1}", end="")
        scraped_data.extend(scrape_republica_page(page))
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
