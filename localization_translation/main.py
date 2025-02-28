import json
import os
from deep_translator import GoogleTranslator

INPUT_FILE = "input.json"
OUTPUT_FILE = "output.json"
PROGRESS_FILE = "progress.json"
TARGET_LANGUAGE = "de"


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def parse_topics(data):
    topics = {}
    for key, text in data.items():
        parts = key.split("/")
        topic = parts[-2]
        subkey = parts[-1]

        if topic not in topics:
            topics[topic] = {}
        topics[topic][subkey] = text

    for topic in topics:
        topics[topic] = dict(sorted(topics[topic].items(), key=lambda x: (x[0] != "init", x[0])))

    return topics


def get_last_completed():
    return load_json(PROGRESS_FILE)


def save_progress(topic):
    progress = get_last_completed()
    progress[topic] = True
    save_json(PROGRESS_FILE, progress)


def translate_text(text):
    try:
        translated_text = GoogleTranslator(source="auto", target=TARGET_LANGUAGE).translate(text)
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return "Translation unavailable"


def edit_translation(output_data):
    topics = parse_topics(output_data)

    print("\nAvailable topics for editing:")
    for topic in topics:
        print(f"- {topic}")

    topic_to_edit = input("\nEnter the full topic name to edit: ").strip()

    if topic_to_edit not in topics:
        print("Topic not found in translations. Returning to menu.")
        return

    print(f"\nEditing topic: {topic_to_edit}")
    updated_responses = {}

    for subkey, text in topics[topic_to_edit].items():
        print(f"{subkey}: {text}")
        new_text = input("Edit (press Enter to keep current text): ").strip()
        updated_responses[subkey] = new_text if new_text else text

    for subkey, new_text in updated_responses.items():
        key = f"Conversations/Activity Dialogue/{topic_to_edit}/{subkey}"
        output_data[key] = new_text

    save_json(OUTPUT_FILE, output_data)
    print(f"Updated translations for topic '{topic_to_edit}' saved.")


def add_translation():
    data = load_json(INPUT_FILE)
    output_data = load_json(OUTPUT_FILE)
    progress = get_last_completed()

    topics = parse_topics(data)

    while True:
        topic_filter = input("\nEnter a topic keyword to filter by: ").strip()
        matching_topics = {k: v for k, v in topics.items() if topic_filter in k}

        if not matching_topics:
            print("No matching topics found. Try again.")
            continue

        for topic, lines in matching_topics.items():
            if topic in progress:
                continue

            print(f"\nTopic: {topic}")
            responses = {}

            for subkey, text in lines.items():
                suggested_translation = translate_text(text)

                print(f"\n{subkey}: {text}")
                print(f"Suggested translation ({TARGET_LANGUAGE}): {suggested_translation}")

                response = input("Your response (press Enter to accept suggestion): ").strip()
                responses[subkey] = response if response else suggested_translation

            # Append responses to the output file in the correct format
            for subkey, response in responses.items():
                key = f"Conversations/Activity Dialogue/{topic}/{subkey}"
                output_data[key] = response

            save_json(OUTPUT_FILE, output_data)
            save_progress(topic)

            print(f"Responses for topic '{topic}' saved.\n")

        break

    print("All matching topics completed!")


def main():
    while True:
        print("\nSelect Mode:")
        print("1. Add new translations")
        print("2. Edit existing translations")
        print("3. Exit")

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
