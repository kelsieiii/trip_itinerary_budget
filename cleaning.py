#!/usr/bin/env python3
import argparse
import pandas as pd
import json

def clean_csv(df: pd.DataFrame) -> pd.DataFrame:
    # 1) Rename to snake_case
    df = df.rename(columns={
        'firstName':    'first_name',
        'lastName':     'last_name',
        'email':        'email',
        'organization': 'org',
        'Cities':       'cities',           # JSON key column
        'startDate':    'start_date',
        'endDate':      'end_date',
        'Placesbycity': 'places_by_city',
        'studentCount': 'student_count',
        'gradeLevel':   'grade_level',
        'teacherCount': 'teacher_count',
        'submittedAt':  'submitted_at'
    })
    # 2) Format dates
    df['start_date'] = pd.to_datetime(df['start_date']).dt.strftime('%Y-%m-%d')
    df['end_date']   = pd.to_datetime(df['end_date']).dt.strftime('%Y-%m-%d')

    # 3) Explode JSON "places_by_city" → one row per city
    rows = []
    for _, r in df.iterrows():
        try:
            city_map = json.loads(r['places_by_city'])
        except Exception:
            # skip malformed
            continue
        for entry in city_map:
            rows.append({
                'first_name':    r['first_name'],
                'last_name':     r['last_name'],
                'email':         r['email'],
                'org':           r['org'],
                'city':          entry['city'],
                'places':        ', '.join(entry['places']),
                'start_date':    r['start_date'],
                'end_date':      r['end_date'],
                'student_count': r['student_count'],
                'grade_level':   r['grade_level'],
                'teacher_count': r['teacher_count'],
                'submitted_at':  r['submitted_at']
            })
    return pd.DataFrame(rows)

def main():
    parser = argparse.ArgumentParser(
        description="Clean raw trip CSV into an exploded, per-city format"
    )
    parser.add_argument("input_csv",  help="Path to raw submissions CSV")
    parser.add_argument("output_csv", help="Where to save the cleaned CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    cleaned = clean_csv(df)
    cleaned.to_csv(args.output_csv, index=False)
    print(f"[cleaning] Wrote cleaned CSV → {args.output_csv}")

if __name__ == "__main__":
    main()
