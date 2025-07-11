# 🧳 Trip Itinerary & Budget Generator

This tool helps you **generate multi-city trip itineraries and detailed budgets** based on a simple CSV submission.  

---

## 🚀 How to Use (Streamlit App)

1. **Go to the web app**: [Click here to open](https://tripitinerarybudget.streamlit.app/)  
2. **Upload your raw CSV file**
   - It should contain fields like `firstName`, `lastName`, `Cities`, and `Placesbycity` (example format provided below)
   - The original csv file is downloaded from Wix "tripsubmissions" collection
3. Wait a moment while the system:
   - Cleans the data
   - Generates the trip itinerary
   - Calculates the full budget
4. **Download the results**
   - `itinerary.csv`: Full daily schedule for the trip
   - `budget.csv`: Cost breakdown (in RMB and USD)

---

## 🧾 What You Get

- **Cleaned data preview**
- **Detailed daily itinerary**
- **Complete budget** including:
  - Hotels
  - Meals
  - Attraction tickets (using live LLM lookup)
  - Transport (bus + inter-city transfers)
  - Final total cost shown in **USD and RMB**

---

## 💸 How the Budget Is Calculated

The system automatically calculates **a detailed trip budget** based on the group size, trip length, and destination details. Here's how:

### ✅ 1. Hotel Costs
- 2 students share 1 room
- Each teacher gets their own room
- **Rate:** ¥450 RMB per room per night

### ✅ 2. Meal Costs
- Everyone eats 2 meals per day (lunch + dinner)
- **Rate:** ¥150 RMB per meal per person

### ✅ 3. Attraction Tickets
- LLM (ChatGPT) estimates typical ticket prices per place
- Student and adult prices are calculated separately
- If free, it's listed as ¥0

### ✅ 4. Bus Rental
- One bus rented per day of the trip
- **Rate:** ¥1,500 RMB per day per bus

### ✅ 5. Inter-City Transfers
- ¥950 RMB per person for each city-to-city transfer
- Automatically counts the number of hops between cities

### ✅ 6. Total in RMB and USD
- All costs are summed in **RMB**
- Also shown in **USD** using a fixed rate:
> 💱 **1 USD = 7.2 RMB**

---

## Input CSV format
firstName,lastName,email,organization,Cities,Placesbycity,startDate,endDate,studentCount,teacherCount,gradeLevel,submittedAt
Muyao,Zi,example@email.com,Student,"Beijing,Chengdu,Xi'an","[{""city"":""Beijing"",""places"":[""Great Wall"",""Temple of Heaven""]},{""city"":""Chengdu"",""places"":[""Panda Base""]},{""city"":""Xi'an"",""places"":[""Big Goose Pagoda""]}]",2025-07-11,2025-07-15,30,3,7,2025-06-30

## Openai API key
- Itinerary and ticket pricing rely on the OpenAI API.
- Make sure to set your OpenAI API key via Streamlit secrets.
  OPENAI_API_KEY = "sk-..."


