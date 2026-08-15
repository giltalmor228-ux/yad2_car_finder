# Yad2 Car Metadata DB

Generated from the HTML snippets provided in this conversation.

## Files

- `yad2_car_metadata.sqlite` - SQLite database with `manufacturers` and `models` tables.
- `yad2_car_metadata.json` - Nested dictionary grouped by manufacturer name.
- `yad2_car_models_flat.json` - Flat list of model records.
- `yad2_car_models.csv` - Flat CSV for quick review.

## Important limitation

The uploaded model checklist HTML contains manufacturer group names and model IDs, but not manufacturer IDs.
Manufacturer IDs are filled when provided manually (e.g. Toyota=19, Honda=17, Hyundai=21, Mazda=27, Suzuki=36, Nissan=32).
Some manufacturer IDs may still be `null` until confirmed from Yad2.

## Parsed source summary

- Pasted text(10).txt: 35 model rows parsed
- Pasted text(11).txt: 128 model rows parsed
- conversation Honda checklist HTML: 17 model rows (Honda manufacturer_id=17)

Total unique model records: 180
Total manufacturer groups: 7
Manufacturer groups: אבארט, הונדה, טויוטה, יונדאי, מאזדה, ניסאן, סוזוקי

## Suggested next step

Provide additional manufacturer dropdown / model checklist HTML to expand the catalog.

## Suggested next step

Provide the manufacturer dropdown HTML so we can populate `yad2_manufacturer_id` for each manufacturer name.
