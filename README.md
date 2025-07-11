# 🧳 Trip Itinerary & Budget Generator

This tool helps you **generate multi-city trip itineraries and detailed budgets** based on a simple CSV submission.  

<img width="1817" height="620" alt="image" src="https://github.com/user-attachments/assets/9954578c-ef22-4807-b626-15fa1207ed60" />


---

## 🚀 How to Use (Streamlit App)

1. **Go to the web app**: [Click here to open](https://tripitinerarybudget.streamlit.app/)  
2. **Upload your raw CSV file**
   - It should contain fields like `firstName`, `lastName`, `Cities`, and `Placesbycity`
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

  <img width="1422" height="264" alt="image" src="https://github.com/user-attachments/assets/068972ac-66c0-4e54-aeeb-014a2b19e460" />

- **Detailed daily itinerary**

  <img width="760" height="659" alt="image" src="https://github.com/user-attachments/assets/1eca2c4a-47bb-4dff-98bf-9e72610c859c" />

- **Complete budget** including:
  - Hotels
  - Meals
  - Attraction tickets (using live LLM lookup)
  - Transport (bus + inter-city transfers)
  - Final total cost shown in **USD and RMB**
  <img width="1420" height="672" alt="image" src="https://github.com/user-attachments/assets/e9e21244-d180-462f-83bb-441d8f36b161" />


---

## 💸 How the Budget Is Calculated

The system automatically calculates **a detailed trip budget** based on the group size, trip length, and destination details. Here's how:

### 1. Hotel Costs
- 2 students share 1 room
- Each teacher gets their own room
- **Rate:** ¥450 RMB per room per night

### 2. Meal Costs
- Everyone eats 2 meals per day (lunch + dinner)
- **Rate:** ¥150 RMB per meal per person

### 3. Attraction Tickets
- LLM (ChatGPT) estimates typical ticket prices per place
- Student and adult prices are calculated separately
- If free, it's listed as ¥0

### 4. Bus Rental
- One bus rented per day of the trip
- **Rate:** ¥1,500 RMB per day per bus

### 5. Inter-City Transfers
- ¥950 RMB per person for each city-to-city transfer
- Automatically counts the number of hops between cities

### 6. Total in RMB and USD
- All costs are summed in **RMB**
- Also shown in **USD** using a fixed rate:
> 💱 **1 USD = 7.2 RMB**

---

## Openai API key
- Itinerary and ticket pricing rely on the OpenAI API.
- Make sure to set your OpenAI API key via Streamlit secrets.
  OPENAI_API_KEY = "sk-..."


