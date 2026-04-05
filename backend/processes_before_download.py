import json

food_stats = json.load(open("food_stats.json"))
portions = json.load(open("portions.json"))

FREQ_MAP = {
    "Per day": 1,
    "Per week": 7,
    "Per Month": 30,
}

# tempo = [{'id': '1.1', 'name': 'White Bread: Arabic/Iranian bread/Pita or Lebanese/ baguette/Toast  ', 'portion_options': ['1 small baguette', '1 toast', '¼ Arabic bread', ''], 'section': '1', 'selected_portion_option': '1 small baguette', 'portion_size': 4.0, 'frequency': 'Per day', 'frequency_count': 3.0}, {'id': '1.1.1', 'name': 'White Bread (homemade) : Arabic/Iranian bread/Pita or Lebanese/ baguette/Toast  ', 'portion_options': ['1 small baguette', '1 toast', '¼ Arabic bread', ''], 'section': '1', 'selected_portion_option': '¼ Arabic bread', 'portion_size': 1.0, 'frequency': 'Per week', 'frequency_count': 5.0}, {'id': '1.2', 'name': 'Brown bread: Arabic/Iranian bread/Pita or Lebanese/ baguette/Toast  ', 'portion_options': ['1 small baguette', '1 toast', '¼ Arabic bread', ''], 'section': '1', 'selected_portion_option': '1 toast', 'portion_size': 12.0, 'frequency': 'Per Month', 'frequency_count': 6.0}]

def process_df_before_download(rows: list[dict]):
    for row in rows:
        current_food_item_stats = food_stats.get(row['id'])
        if not current_food_item_stats:
            raise IndexError(f"Item with ID {row['id']} not found")
        if row['selected_portion_option'] is None or row['selected_portion_option'] == "":
            continue

        single_portion_in_grams = float(portions[row['id']]['portions'][row['selected_portion_option']])
        row.update({"Single selected portion (Grams)": single_portion_in_grams})
        
        portions_per_day = ((row['portion_size'] * row['frequency_count']) / FREQ_MAP[row['frequency']])
        row.update({"Portions per day": portions_per_day})
        
        for stat_name, stat_value in current_food_item_stats.items():
            current_stat = (stat_value/100) * single_portion_in_grams * portions_per_day
            row.update({stat_name: stat_value, f"calculated_{stat_name}": current_stat})


# process_df_before_download(tempo)

# for code, details in portions_json.items():
#     found = False
#     for row in composite_rows: 
#         if code == row['Code'] and details['name'] == row['FOOD ITEM']:
#             found = True
#             break
#     if found:
#         print(code)
#         continue
#     else:
#         raise RuntimeError("WHAT")
    

# for row in composite_rows:
#     if row['Code'].count('.') == 0:
#         continue
#     composite_portion_item = portions_json.get(row['Code'])
#     if composite_portion_item:
#         if composite_portion_item['name'] != row['FOOD ITEM']:
#             print(f"ITEMS DO NOT HAVE THE SAME NAME BUT THE SAME CODE [{row['Code']}]: {row['FOOD ITEM']} =!= {composite_portion_item['name']}")
#     else:
#         print(f"ITEM NOT FOUND IN PORTION JSON: {row['Code']}") 