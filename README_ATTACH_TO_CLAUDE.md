# Yad2 Claude/Codex Prompt Package

This folder contains the files to attach to Claude Code / Codex for implementing the Yad2 Telegram car monitoring bot.

## Attach these files first

1. `docs/PROMPT_FOR_CLAUDE_CODE.md`
2. `configs/search_profile_primary.json`
3. `data/yad2_filter_metadata.json`
4. `configs/listing_keyword_rules.json`
5. `configs/scoring_rules.json`
6. `docs/telegram_message_template.md`
7. `samples/search_result_card.html`
8. `samples/listing_detail_technical_section.html`
9. `samples/listing_detail_description_location_phone_image.html`

## Model metadata files

Attach these too if you want the implementation to support model-name/model-ID resolution:

- `data/yad2_car_metadata.json`
- `data/yad2_car_models_flat.json`
- `data/yad2_car_models.csv`
- `data/yad2_car_metadata.sqlite`

For the current search profile, no `model=` filter is used, so these model files are helpful but not mandatory for the first version.

## Important

This package is planning + prompt material only. It is not the implementation.
