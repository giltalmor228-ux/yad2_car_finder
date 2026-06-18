# Yad2 Car Metadata DB

Generated from the HTML snippets provided in this conversation.

## Files

- `yad2_car_metadata.sqlite` - SQLite database with `manufacturers` and `models` tables.
- `yad2_car_metadata.json` - Nested dictionary grouped by manufacturer name.
- `yad2_car_models_flat.json` - Flat list of model records.
- `yad2_car_models.csv` - Flat CSV for quick review.

## Important limitation

The uploaded model checklist HTML contains manufacturer group names and model IDs, but not manufacturer IDs.
Only Toyota has `yad2_manufacturer_id=19` because it was provided manually in the conversation.
The other manufacturer IDs are currently `null` in JSON / empty in CSV / NULL in SQLite until the manufacturer dropdown HTML is provided.

## Parsed source summary

- Pasted text(10).txt: 35 model rows parsed
- Pasted text(11).txt: 128 model rows parsed

Total unique model records: 163
Total manufacturer groups: 6
Manufacturer groups: אבארט, טויוטה, יונדאי, מאזדה, ניסאן, סוזוקי

## Suggested next step

Provide the manufacturer dropdown HTML so we can populate `yad2_manufacturer_id` for each manufacturer name.
