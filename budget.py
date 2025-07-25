#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import re, json, time, os
import openai
from math import ceil

# Rates & constants
FIXED_HOTEL_RATE   = 450    # RMB / room-night
BUS_RATE_PER_DAY   = 1500   # RMB / day
MEAL_RATE          = 150    # RMB / meal
TRANSFER_RATE      = 950    # RMB / person-transfer

# 1) Split places helper (reused)
def split_places(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,，；]", s) if p.strip()]

# 2) Ticket-price lookup (LLM)
def fetch_ticket_price_llm(place: str, retries: int = 2) -> dict:
    system = (
        "You are a tourism data assistant. Return JSON with "
        "'adult' and 'student' admission prices in RMB, or 0 if free."
    )
    user = f"For “{place}”, what are the current admission prices (RMB) for adult & student? JSON only."
    openai.api_key = os.getenv("OPENAI_API_KEY")
    for _ in range(retries+1):
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            temperature=0.0, max_tokens=120
        )
        txt = resp.choices[0].message.content
        m = re.search(r"\{.*?\}", txt, re.DOTALL)
        if m:
            js = m.group(0).replace("'",'"')
            js = re.sub(r",\s*}", "}", js)
            try:
                data = json.loads(js)
                return {"adult":float(data.get("adult",0)),
                        "student":float(data.get("student",0))}
            except:
                pass
        time.sleep(1)
    return {"adult":0.0,"student":0.0}

# 3) Attraction breakdown (per-place)
def compute_attraction_breakdown(places_str: str,
                                 stud_cnt: int,
                                 adult_cnt: int) -> pd.DataFrame:
    places = split_places(places_str)
    cache  = {pl: fetch_ticket_price_llm(pl) for pl in places}

    rows = []
    for pl in places:
        p  = cache[pl]
        st = p["student"] * stud_cnt
        at = p["adult"]   * adult_cnt
        rows.append({
            "place":             pl,
            "student_unit_price": p["student"],
            "student_count":      stud_cnt,
            "student_total":      st,
            "adult_unit_price":   p["adult"],
            "adult_count":        adult_cnt,
            "adult_total":        at,
            "attraction_total":   st + at
        })
    # summary row
    total = sum(r["attraction_total"] for r in rows)
    rows.append({
        "place":"TOTAL","student_unit_price":"","student_count":"",
        "student_total":"","adult_unit_price":"","adult_count":"",
        "adult_total":"","attraction_total":total
    })
    return pd.DataFrame(rows)

def calculate_budget(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: itinerary CSV from itinerary.py (one row per trip),
           with columns: cities, places, start_date, end_date, student_count, teacher_count.
    Output: detailed line-item DataFrame for the full trip.
    """
    # Prepare
    STUD = int(df.loc[0, 'student_count'])
    TCHR = int(df.loc[0, 'teacher_count'])
    PEOPLE = STUD + TCHR


    # Helper to count transfers from 'cities' column
    def count_transfers(cities_str):
        return max(len(cities_str.split(',')) - 1, 0)

    line_items = []

    for _, row in df.iterrows():
        trip = row['cities']
        st  = pd.to_datetime(row['start_date'])
        ed  = pd.to_datetime(row['end_date'])
        nights = (ed - st).days
        days   = nights + 1

        # 1) Hotel
        rooms = ceil(STUD/2) + TCHR
        hc = nights * rooms * FIXED_HOTEL_RATE
        line_items.append({
            "City/Trip": trip, "Category":"Hotel",
            "Item":"Room-night","Unit":"room-night",
            "Quantity": nights*rooms,
            "Unit Price (RMB)": FIXED_HOTEL_RATE,
            "Total (RMB)": hc
        })

        # 2) Meals
        meals = days * 2 * PEOPLE
        mc = meals * MEAL_RATE
        line_items.append({
            "City/Trip": trip, "Category":"Meals",
            "Item":"Meal","Unit":"meal",
            "Quantity": meals,
            "Unit Price (RMB)": MEAL_RATE,
            "Total (RMB)": mc
        })

        # 3) Attractions (per place)
        breakdown = compute_attraction_breakdown(row['places'], STUD, TCHR)
        for _, br in breakdown.iterrows():
            if br['place']=="TOTAL": continue
            # student
            line_items.append({
                "City/Trip": trip, "Category":"Attraction",
                "Item":f"{br['place']} (student)","Unit":"ticket",
                "Quantity": br['student_count'],
                "Unit Price (RMB)": br['student_unit_price'],
                "Total (RMB)": br['student_total']
            })
            # adult
            line_items.append({
                "City/Trip": trip, "Category":"Attraction",
                "Item":f"{br['place']} (adult)","Unit":"ticket",
                "Quantity": br['adult_count'],
                "Unit Price (RMB)": br['adult_unit_price'],
                "Total (RMB)": br['adult_total']
            })

        # 4) Bus rental
        brc = days * BUS_RATE_PER_DAY
        line_items.append({
            "City/Trip": trip, "Category":"Transport",
            "Item":"Bus rental","Unit":"day",
            "Quantity": days,
            "Unit Price (RMB)": BUS_RATE_PER_DAY,
            "Total (RMB)": brc
        })

        # 5) Inter-city transfers
        trans = count_transfers(row['cities'])
        tc = trans * PEOPLE * TRANSFER_RATE
        line_items.append({
            "City/Trip": trip, "Category":"Transport",
            "Item":"Inter-city transfer","Unit":"person-transfer",
            "Quantity": trans * PEOPLE,
            "Unit Price (RMB)": TRANSFER_RATE,
            "Total (RMB)": tc
        })

    # Assemble and append GRAND TOTAL row
    detailed = pd.DataFrame(line_items)

    # Fixed exchange rate
    EXCHANGE_RATE = 7.2
    detailed['Total (USD)'] = detailed['Total (RMB)'] / EXCHANGE_RATE

    grand_rmb = detailed['Total (RMB)'].sum()
    grand_usd = detailed['Total (USD)'].sum()
    
    avg_per_person = total / (row["student_count"] + row["teacher_count"])
    avg_per_student = total / row["student_count"]
    avg_per_person_usd  = grand_usd / PEOPLE
    avg_per_student_usd = grand_usd / STUD


    total_row = {
        "City/Trip": "GRAND TOTAL", "Category": "", "Item": "", "Unit": "",
        "Quantity": "", "Unit Price (RMB)": "", "Total (RMB)": grand_rmb,
        "Total (USD)": grand_usd,
        "Avg per Person (USD)": avg_per_person_usd,
        "Avg per Student (USD)": avg_per_student_usd
     }

    detailed = pd.concat([detailed, pd.DataFrame([total_row])], ignore_index=True)
    return detailed

def main():
    parser = argparse.ArgumentParser(
        description="Calculate detailed budget from multi-city itinerary CSV"
    )
    parser.add_argument("input_csv",  help="Itinerary CSV (output of itinerary.py)")
    parser.add_argument("output_csv", help="Where to save the budget CSV")
    args = parser.parse_args()

    itin = pd.read_csv(args.input_csv)
    out  = calculate_budget(itin)
    out.to_csv(args.output_csv, index=False)
    print(f"[budget] Wrote detailed budget → {args.output_csv}")

if __name__ == "__main__":
    main()
