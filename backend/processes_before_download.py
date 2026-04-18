import json
import io
import xlsxwriter
import math

food_stats = json.load(open("food_stats.json"))
portions = json.load(open("portions.json"))

ultraprocessed_foods = json.load(open("ultraprocessed_foods.json"))
ultraprocessed_foods_ids = [id for id, data in ultraprocessed_foods.items() if data['ultraprocessed']]

FREQ_MAP = {
    "Per day": 1,
    "Per week": 7,
    "Per Month": 30,
}


def process_df_before_download(rows: list[dict]):
    stats_per_section: dict[str, dict] = {}
    ultraprocessed_foods_stats_sum: dict[str, float] = {}
    empty_template_row = {f"Calculated {stat_name}":0 for stat_name in food_stats[list(food_stats.keys())[0]].keys()}
    for row in rows:
        current_food_item_stats = food_stats.get(row['id'])
        if row['section'] not in stats_per_section: 
            stats_per_section[row['section']] = empty_template_row.copy()
            stats_per_section[row['section']].update({"name": f"Section {row['section']} summation of stats"})  
        if not current_food_item_stats:
            raise IndexError(f"Item with ID {row['id']} not found")
        if row['selected_portion_size'] is None or row['selected_portion_size'] == "":
            row.update(empty_template_row)                
            continue

        gram_per_portion = float(portions[row['id']]['portions'][row['selected_portion_size']])
        row.update({"Gram/Portion": gram_per_portion})

        if row['frequency'] == "Never":
            portions_per_day = 0
        else:    
            portions_per_day = round((row['number_of_portions'] * row['frequency_count']) / FREQ_MAP[row['frequency']], 3)
        row.update({"Portions/day": portions_per_day})

        grams_per_day = round(gram_per_portion * portions_per_day, 3)
        row.update({"Grams/day": grams_per_day})

        for stat_name, stat_value in current_food_item_stats.items():
            current_stat = round((stat_value/100) * grams_per_day, 3)
            row.update({stat_name: stat_value, f"Calculated {stat_name}": current_stat})

            if row['id'] in ultraprocessed_foods_ids:
                if f'Calculated {stat_name}' not in ultraprocessed_foods_stats_sum: 
                    ultraprocessed_foods_stats_sum[f'Calculated {stat_name}'] = current_stat
                else:
                    ultraprocessed_foods_stats_sum[f'Calculated {stat_name}'] += current_stat

            if f"Calculated {stat_name}" in stats_per_section[row['section']]:
                stats_per_section[row['section']][f"Calculated {stat_name}"] += current_stat
            else:
                stats_per_section[row['section']][f"Calculated {stat_name}"] = current_stat

    current_section = -1
    for row_idx, row in [i for i in enumerate(rows)][::-1]:
        if current_section != row['section']:
            section_id = row.get('section')
            rows.insert(row_idx+1, stats_per_section[section_id])
            current_section = row['section']

    total_stat_sections = {"name": "All Sections summation of stats"}
    for section_stats in stats_per_section.values():
        for stat_name, stat_value in section_stats.items():
            if stat_name == "name":
                continue
            if stat_name in total_stat_sections:
                total_stat_sections[stat_name] += stat_value
            else:
                total_stat_sections[stat_name] = stat_value
    
    rows.append(total_stat_sections)

    rows.append({})
    
    for section_key, section_stats in stats_per_section.items():
        row_to_append = {"name": f"Perc of section #{section_key} contribution"}
        for stat_name, stat_value in section_stats.items():
            if stat_name == "name":
                continue
            if total_stat_sections[stat_name] == 0:
                row_to_append.update({stat_name: 0})
            else:
                row_to_append.update({stat_name: round(100*float(stat_value)/float(total_stat_sections[stat_name]), 3)})

        rows.append(row_to_append)

    ultraprocessed_perc_row = {"name": "Perc of ultra processed food contribution"}
    for stat_name, stat_value in ultraprocessed_foods_stats_sum.items():
        if stat_name == "name":
            continue
        if total_stat_sections[stat_name] == 0:
            ultraprocessed_perc_row.update({stat_name: 0})
        else:
            ultraprocessed_perc_row.update({stat_name: round(100*float(stat_value)/float(total_stat_sections[stat_name]), 3)})

    rows.append(ultraprocessed_perc_row)



def rows_to_workbook(rows: list[dict]) -> tuple[xlsxwriter.Workbook, io.BytesIO]:
    buf = io.BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    worksheet = workbook.add_worksheet()
    worksheet.freeze_panes(1, 0)
    worksheet.autofit()

    bold = workbook.add_format({"bold": True})
    text_type = workbook.add_format({'num_format': '@'})
    summation_lines = workbook.add_format({'bg_color': "#AAAAAA", 'font_color': '#000000'})
    ultraprocessed_lines = workbook.add_format({'bg_color': "#FFF59C", 'font_color': '#000000'})


    if not rows:
        workbook.close()
        buf.seek(0)
        return workbook, buf

    headers = list(rows[0].keys())
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header.replace("_", " ").title(), bold)
        
        if header == 'id':
            worksheet.set_column(col_num, col_num, 7, text_type)

        elif header == 'name':
            worksheet.set_column(col_num, col_num, 40, text_type)

    for row_num, row in enumerate(rows, start=1):
        if row.get('name') is None:
            continue
        
        if row.get('id') in ultraprocessed_foods_ids or row.get('name') == "Perc of ultra processed food contribution":
            worksheet.set_row(row_num, cell_format=ultraprocessed_lines)

        if row.get('name').endswith("summation of stats"):
            worksheet.set_row(row_num, cell_format=summation_lines)
            
        for col_num, key in enumerate(headers):
            value = row.get(key)
            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                value = ""
            worksheet.write(row_num, col_num, value)

    workbook.close()
    buf.seek(0)
    return workbook, buf
