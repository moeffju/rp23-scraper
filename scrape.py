import csv
import requests
from bs4 import BeautifulSoup

base_url = "https://re-publica.com/de/sessions?page="
last_page = 30

# Open a CSV file for writing
with open("session_data.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    
    # Write the header row
    writer.writerow([
        "Session Title",
        "Speakers",
        "Info",
        "Tags",
        "Room",
        "Start",
        "End",
        "Format",
        "Language",
        "Translation"
    ])

    for page in range(last_page + 1):
        url = base_url + str(page)
        print(f"Fetching page {page} from {url} ", end="")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        session_articles = soup.find_all("article")

        for article in session_articles:
            print(".", end='')
            # Extract session data from the article tag
            session_title_elem = article.find("h2", class_="node__title")
            session_title = session_title_elem.text.strip() if session_title_elem else ""

            session_speakers_elem = article.select("p.big-speaker-list a")
            session_speakers = [a.text for a in session_speakers_elem]

            session_info_elem = article.find("div", class_="field__item")
            session_info = session_info_elem.text.strip() if session_info_elem else ""

            session_tags_elem = article.select("div.field--name-field-tag-additional a")
            session_tags = [a.text for a in session_tags_elem]

            session_room_elem = article.find("div", class_="field--name-field-room")
            session_room = session_room_elem.text.strip() if session_room_elem else ""

            session_dates = article.select("div.field--name-field-date time")
            session_start = session_dates[0]["datetime"] if session_dates else ""
            session_end = session_dates[1]["datetime"] if len(session_dates) > 1 else ""

            session_format_elem = article.find("div", class_="field--name-field-format")
            session_format = session_format_elem.text.strip() if session_format_elem else ""

            session_language_elem = article.find("div", class_="field--name-field-language")
            session_language = session_language_elem.text.strip() if session_language_elem else ""

            session_translation_elem = article.find("div", class_="field--name-field-translation")
            session_translation = session_translation_elem.text.strip() if session_translation_elem else ""

            # Write session data to the CSV file
            writer.writerow([
                session_title,
                ", ".join(session_speakers),
                session_info,
                ", ".join(session_tags),
                session_room,
                session_start,
                session_end,
                session_format,
                session_language,
                session_translation
            ])

        print("")
