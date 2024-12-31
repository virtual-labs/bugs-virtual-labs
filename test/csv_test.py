import csv
import time
from collections import defaultdict
import google.generativeai as genai
import pickle

# Load environment variables
import os
KEY = 'GEMINI_KEY_HERE'
global total
total = 1
if not KEY:
    print("Please set the environment variable API_KEY")
    exit(1)

# Configure generative AI
genai.configure(api_key=KEY)

# Template for labeling issues
TEMPLATE = 'You are a content moderator for GitHub issues. Your task is to label issues as inappropriate or not. Inappropriate refers to issues containing hateful/profane language. Given an issue return only NSFW if inappropriate else return SFW. Nothing else.\nIssue\n'

def predict_label(comment):
    # Configure the generative model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(f"{TEMPLATE}{comment}")
    if 'NSFW' in response.text:
        return 'NSFW'
    return 'SFW'

def get_comments_from_csv(csv_path):
    issues = []
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            content = row['body']
            extracted_content = ''
            flag = False
            for line in content.split("\n"):
                if 'Additional info' in line:
                    flag = True
                elif 'UserAgent' in line:
                    break
                if flag:
                    extracted_content += line.replace('Additional info-', '').strip() + ' '

            issue = {
                "id": row['id'],
                "number": row['number'],
                "title": row['title'],
                "body": extracted_content.strip() if extracted_content else row['body'],
                "actual_label": row.get('labels', '')  # Add "labels" to map actual if provided
            }
            issues.append(issue)
    return issues

def get_predictions(issues, checkpoint_path="checkpoint.pkl"):
    results = []

    # Load checkpoint if available
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'rb') as f:
            processed_issues = pickle.load(f)
        processed_ids = {issue['id'] for issue in processed_issues}
        results.extend(processed_issues)
    else:
        processed_ids = set()

    for i,issue in enumerate(issues):
        if issue['id'] in processed_ids:
            continue

        try:
            global total
            print(f"Processing issue {total}...")
            label = predict_label(issue['body'] or issue['title'])
            total += 1
            results.append({"id": issue['id'], "predicted_label": label, "actual_label": issue.get('actual_label', ''),'number': issue.get('number', '')})

            # Save progress to checkpoint
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(results, f)

        except Exception as e:
            print(f"Error processing issue {issue['id']}: {e}")

        # Rate limit handling
        time.sleep(5)  # Ensure 12 requests per minute

    return results

def calculate_statistics(predictions):
    stats = defaultdict(int)
    for result in predictions:
        predicted = result['predicted_label']
        actual = 'NSFW' if 'Inappropriate' in result['actual_label'] else 'SFW'

        # Track counts
        if predicted == 'NSFW':
            stats['predicted_inappropriate'] += 1
        if actual == 'NSFW':
            stats['actual_inappropriate'] += 1
        if predicted == actual:
            stats['correct_predictions'] += 1

    stats['total_predictions'] = len(predictions)
    return stats

def main(csv_path):
    # Step 1: Read CSV
    issues = get_comments_from_csv(csv_path)

    # Step 2: Get Predictions
    predictions = get_predictions(issues)

    # Step 3: Calculate Statistics
    stats = calculate_statistics(predictions)

    # Print statistics
    print("--- Results ---")
    print(f"Total issues processed: {stats['total_predictions']}")
    print(f"Predicted Inappropriate (NSFW): {stats['predicted_inappropriate']}")
    print(f"Actual Inappropriate (NSFW): {stats['actual_inappropriate']}")
    print(f"Correct Predictions: {stats['correct_predictions']}")

# Run the program
if __name__ == "__main__":
    csv_file_path = "issues.csv"  # Replace with the actual path to your CSV file
    main(csv_file_path)
