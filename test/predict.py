import pickle
from collections import defaultdict

def calculate_statistics_from_pkl(pkl_path):
    try:
        # Load predictions from the pickle file
        with open(pkl_path, 'rb') as f:
            predictions = pickle.load(f)

        # Initialize statistics
        stats = defaultdict(int)
        false_negatives = []
        false_positives = []
        true_positives = []

        for result in predictions:
            predicted = result['predicted_label']
            actual = 'NSFW' if 'Inappropriate' in result.get('actual_label', '') else 'SFW'
            issue_id = result.get('number', 'unknown')

            # Track counts
            if predicted == 'NSFW':
                stats['predicted_inappropriate'] += 1
            if actual == 'NSFW':
                stats['actual_inappropriate'] += 1
            if predicted == actual:
                stats['correct_predictions'] += 1
                if predicted == 'NSFW':
                    true_positives.append(issue_id)
            else:
                if predicted == 'NSFW' and actual == 'SFW':
                    false_positives.append(issue_id)
                elif predicted == 'SFW' and actual == 'NSFW':
                    false_negatives.append(issue_id)

        stats['total_predictions'] = len(predictions)
        stats['false_negatives'] = false_negatives
        stats['false_positives'] = false_positives
        stats['true_positives'] = true_positives

        return stats

    except FileNotFoundError:
        print(f"Error: The file '{pkl_path}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Run the script
if __name__ == "__main__":
    pkl_file_path = "checkpoint.pkl"  # Replace with the actual path to your pkl file
    stats = calculate_statistics_from_pkl(pkl_file_path)

    if stats:
        print("--- Results ---")
        print(f"Total issues processed: {stats['total_predictions']}")
        print(f"Predicted Inappropriate (NSFW): {stats['predicted_inappropriate']}")
        print(f"Actual Inappropriate (NSFW): {stats['actual_inappropriate']}")
        print(f"Correct Predictions: {stats['correct_predictions']}")
        print(f"False Negatives: {stats['false_negatives']}")
        print(f"False Positives: {stats['false_positives']}")
        print(f"True Positives: {stats['true_positives']}")
        print(f"Total FP: {len(stats['false_positives'])}")
        print(f"Total FN: {len(stats['false_negatives'])}")
        print(f"Total TP: {len(stats['true_positives'])}")

