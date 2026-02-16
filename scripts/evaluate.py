import csv
from email_spam_detector.detectors import GibberishDetector

def run_evaluation(name, detector, data):
    results = []
    for email, true_label in data:
        pred_label = 1 if detector.is_spam(email) else 0
        results.append((email, true_label, pred_label))
            
    tp_examples = [e for e, t, p in results if t == 1 and p == 1]
    tn_examples = [e for e, t, p in results if t == 0 and p == 0]
    fp_examples = [e for e, t, p in results if t == 0 and p == 1]
    fn_examples = [e for e, t, p in results if t == 1 and p == 0]
    
    tp = len(tp_examples)
    tn = len(tn_examples)
    fp = len(fp_examples)
    fn = len(fn_examples)
    
    accuracy = (tp + tn) / len(results) if results else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n--- {name} Results ---")
    print(f"Accuracy:  {accuracy:.2f}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall:    {recall:.2f}")
    print(f"F1 Score:  {f1:.2f}")
    print(f"Confusion Matrix: TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    
    if tp_examples:
        print(f"  Example Spam (Correct): {tp_examples[0]}")
    if tn_examples:
        print(f"  Example Ham (Correct):  {tn_examples[0]}")
    if fp_examples:
        print(f"  Example False Positive: {fp_examples[0]}")
    if fn_examples:
        print(f"  Example False Negative: {fn_examples[0]}")

def evaluate():
    from email_spam_detector.detectors import KeywordDetector, EnsembleDetector, HeuristicDetector
    
    data = []
    with open('data/emails.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append((row['email'], int(row['label'])))
            
    gibberish = GibberishDetector()
    keyword = KeywordDetector()
    heuristic = HeuristicDetector()
    ensemble = EnsembleDetector([gibberish, keyword, heuristic])
    
    run_evaluation("Gibberish Detector", gibberish, data)
    run_evaluation("Keyword Detector", keyword, data)
    run_evaluation("Heuristic Detector", heuristic, data)
    run_evaluation("Ensemble (OR)", ensemble, data)

if __name__ == "__main__":
    evaluate()
