import json
from pathlib import Path

base = Path(
    "/Applications/Khmer Law Code.app/Wrapper/Runner.app/"
    "Frameworks/App.framework/flutter_assets/assets"
)

files = ["codes.json", "articles_chapter.json", "definition.json", "amendment.json"]

for filename in files:
    path = base / filename
    print(f"\n{'=' * 50}")
    print("File:", filename)
    print("Size:", round(path.stat().st_size / 1024 / 1024, 2), "MB")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as e:
        print("Unable to parse JSON:", e)
        continue

    print("Root type:", type(data).__name__)

    if isinstance(data, list):
        print("Total records:", len(data))
        if data:
            print("First record type:", type(data[0]).__name__)
            if isinstance(data[0], dict):
                print("Fields:", list(data[0].keys()))

    elif isinstance(data, dict):
        print("Top-level keys:", list(data.keys()))
        for key, value in data.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} records")
                if value and isinstance(value[0], dict):
                    print("  Fields:", list(value[0].keys()))
