#!/usr/bin/env python3
import argparse
import pandas as pd

def clean_csv(df: pd.DataFrame) -> pd.DataFrame:
    """
    From csv_cleaning.ipynb:
      • Subset to the required columns
      • Rename to snake_case
      • Convert dates to YYYY-MM-DD
    """
    cols_to_keep = [
        'firstName', 'lastName', 'email', 'organization', 'city',
        'startDate', 'endDate', 'places', 'studentCount',
        'gradeLevel', 'teacherCount', 'submittedAt'
    ]
    df_clean = df[cols_to_keep].copy()

    df_clean.rename(columns={
        'firstName':    'first_name',
        'lastName':     'last_name',
        'email':        'email',
        'organization': 'org',
        'city':         'city',
        'startDate':    'start_date',
        'endDate':      'end_date',
        'places':       'places',
        'studentCount': 'student_count',
        'gradeLevel':   'grade_level',
        'teacherCount': 'teacher_count',
        'submittedAt':  'submitted_at'
    }, inplace=True)

    df_clean.reset_index(drop=True, inplace=True)
    df_clean['start_date'] = pd.to_datetime(df_clean['start_date']).dt.strftime('%Y-%m-%d')
    df_clean['end_date']   = pd.to_datetime(df_clean['end_date']).dt.strftime('%Y-%m-%d')
    return df_clean

def main():
    parser = argparse.ArgumentParser(
        description="Clean raw trip CSV into a standardized format"
    )
    parser.add_argument("input_csv",  help="Path to raw input CSV")
    parser.add_argument("output_csv", help="Path to write cleaned CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    cleaned = clean_csv(df)
    cleaned.to_csv(args.output_csv, index=False)
    print(f"[cleaning] Cleaned data → {args.output_csv}")

if __name__ == "__main__":
    main()
