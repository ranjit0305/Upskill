import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import sys
import os

# Add the current directory to sys.path to import app models
sys.path.append(os.getcwd())

from app.models.assessment import Question, QuestionType, DifficultyLevel

async def seed_aptitude_questions():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client.upskill_db
    await init_beanie(database=database, document_models=[Question])

    zoho_apt_qs = [
        # Time and Work
        {"text": "A can do a piece of work in 15 days and B in 20 days. They work together for 4 days. Fraction of work left?", "options": ["1/4", "7/15", "8/15", "1/10"], "ans": "8/15", "cat": "time_and_work"},
        {"text": "A, B, C can do work in 20, 30, 60 days. In how many days can A do it if assisted by B and C every 3rd day?", "options": ["12", "15", "16", "18"], "ans": "15", "cat": "time_and_work"},
        {"text": "A is thrice as efficient as B and finishes a work in 60 days less than B. Working together, they finish in?", "options": ["20", "22.5", "25", "30"], "ans": "22.5", "cat": "time_and_work"},
        {"text": "10 men can complete a work in 7 days. How many more men are needed to finish it in 5 days?", "options": ["2", "4", "5", "10"], "ans": "4", "cat": "time_and_work"},
        {"text": "A and B together can do work in 8 days. B alone in 12 days. A alone takes?", "options": ["16", "20", "24", "30"], "ans": "24", "cat": "time_and_work"},
        
        # Profit and Loss
        {"text": "Gain percent when CP is $80 and SP is $100?", "options": ["20%", "25%", "30%", "15%"], "ans": "25%", "cat": "profit_and_loss"},
        {"text": "A toy bought for $200 and sold for $180. Loss %?", "options": ["5%", "10%", "15%", "20%"], "ans": "10%", "cat": "profit_and_loss"},
        {"text": "A man buys 10 oranges for $3 and sells 8 for $3. Gain %?", "options": ["20%", "25%", "30%", "15%"], "ans": "25%", "cat": "profit_and_loss"},
        {"text": "Cost price of 20 articles is SP of 15 articles. Profit %?", "options": ["33.33%", "25%", "20%", "50%"], "ans": "33.33%", "cat": "profit_and_loss"},
        {"text": "If selling price is doubled, profit triples. Find profit %.", "options": ["100%", "200%", "50%", "150%"], "ans": "100%", "cat": "profit_and_loss"},
        
        # Speed, Distance, Time
        {"text": "A train 240m long passes a pole in 24s. Time to pass platform 650m long?", "options": ["89s", "100s", "150s", "50s"], "ans": "89s", "cat": "speed_distance_time"},
        {"text": "Person crosses 600m long street in 5 mins. Speed in km/hr?", "options": ["7.2", "3.6", "8.4", "10"], "ans": "7.2", "cat": "speed_distance_time"},
        {"text": "Ratio of speeds of two trains is 7:8. If 2nd train runs 400km in 5 hrs, speed of 1st?", "options": ["70 km/hr", "80 km/hr", "75 km/hr", "84 km/hr"], "ans": "70 km/hr", "cat": "speed_distance_time"},
        {"text": "Man walking at 3/4th of his usual speed reaches 20 mins late. Usual time?", "options": ["60 min", "80 min", "45 min", "30 min"], "ans": "60 min", "cat": "speed_distance_time"},
        {"text": "Average speed of car during trip of 200km in 4 hrs?", "options": ["40 km/hr", "50 km/hr", "60 km/hr", "80 km/hr"], "ans": "50 km/hr", "cat": "speed_distance_time"},
        
        # Logical Reasoning / Series
        {"text": "Series: 7, 10, 8, 11, 9, 12, ... Next number?", "options": ["10", "13", "7", "11"], "ans": "10", "cat": "logical_reasoning"},
        {"text": "SCD, TEF, UGH, ____, WKL", "options": ["CMN", "UJI", "VIJ", "IJT"], "ans": "VIJ", "cat": "logical_reasoning"},
        {"text": "Series: 2, 1, (1/2), (1/4), ... Next?", "options": ["1/3", "1/8", "2/8", "1/16"], "ans": "1/8", "cat": "logical_reasoning"},
        {"text": "FAG, GAF, HAI, IAH, ____", "options": ["JAK", "HAL", "HAK", "JAI"], "ans": "JAK", "cat": "logical_reasoning"},
        {"text": "Series: 31, 29, 24, 22, 17, ... Next?", "options": ["15", "14", "13", "12"], "ans": "15", "cat": "logical_reasoning"},
        
        # Percentages
        {"text": "What is 15% of 34 kg?", "options": ["3.4 kg", "5.1 kg", "5 kg", "4.5 kg"], "ans": "5.1 kg", "cat": "percentages"},
        {"text": "If 20% of a = b, then b% of 20 is same as?", "options": ["4% of a", "5% of a", "20% of a", "None"], "ans": "4% of a", "cat": "percentages"},
        {"text": "In an election, 2 candidates got 40% and 60% votes. Winner wins by 1600 votes. Total votes?", "options": ["8000", "4000", "10000", "6000"], "ans": "8000", "cat": "percentages"},
        {"text": "Price of sugar rises 20%. By how much % should consumption decrease to keep same expenditure?", "options": ["16.66%", "20%", "25%", "10%"], "ans": "16.66%", "cat": "percentages"},
        {"text": "40% of 280 + 18% of 550 = ?", "options": ["211", "200", "198", "215"], "ans": "211", "cat": "percentages"},
        
        # Probability
        {"text": "Probability of getting a sum of 7 when two dice are thrown?", "options": ["1/6", "1/12", "5/36", "7/36"], "ans": "1/6", "cat": "probability"},
        {"text": "A card is drawn from a pack of 52. Probability that it is a spade or a king?", "options": ["4/13", "17/52", "1/4", "13/52"], "ans": "4/13", "cat": "probability"},
        {"text": "Two coins are tossed. Probability of getting at most one head?", "options": ["3/4", "1/4", "1/2", "1/3"], "ans": "3/4", "cat": "probability"},
        {"text": "A bag contains 6 black and 8 white balls. One ball is drawn. Probability it is white?", "options": ["3/4", "4/7", "1/8", "3/7"], "ans": "4/7", "cat": "probability"},
        {"text": "Probability a non-leap year has 53 Sundays?", "options": ["1/7", "2/7", "53/365", "0"], "ans": "1/7", "cat": "probability"},
        
        # Simple Interest
        {"text": "SI on $5000 at 10% for 2 years?", "options": ["$1000", "$500", "$1500", "$2000"], "ans": "$1000", "cat": "simple_interest"},
        {"text": "Sum of money doubles in 10 years SI. Rate of interest?", "options": ["10%", "5%", "12.5%", "20%"], "ans": "10%", "cat": "simple_interest"},
        {"text": "In how many years will $8000 become $9200 at 5% SI?", "options": ["3", "4", "5", "2"], "ans": "3", "cat": "simple_interest"},
        {"text": "$6400 yields $1152 as interest in 3 years. Rate?", "options": ["6%", "7%", "8%", "9%"], "ans": "6%", "cat": "simple_interest"},
        {"text": "A sum fetched $4016.25 as SI at 9% in 5 years. Sum?", "options": ["$8925", "$8032.5", "$9000", "$8500"], "ans": "$8925", "cat": "simple_interest"},
        
        # Average
        {"text": "Average of first 50 natural numbers?", "options": ["25.5", "25", "26", "25.25"], "ans": "25.5", "cat": "average"},
        {"text": "Average of 7 consecutive numbers is 20. Largest number?", "options": ["24", "23", "20", "26"], "ans": "23", "cat": "average"},
        {"text": "Average age of 30 students is 15. If teacher's age included, it becomes 16. Teacher's age?", "options": ["46", "31", "45", "40"], "ans": "46", "cat": "average"},
        {"text": "The weight of 10 people increased by 1.8kg when one weighing 53kg is replaced by new. New weight?", "options": ["71", "61", "70", "72"], "ans": "71", "cat": "average"},
        {"text": "Average of five numbers is 27. If one is excluded, average is 25. Excluded number?", "options": ["35", "27", "30", "25"], "ans": "35", "cat": "average"},

        # Pipes and Cisterns
        {"text": "Two pipes fill a tank in 20 and 30 mins. Both together fill in?", "options": ["12 min", "15 min", "25 min", "10 min"], "ans": "12 min", "cat": "pipes_and_cisterns"},
        {"text": "Pipe A fills in 10 hrs, B in 15 hrs. Both in?", "options": ["6", "7", "8", "5"], "ans": "6", "cat": "pipes_and_cisterns"},
        {"text": "Pipe can fill tank in 8 hrs. Due to leak, it takes 10 hrs. Leak empties full tank in?", "options": ["40 hr", "30 hr", "20 hr", "45 hr"], "ans": "40 hr", "cat": "pipes_and_cisterns"},
        {"text": "A can fill in 6 hrs, B in 8 hrs. Both open for 2 hrs, then A closed. B fills rest in?", "options": ["10/3 hr", "21/4 hr", "15/4 hr", "18/5 hr"], "ans": "10/3 hr", "cat": "pipes_and_cisterns"},
        {"text": "Pipes A and B fill in 12 and 15 mins. C empties in 6 mins. If A and B open for 5 mins then C opened. Tank empties in?", "options": ["45 min", "30 min", "60 min", "20 min"], "ans": "45 min", "cat": "pipes_and_cisterns"},

        # Numbers and Ages
        {"text": "Sum of ages of 5 children born at intervals of 3 years each is 50. Age of youngest?", "options": ["4", "8", "10", "None"], "ans": "4", "cat": "numbers_and_ages"},
        {"text": "Father is 3 times as old as son. In 15 years, he will be twice. Father's age?", "options": ["45", "30", "60", "36"], "ans": "45", "cat": "numbers_and_ages"},
        {"text": "Ratio of ages of A and B is 4:5. Sum is 36. Age of A?", "options": ["16", "20", "24", "18"], "ans": "16", "cat": "numbers_and_ages"},
        {"text": "A is 2 years older than B who is twice as old as C. If sum is 27, age of B?", "options": ["10", "9", "8", "11"], "ans": "10", "cat": "numbers_and_ages"},
        {"text": "Present ages of X and Y are 5:6. After 7 years ratio is 6:7. X's age?", "options": ["35", "42", "49", "25"], "ans": "35", "cat": "numbers_and_ages"}
    ]

    count = 0
    for q in zoho_apt_qs:
        # Check if already exists
        existing = await Question.find_one(Question.question == q["text"])
        if not existing:
            new_q = Question(
                type=QuestionType.APTITUDE,
                category=q["cat"],
                difficulty=DifficultyLevel.MEDIUM,
                question=q["text"],
                options=q["options"],
                correct_answer=q["ans"],
                explanation="Standard aptitude question for Zoho preparation.",
                companies=["zoho"],
                is_generated=True,
                created_by="system_seeder"
            )
            await new_q.insert()
            count += 1
    
    print(f"Successfully seeded {count} new questions for Zoho.")
    await client.close()

if __name__ == "__main__":
    asyncio.run(seed_aptitude_questions())
