import requests
import csv
import json
import time

# 问题列表（共14个）
questions = [
    "What was the total return of the Government Pension Fund Global in 2023, and how did it compare to the benchmark index?",
    "What was the return on unlisted real estate investments in 2023?",
    "How much did the fund’s market value increase in 2023 and what factors contributed to it?",
    "Which asset class had the highest return in 2023 and why?",
    "What was the asset allocation of the fund at the end of 2023?",
    "How much of the fund was invested in US equities and bonds at the end of 2023?",
    "What percentage of the real estate investments was allocated to office properties?",
    "What are the three main investment strategies used by Norges Bank to manage the fund?",
    "Why did unlisted real estate investments underperform in 2023?",
    "What is the role of responsible investment in the fund’s strategy, and how is it implemented?",
    "What are the key risks identified in the 2023 stress tests, and what potential losses were estimated?",
    "What is the expected absolute volatility of the fund as of 2023, and what does it imply?",
    "What was the average annual return of the fund from 1998 to 2023?",
    "How did equity and fixed-income management contribute to relative return over the past 5 years?"
]

url = 'http://35.246.2.155:8000/api/v1/integration'
headers = {'Content-Type': 'application/json'}

csv_file = 'results.csv'
json_file = 'results.json'
results = []

with open(csv_file, mode='w', newline='', encoding='utf-8') as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(['Question', 'Answer'])

    for q in questions:
        payload = {
            "prompt": q,
            "max_context_docs": 10,
            "source_filter": "",
            "debug": True
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()

            raw_answer = result.get("completion", "")
            answer = raw_answer.strip() if isinstance(raw_answer, str) else str(raw_answer)

        except Exception as e:
            answer = f"ERROR: {str(e)}"

        writer.writerow([q, answer])
        results.append({"question": q, "answer": answer})
        print(f"✔ Asked: {q[:50]}... → Answered.")
        time.sleep(0.5)

# 保存为 JSON
with open(json_file, 'w', encoding='utf-8') as f_json:
    json.dump(results, f_json, ensure_ascii=False, indent=2)

print(f"\n🎉 All results saved to {csv_file} and {json_file}")