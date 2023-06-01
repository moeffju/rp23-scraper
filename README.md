# rp23-scraper

Downloads sessions for re:publica 2023 conference and outputs the data in a machine-readable form, either:

* CSV (`--csv`, the default),
* JSON (`--json`), plain dump containing the most data, or
* Frab Json (`--frab`), a JSON file in (mostly) [https://github.com/frab/frab] format

Usage:

    ./scrape.py [--csv] [--frab] [--json]

You can pass multiple format arguments at once.

## Example Output

### CSV format

```csv
url,start_datetime,start_date,start_time,end_datetime,end_date,end_time,duration,room,slug,title,track,type,language,abstract,description,translation,speakers
https://re-publica.com/de/session/welcome-everybody-its-republica-time,2023-06-05 10:30:00+02:00,2023-06-05,10:30,2023-06-05 11:15:00+02:00,2023-06-05,11:15,0:45,Stage 1,welcome-everybody-it-s-re-publica-time,Welcome everybody - it's re:publica time!,This is FUN.,Vortrag,de,"Welcome back to re:publica 23!
We are looking forward to three fantastic days with you.","Welcome back to re:publica 23!
We are looking forward to three fantastic days with you.",Yes,"Andreas Gebhard, Markus Beckedahl, Tanja Haeusler, Johnny Haeusler"
```

| url | start_datetime | start_date | start_time | end_datetime | end_date | end_time | duration | room | slug | title | track | type | language | abstract | description | translation | speakers |
| --- | -------------- | ---------- | ---------- | ------------ | -------- | -------- | -------- | ---- | ---- | ----- | ----- | ---- | -------- | -------- | ----------- | ------------ | -------- |
| [https://re-publica.com/de/session/welcome-everybody-its-republica-time](https://re-publica.com/de/session/welcome-everybody-its-republica-time) | 2023-06-05 10:30:00+02:00 | 2023-06-05 | 10:30 | 2023-06-05 11:15:00+02:00 | 2023-06-05 | 11:15 | 0:45 | Stage 1 | welcome-everybody-it-s-re-publica-time | Welcome everybody - it's re:publica time! | This is FUN. | Vortrag | Deutsch | "Welcome back to re:publica 23!\nWe are looking forward to three fantastic days with you." | "Welcome back to re:publica 23!\nWe are looking forward to three fantastic days with you." | Yes | Andreas Gebhard, Markus Beckedahl, Tanja Haeusler, Johnny Haeusler |


### JSON format

```json
[
    {
        "url": "https://re-publica.com/de/session/welcome-everybody-its-republica-time",
        "id": 0,
        "start_datetime": "2023-06-05 10:30:00+02:00",
        "start_date": "2023-06-05",
        "start_time": "10:30",
        "end_datetime": "2023-06-05 11:15:00+02:00",
        "end_date": "2023-06-05",
        "end_time": "11:15",
        "duration": "0:45",
        "room": "Stage 1",
        "slug": "welcome-everybody-it-s-re-publica-time",
        "title": "Welcome everybody - it's re:publica time!",
        "track": "This is FUN.",
        "type": "Vortrag",
        "language": "de",
        "abstract": "Welcome back to re:publica 23!\r\nWe are looking forward to three fantastic days with you.",
        "description": "Welcome back to re:publica 23!\r\nWe are looking forward to three fantastic days with you.",
        "translation": true,
        "persons": [
            {
                "id": 10893,
                "public_name": "Andreas Gebhard"
            },
            {
                "id": 11546,
                "public_name": "Markus Beckedahl"
            },
            {
                "id": 10890,
                "public_name": "Tanja Haeusler"
            },
            {
                "id": 11007,
                "public_name": "Johnny Haeusler"
            }
        ]
    },
    ...
```

### Frab JSON

NOTE: This format adds a `translation` boolean field on each event, which regular Frab does not generate. It otherwise tries to stick to the [C3VOC schema](https://c3voc.de/schedule/schema.json) where possible. Note that IDs and GUIDs are not available.

```json
{
    "version": "2023-06-01T220142+0200-frab",
    "base_url": "https://re-publica.com/",
    "conference": {
        "acronym": "rp23",
        "title": "re:publica 2023",
        "start": "2023-06-05",
        "end": "2023-06-07",
        "daysCount": 4,
        "timeslot_duration": "00:15",
        "time_zone_name": "Europe/Berlin",
        "days": [
            {
                "index": 1,
                "date": "2023-06-05",
                "day_start": "10:30",
                "day_end": "21:53",
                "rooms": {
                    "Stage 1": [
                        {
                            "url": "https://re-publica.com/de/session/welcome-everybody-its-republica-time",
                            "id": 0,
                            "duration": "0:45",
                            "room": "Stage 1",
                            "slug": "welcome-everybody-it-s-re-publica-time",
                            "title": "Welcome everybody - it's re:publica time!",
                            "track": "This is FUN.",
                            "type": "Vortrag",
                            "language": "de",
                            "abstract": "Welcome back to re:publica 23!\r\nWe are looking forward to three fantastic days with you.",
                            "description": "Welcome back to re:publica 23!\r\nWe are looking forward to three fantastic days with you.",
                            "persons": [
                                {
                                    "id": 10893,
                                    "public_name": "Andreas Gebhard"
                                },
                                {
                                    "id": 11546,
                                    "public_name": "Markus Beckedahl"
                                },
                                {
                                    "id": 10890,
                                    "public_name": "Tanja Haeusler"
                                },
                                {
                                    "id": 11007,
                                    "public_name": "Johnny Haeusler"
                                }
                            ],
                            "start": "2023-06-05T10:30:00+02:00",
                            "guid": "https://re-publica.com/de/session/welcome-everybody-its-republica-time",
                            "logo": "",
                            "do_not_record": false,
                            "answers": [],
                            "links": [],
                            "attachments": [],
                            "recording_license": "Unknown"
                        },
                        ...
```
