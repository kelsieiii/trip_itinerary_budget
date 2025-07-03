#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import re, json, time, os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY", None)


# Constants
GUIDES             = 1
FIXED_HOTEL_RATE   = 450   # RMB/night per room
BUS_RATE_PER_DAY   = 1500  # RMB/day
STD_MEAL_RATE      = 80    # RMB/meal
# SPEC_MEAL_RATE     = 150   # RMB/meal
GUIDE_RATE_PER_DAY = 900   # RMB/day

def split_places(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,，；]", s) if p.strip()]

def fetch_ticket_price_llm(place: str, retries: int = 2) -> dict:
    system = (
        "You are a tourism data assistant. Return admission prices in RMB "
        "for adult and student as JSON, e.g. {\"adult\":120,\"student\":60}, "
        "or {\"adult\":0,\"student\":0} if free."
    )
    user = f"For '{place}', what are the current admission prices (RMB) for adult & student? JSON only."
    for _ in range(retries + 1):
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user}
            ],
            temperature=0.0,
            max_tokens=80
        )
        txt = resp.choices[0].message.content
        m   = re.search(r"\{.*?\}", txt, re.DOTALL)
        if not m:
            time.sleep(1)
            continue
        js = m.group(0).replace("'", '"')
        js = re.sub(r",\s*}", "}", js)
        try:
            data = json.loads(js)
            return {"adult": float(data.get("adult", 0)), "student": float(data.get("student", 0))}
        except:
            time.sleep(1)
    return {"adult": 0.0, "student": 0.0}

def compute_attraction_breakdown(places_str: str, stud_cnt: int, adult_cnt: int) -> pd.DataFrame:
    places = split_places(places_str)
    cache  = {pl: fetch_ticket_price_llm(pl) for pl in places}
    rows   = []
    for pl in places:
        p      = cache[pl]
        stud_t = p["student"] * stud_cnt
        adult_t= p["adult"]   * adult_cnt
        rows.append({
            "place":              pl,
            "student_unit_price": p["student"],
            "student_count":      stud_cnt,
            "student_total":      stud_t,
            "adult_unit_price":   p["adult"],
            "adult_count":        adult_cnt,
            "adult_total":        adult_t,
            "attraction_total":   stud_t + adult_t
        })
    total = sum(r["attraction_total"] for r in rows)
    rows.append({
        "place":"TOTAL","student_unit_price":"","student_count":"",
        "student_total":"","adult_unit_price":"","adult_count":"",
        "adult_total":"","attraction_total":total
    })
    return pd.DataFrame(rows)

def calculate_budget(itin_df: pd.DataFrame) -> pd.DataFrame:
    line_items = []

    for _, row in itin_df.iterrows():
        city      = row["city"]
        start     = pd.to_datetime(row["start_date"])
        end       = pd.to_datetime(row["end_date"])
        nights    = (end - start).days
        days      = nights + 1
        stud_cnt  = int(row["student_count"])
        teach_cnt = int(row["teacher_count"])
        adult_cnt = teach_cnt + GUIDES
        rooms     = int(np.ceil(stud_cnt / 2) + teach_cnt + GUIDES)

        # Hotel
        hotel_cost = nights * rooms * FIXED_HOTEL_RATE
        line_items.append({
            "City": city, "Category":"Hotel","Item":"Room-night",
            "Unit":"room-night","Quantity":nights*rooms,
            "Unit Price (RMB)":FIXED_HOTEL_RATE,
            "Total (RMB)":hotel_cost
        })

        # Meals
        total_ppl   = stud_cnt + teach_cnt + GUIDES
        total_meals = days * 2 * total_ppl
        std_meals   = int(round(total_meals * 0.75))
        spec_meals  = total_meals - std_meals
        line_items.append({
            "City": city, "Category":"Meals","Item":"Standard meal",
            "Unit":"meal","Quantity":std_meals,
            "Unit Price (RMB)":STD_MEAL_RATE,
            "Total (RMB)":std_meals * STD_MEAL_RATE
        })
        # line_items.append({
        #     "City": city, "Category":"Meals","Item":"Special meal",
        #     "Unit":"meal","Quantity":spec_meals,
        #     "Unit Price (RMB)":SPEC_MEAL_RATE,
        #     "Total (RMB)":spec_meals * SPEC_MEAL_RATE
        # })

        # Guide
        guide_cost = days * GUIDE_RATE_PER_DAY * GUIDES
        line_items.append({
            "City": city, "Category":"Guide","Item":"Guide-day",
            "Unit":"day","Quantity":days * GUIDES,
            "Unit Price (RMB)":GUIDE_RATE_PER_DAY,
            "Total (RMB)":guide_cost
        })

        # Attractions
        breakdown = compute_attraction_breakdown(row["places"], stud_cnt, adult_cnt)
        for _, br in breakdown.iterrows():
            if br["place"] == "TOTAL":
                continue
            line_items.extend([
                {
                    "City": city, "Category":"Attraction",
                    "Item":f"{br['place']} (student)","Unit":"ticket",
                    "Quantity":br["student_count"],
                    "Unit Price (RMB)":br["student_unit_price"],
                    "Total (RMB)":br["student_total"]
                },
                {
                    "City": city, "Category":"Attraction",
                    "Item":f"{br['place']} (adult)","Unit":"ticket",
                    "Quantity":br["adult_count"],
                    "Unit Price (RMB)":br["adult_unit_price"],
                    "Total (RMB)":br["adult_total"]
                }
            ])

        # Bus rental
        bus_cost = days * BUS_RATE_PER_DAY
        line_items.append({
            "City": city, "Category":"Transport","Item":"Bus rental",
            "Unit":"day","Quantity":days,
            "Unit Price (RMB)":BUS_RATE_PER_DAY,
            "Total (RMB)":bus_cost
        })

    detailed = pd.DataFrame(line_items)
    grand    = detailed["Total (RMB)"].sum()
    total_row = {
        "City":"TOTAL","Category":"","Item":"","Unit":"",
        "Quantity":"","Unit Price (RMB)":"","Total (RMB)":grand
    }
    detailed = pd.concat([detailed, pd.DataFrame([total_row])], ignore_index=True)
    return detailed

def main():
    parser = argparse.ArgumentParser(
        description="Calculate detailed budget from itinerary CSV"
    )
    parser.add_argument("input_csv",  help="Path to itinerary CSV")
    parser.add_argument("output_csv", help="Path to write budget CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    detailed = calculate_budget(df)
    detailed.to_csv(args.output_csv, index=False)
    print(f"[budget] Saved detailed budget → {args.output_csv}")

if __name__ == "__main__":
    main()
