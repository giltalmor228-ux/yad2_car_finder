# Attachment Checklist for Claude Code / Codex

## Minimum required

- [ ] docs/PROMPT_FOR_CLAUDE_CODE.md
- [ ] configs/search_profile_primary.json
- [ ] data/yad2_filter_metadata.json
- [ ] configs/listing_keyword_rules.json
- [ ] configs/scoring_rules.json
- [ ] docs/telegram_message_template.md
- [ ] samples/search_result_card.html
- [ ] samples/listing_detail_technical_section.html
- [ ] samples/listing_detail_description_location_phone_image.html

## Optional but recommended

- [ ] data/yad2_car_metadata.json
- [ ] data/yad2_car_models_flat.json
- [ ] data/yad2_car_models.csv
- [ ] data/yad2_car_metadata.sqlite
- [ ] samples/listing_detail_full_page.html, if you collect it later

## Not needed for the first version

- Manufacturer dropdown HTML, because we manually defined manufacturer IDs.
- Phone number raw values, because the bot should store only phone_available=true/false.
