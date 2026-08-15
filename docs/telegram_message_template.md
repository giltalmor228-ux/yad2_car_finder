# Telegram Message Template

## Telegram delivery rule

If listing has at least one image:
- Send the first image as a Telegram photo.
- Put the listing summary as the photo caption.
- If there are multiple images, optionally send the rest as an album/media group.

If listing has no image:
- Send the same listing summary as a regular text message.

Do not store or send the raw seller phone number by default.
Store only `phone_available: true/false`.

## Message caption / text template

🚗 {title}
{subtitle}

💰 מחיר: {price}
📅 שנה: {year}
🛣️ ק״מ: {km}
✋ יד: {hand}
⚙️ גיר: {gearbox}
⛽ מנוע: {engine}
📍 מיקום: {location}
👤 בעלות נוכחית: {current_ownership}
📜 בעלות מקורית: {original_ownership}
🧪 טסט עד: {test_valid_until}

⭐ ציון התאמה: {score}/100

✅ נקודות חיוביות:
{positive_reasons}

⚠️ דגלים:
{flags}

🖼️ תמונות: {image_count}

🔗 {url}
