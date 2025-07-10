#!/usr/bin/env python3
import argparse
import pandas as pd
import openai
import time
import os
from datetime import datetime

# Use your preferred model & token budget
DEFAULT_MODEL      = "gpt-3.5-turbo-16k"
DEFAULT_MAX_TOKENS = 2000

def make_multicity_prompt(trip_df: pd.DataFrame) -> str:
    """Build a single prompt covering all cities in one submission."""
    org           = trip_df.iloc[0]['org']
    start_date    = trip_df.iloc[0]['start_date']
    end_date      = trip_df.iloc[0]['end_date']
    stud_cnt      = trip_df.iloc[0]['student_count']
    grade_level   = trip_df.iloc[0]['grade_level']
    teach_cnt     = trip_df.iloc[0]['teacher_count']
    start_dt      = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt        = datetime.strptime(end_date,   '%Y-%m-%d')
    total_days    = (end_dt - start_dt).days + 1

    # Map cities → places
    city_sites = {
        row['city']: [p.strip() for p in row['places'].split(',')]
        for _, row in trip_df.iterrows()
    }

    prompt = (
        f"Plan a detailed, day-by-day **multi-city** field-trip itinerary for {org}:\n"
        f"- Dates: {start_date} → {end_date} ({total_days} days total)\n"
        f"- Group size: {stud_cnt} students (grade {grade_level}) + {teach_cnt} teachers\n\n"
        f"Cities & key sites (visit order):\n"
    )
    for city, sites in city_sites.items():
        prompt += f"  • {city}: {', '.join(sites)}\n"

    prompt += (
        "\nWhen planning, please:\n"
        "1. Sequence the cities to minimize total travel distance.\n"
        "2. Use high-speed rail for ~200–800 km hops, flights for >800 km.\n"
        "3. Include transport times on each day.\n"
        "4. Group intra-city sites geographically.\n"
        "5. Add meal breaks, rest periods, and overnight stays.\n"
        "6. Suggest one backup activity per city for bad weather.\n"
        "7. Estimate per-person costs (fees, transport, meals).\n\n"
        "Output format:\n"
        "Day 1:\n"
        "  - Morning (8:00–12:00): …\n"
        "  - Lunch (12:00–13:30): …\n"
        "  - Afternoon (14:00–18:00): …\n"
        "  - Evening/Travel (18:00–21:00): …\n\n"
        f"Continue through Day {total_days}, including any inter-city legs."
    )
    return prompt

def generate_itinerary(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> str:
    """Call OpenAI ChatCompletion and return the itinerary text."""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    for attempt in range(1, max_retries+1):
        try:
            resp = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role":"system", "content":"You are a helpful trip planner."},
                    {"role":"user",   "content":prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[itinerary] Attempt {attempt} failed: {e}")
            time.sleep(2)
    return "[Error generating itinerary]"

def generate_itinerary_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: exploded DataFrame from cleaning.py (1 row per city).
    Output: one row per trip, with aggregated cities/places and itinerary text.
    """
    trips = df.groupby(['email','submitted_at'], sort=False)
    results = []
    for (email, submitted_at), group in trips:
        prompt = make_multicity_prompt(group)
        text   = generate_itinerary(prompt)
        row0   = group.iloc[0]

        results.append({
            'first_name':    row0['first_name'],
            'last_name':     row0['last_name'],
            'email':         email,
            'org':           row0['org'],
            'start_date':    row0['start_date'],
            'end_date':      row0['end_date'],
            'student_count': row0['student_count'],
            'grade_level':   row0['grade_level'],
            'teacher_count': row0['teacher_count'],
            'submitted_at':  submitted_at,
            'cities':        ', '.join(group['city'].tolist()),
            'places':        ', '.join(group['places'].tolist()),
            'itinerary':     text
        })
        time.sleep(1)

    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-city itineraries from cleaned CSV"
    )
    parser.add_argument("input_csv",  help="Output of cleaning.py")
    parser.add_argument("output_csv", help="Where to save itinerary CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    out = generate_itinerary_df(df)
    out.to_csv(args.output_csv, index=False)
    print(f"[itinerary] Wrote itinerary → {args.output_csv}")

if __name__ == "__main__":
    main()
