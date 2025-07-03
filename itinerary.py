#!/usr/bin/env python3
import argparse
import pandas as pd
import openai
import time
import os
from datetime import datetime, timedelta

openai.api_key = os.getenv("OPENAI_API_KEY", None)

def make_prompt(row) -> str:
    """
    Build the day-by-day itinerary prompt exactly as in your Colab.
    """
    start = datetime.strptime(row['start_date'], '%Y-%m-%d')
    end   = datetime.strptime(row['end_date'],   '%Y-%m-%d')
    num_days = (end - start).days + 1

    return (
        f"Plan a detailed, day-by-day field-trip itinerary for a group from {row['org']}:\n"
        f"- Trip dates: {row['start_date']} through {row['end_date']} ({num_days} days)\n"
        f"- Destination city: {row['city']}, China\n"
        f"- Group size: {row['student_count']} students (grade {row['grade_level']}) + "
        f"{row['teacher_count']} teachers\n"
        f"- Key sites: {row['places']}\n\n"
        "When crafting the plan, please consider and explicitly specify:\n"
        "1. Logical travel sequence & transit times\n"
        "2. Opening hours and recommended visit durations\n"
        "3. Built-in meal breaks and rest periods\n"
        "4. Weather-appropriate alternatives or indoor backups\n"
        "5. Rough per-person cost estimates (entrance fees, transport)\n\n"
        "Output format:\n"
        "Day 1:\n"
        "  - Morning: [Activity], [Location], transit details, visit duration\n"
        "  - Lunch: [Suggested restaurant or picnic]\n"
        "  - Afternoon: [Activity], [Location], transit details\n"
        "  - Evening: [Summary or downtime suggestion]\n\n"
        f"(Continue through Day {num_days}.)"
    )

def generate_itinerary(prompt: str,
                       model: str = "gpt-3.5-turbo",
                       max_retries: int = 3) -> str:
    """
    Call OpenAI to get the itinerary text.
    Retries up to max_retries on error.
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful trip planner."},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
            )
            text = resp.choices[0].message.content
            if text:
                return text.strip()
        except Exception as e:
            print(f"[itinerary] Attempt {attempt} failed: {e}")
            time.sleep(2)
    return "[Error generating itinerary]"

def generate_itinerary_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row in the cleaned DataFrame, build a prompt,
    call the LLM, and collect results into a new DataFrame.
    """
    results = []
    for _, row in df.iterrows():
        prompt = make_prompt(row)
        itinerary_text = generate_itinerary(prompt)
        results.append({
            "first_name":    row['first_name'],
            "last_name":     row['last_name'],
            "email":         row['email'],
            "org":           row['org'],
            "city":          row['city'],
            "places":        row['places'],
            "start_date":    row['start_date'],
            "end_date":      row['end_date'],
            "student_count": row['student_count'],
            "grade_level":   row['grade_level'],
            "teacher_count": row['teacher_count'],
            "itinerary":     itinerary_text
        })
        time.sleep(1)  # avoid rate limits
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(
        description="Generate trip itinerary from cleaned CSV"
    )
    parser.add_argument("input_csv",  help="Cleaned CSV from step 1")
    parser.add_argument("output_csv", help="Where to save generated itinerary CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    itin_df = generate_itinerary_df(df)
    itin_df.to_csv(args.output_csv, index=False)
    print(f"[itinerary] Saved itinerary CSV → {args.output_csv}")

if __name__ == "__main__":
    main()
