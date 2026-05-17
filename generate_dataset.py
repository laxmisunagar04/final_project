import pandas as pd
import random

data = []

for i in range(120):

    cgpa = round(random.uniform(5.0, 9.5), 2)
    coding = random.randint(30, 100)
    projects = random.randint(0, 5)
    internships = random.randint(0, 3)
    communication = random.randint(3, 10)

    score = (cgpa*10 + coding + projects*10 + internships*10 + communication*5)/5

    # 🔥 Balanced logic
    if score > 75:
        placed = 1
    elif score < 55:
        placed = 0
    else:
        placed = random.choice([0,1])   # balance

    data.append([cgpa, coding, projects, internships, communication, placed])

df = pd.DataFrame(data, columns=[
    "cgpa", "coding", "projects", "internships", "communication", "placed"
])

df.to_csv("dataset/placement_ai.csv", index=False)

print("✅ Balanced dataset created!")