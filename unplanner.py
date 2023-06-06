#!/usr/bin/env python

import csv
import sys


def filter_csv(csv_file, names):
    filtered_rows = []

    # Define the column ranges for each stage
    stage_ranges = {
        'Stage 1': (3, 13),
        'Stage 2': (13, 23),
        'Standby': (1, 2)
    }

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)

        # Skip the header rows
        for i, row in enumerate(rows):
            if row[0] == 'date':
                break

        # Iterate over the data rows
        for row in rows[i:]:
            matching_stage = None
            matching_columns = []

            # Iterate over the INT_* columns
            for j in range(len(row)):
                cell_value = row[j]
                if any(name.lower() in cell_value.lower() for name in names):
                    matching_stage = determine_stage(j, stage_ranges)
                    matching_columns = row[stage_ranges[matching_stage][0]:stage_ranges[matching_stage][1]]
                    break

            if matching_stage:
                filtered_row = [row[0], matching_stage] + matching_columns
                filtered_rows.append(filtered_row)

    return filtered_rows


def determine_stage(col_idx, stage_ranges):
    for stage, (start, end) in stage_ranges.items():
        if start <= col_idx < end:
            return stage

    return None


def output_csv(filtered_rows):
    writer = csv.writer(sys.stdout)
    writer.writerows(filtered_rows)


def output_list(filtered_rows):
    for row in filtered_rows:
        date = row[0]
        stage = row[1]
        if stage == "Standby":
            print(f"{date} - {stage}")
        else:
            time = row[3]
            duration = row[4]
            title = row[5]
            speakers = row[6]
            language = row[7]
            formatted_output = f"{date} - {stage} - {time} ({duration}) - [{language}] {title} - {speakers}"
            print(formatted_output)


if len(sys.argv) < 3:
    print("Usage: python unplanner.py <csv_file> <name1> <name2> ... [--csv]")
    sys.exit(1)

output_type = 'list'

if '--csv' in sys.argv:
    output_type = 'csv'
    sys.argv.remove('--csv')

csv_file = sys.argv[1]
names_to_filter = sys.argv[2:]

filtered_rows = filter_csv(csv_file, names_to_filter)

if output_type == 'csv':
    output_csv(filtered_rows)
else:
    output_list(filtered_rows)
