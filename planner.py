#!/usr/bin/env python

import csv
import sys
from datetime import datetime


if len(sys.argv) < 2:
    print("Please provide the CSV file name as a command-line argument.")
    sys.exit(1)

filename = sys.argv[1]

with open(filename, 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    records = list(reader)

# Filter records
filtered_records = list(filter(lambda record: record["room"] in ["Stage 1", "Stage 2"] and record["translation"] == "True" and record["is_partner_session"] == "False", records))

# Get list of rooms in filtered set
rooms = sorted(set(record["room"] for record in filtered_records))

# Sort records by start_datetime
sorted_records = sorted(filtered_records, key=lambda x: datetime.strptime(x["start_datetime"], "%Y-%m-%d %H:%M:%S%z"))

# Group records by room and start_time
grouped_records = {}
for record in sorted_records:
    start_date = record["start_date"]
    if start_date not in grouped_records:
        grouped_records[start_date] = {}
    start_time = record["start_time"]
    if start_time not in grouped_records[start_date]:
        grouped_records[start_date][start_time] = {}
    room = record["room"]
    if room not in grouped_records[start_date][start_time]:
        grouped_records[start_date][start_time][room] = record
    else:
        # ERROR! two sessions in the same room at the same time?!
        print("ERROR: Multiple sessions for same starting time same room!", file=sys.stderr)
        print(f"Time slot: {start_date} {start_time} in room {room}", file=sys.stderr)
        print(f"Existing data:  {repr(grouped_records[start_date][start_time][room])}", file=sys.stderr)
        print(f"Colliding data: {repr(record)}")
        pass

# Generate and print the header
per_room_header = ["url", "start_time", "duration", "title", "speakers", "language", "type", "INT_1", "INT_2"]
room_header = [f"{room}_{col}" for room in rooms for col in per_room_header]
header = ["date"] + room_header + ["bereitschaft_INT_1", "bereitschaft_INT_2"]

# Output sessions for each room aligned by start time
writer = csv.writer(sys.stdout)
writer.writerow(header)

# Keep track of blocks we've seen to add spacers
last_seen_day = None
last_seen_hour = None

# Output sessions for each room aligned by start time
for start_date, time_rooms_map in grouped_records.items():
    # find day stats
    row = [start_date]
    for room in rooms:
        day_start_time = min([time_rooms_map[time][room]['start_time'] for time in time_rooms_map if room in time_rooms_map[time]])
        day_end_time = max([time_rooms_map[time][room]['end_time'] for time in time_rooms_map if room in time_rooms_map[time]])
        row.extend([f"{room} first session starts {day_start_time}, last session ends {day_end_time}"])
        row.extend(["" for i in range(len(per_room_header)-1)])
    writer.writerow(row)
    # output sessions of the day
    for start_time, rooms_records in time_rooms_map.items():
        current_hour = start_time.split(':')[0]
        if current_hour != last_seen_hour:
            # Add spacer
            writer.writerow([])
        row = [start_date]
        for room in rooms:
            if room in rooms_records:
                row.extend([rooms_records[room].get(col, "") for col in per_room_header])
            else:
                row.extend(["" for col in per_room_header])
        row.extend(["", ""])  # bereitschaft
        writer.writerow(row)
        last_seen_hour = current_hour
    # empty line after every day
    writer.writerow([])
