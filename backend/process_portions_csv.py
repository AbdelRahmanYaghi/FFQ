import csv
import json

items = csv.DictReader(open("portions.tsv"), delimiter="\t")

outputs: dict[tuple[str, str], dict[str, float]] = {}

key = None
for item in items:
    if not item['Portion in grams']:
        key = item['Code']
        if key in outputs:
            print(key)
        outputs[key.strip()] = {"name": item['FOOD ITEM'], "portions": {}} 
    else:
        outputs[key.strip()]['portions'].update({item['REFERENCE PORTION']: item['Portion in grams']})

json.dump(outputs, open("portions.json", 'w'), ensure_ascii=False, indent=4)
