import csv
import json

composite_rows = csv.DictReader(open("composite.tsv"), delimiter='\t')
COLUMNS_TO_IGNORE = ["Code", "FOOD ITEM", "REFERENCE PORTION", "Reference ESHA", "Quantity", "Measure", "Gram Weight (g)" ]

food_stats = {}

for row in composite_rows:
    if row['Code'].count('.') == 0:
        continue
    stats_per_one_food = {}
    for key in row:
        if key.strip() not in COLUMNS_TO_IGNORE:
            try:
                stats_per_one_food[key.strip()] = float(row[key].strip().replace(',', ""))
            except ValueError:
                stats_per_one_food[key.strip()] = 0
    food_stats[row["Code"]] = stats_per_one_food
json.dump(food_stats, open("food_stats.json", 'w'), ensure_ascii=False, indent=4)