import json
import os
from deep_translator import GoogleTranslator
from git import Repo

directory = os.path.dirname(__file__)
INPUT_FILE = os.path.join(directory, "input.json")
OUTPUT_FILE = os.path.join(directory, "output.json")
PROGRESS_FILE = os.path.join(directory, "progress.json")
TARGET_LANGUAGE = "de"
repo = Repo(os.path.join(directory, ".."))

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_last_completed():
    return load_json(PROGRESS_FILE)


def save_progress(topic):
    progress = get_last_completed()
    progress[topic] = True
    save_json(PROGRESS_FILE, progress)


def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target=TARGET_LANGUAGE).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return "Translation unavailable"


def filter_by_topic(data, topic_filter):
    return {key: text for key, text in data.items() if topic_filter.lower() in key.lower()}


def edit_translation(output_data):
    topic_to_edit = input("\nEnter the full key to edit: ").strip()

    if topic_to_edit not in output_data:
        print("Key not found in translations. Returning to menu.")
        return

    print(f"\nEditing key: {topic_to_edit}")
    print(f"Current translation: {output_data[topic_to_edit]}")

    new_text = input("Edit (press Enter to keep current text): ").strip()
    if new_text:
        output_data[topic_to_edit] = new_text
        save_json(OUTPUT_FILE, output_data)
        print(f"Updated translation for '{topic_to_edit}' saved.")


def add_translation():
    data = load_json(INPUT_FILE)
    output_data = load_json(OUTPUT_FILE)
    progress = get_last_completed()

    while True:
        topic_filter = input("\nEnter a topic keyword to filter by: ").strip()
        matching_entries = filter_by_topic(data, topic_filter)

        if not matching_entries:
            print("No matching entries found. Try again.")
            continue

        for key, text in matching_entries.items():
            if key in progress:
                print(f"Skipping {key} (already completed).")
                continue

            print(f"\nKey: {key}")
            suggested_translation = translate_text(text)

            print(f"Original: {text}")
            print(f"Suggested translation ({TARGET_LANGUAGE}): {suggested_translation}")

            response = input("Your response (press Enter to accept suggestion): ").strip()
            output_data[key] = response if response else suggested_translation
            origin = repo.remotes.origin
            origin.pull()
            save_json(OUTPUT_FILE, output_data)
            save_progress(key)
            repo.index.add([OUTPUT_FILE, PROGRESS_FILE])
            repo.commit()
            repo.git.push()

            print(f"Translation for '{key}' saved.\n")

        break

    print("All matching entries completed!")


def main():
    while True:
        print("\nSelect Mode:")
        print("1. Add new translations")
        print("2. Edit existing translations")
        print("3. Exit")

        origin = repo.remotes.origin
        origin.pull()

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_translation()
        elif choice == "2":
            output_data = load_json(OUTPUT_FILE)
            edit_translation(output_data)
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()
