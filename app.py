from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import string
import emoji
from datetime import datetime
from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
import json
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report

app = Flask(__name__)
CORS(app, origins='http://localhost:3000')

# Load slank word dictionary from CSV
slang_dict = pd.read_csv('datatraining/data_training_normalisasi_kata.csv', on_bad_lines='skip').set_index('slang').to_dict()['normalized']

# Fungsi untuk normalisasi slang menggunakan kamus
def normalize_slang(text):
    words = text.split()
    normalized_text = ' '.join([slang_dict.get(word.lower(), word) for word in words])
    return normalized_text

# Fungsi untuk menghapus link, mention, hashtag, tab, new line, back slash, dll.
def remove_links(text):
    text = text.replace('\\t', " ").replace('\\n', " ").replace('\\u', " ").replace('\\', "")
    text = text.encode('ascii', 'replace').decode('ascii')
    text = ' '.join(re.sub(r"([@#][A-Za-z0-9]+)|(\w+://\S+)", " ", text).split())
    return text.replace("http://", " ").replace("https://", " ")

# Fungsi untuk menghapus angka
def remove_number(text):
    return re.sub(r"\d+", " ", text)

# Fungsi untuk membersihkan data ulasan
def clean_review_data(review_text):
    review_text = remove_links(review_text)
    review_text = remove_number(review_text)
    review_text = emoji.replace_emoji(review_text, "")
    review_text = review_text.replace(":", " ")
    review_text = review_text.translate(str.maketrans('', '', string.punctuation))
    review_text = re.sub(r'\s+', ' ', review_text).strip()
    review_text = normalize_slang(review_text)  # Normalisasi slang
    return review_text

# Function to cache reviews
def cache_reviews(cache_file, reviews):
    with open(cache_file, 'w') as f:
        json.dump(reviews, f)

# Function to load cached reviews
def load_cached_reviews(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None

# Function to create cache directory
def create_cache_directory():
    if not os.path.exists('cache'):
        os.makedirs('cache')

# Function to get reviews from Shopee
def get_shopee_reviews(url, limit=50):
    create_cache_directory()  # Ensure cache directory exists
    pattern = r'i\.(\d+)\.(\d+)'
    match = re.search(pattern, url)
    if not match:
        return "Invalid URL"
    shop_id, item_id = match.groups()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    reviews_list = []
    offset = 0
    product_name = None
    product_image = None

    # Define cache file name based on the URL
    cache_file = f"cache/{shop_id}_{item_id}_reviews.json"
    
    # Check if cached reviews exist
    cached_reviews = load_cached_reviews(cache_file)
    if cached_reviews:
        return cached_reviews  # Return cached reviews if available

    while True:
        api_url = f"https://shopee.co.id/api/v2/item/get_ratings?itemid={item_id}&shopid={shop_id}&limit={limit}&offset={offset}"
        try:
            response = session.get(api_url, headers=headers, timeout=10)
            print(f"Request URL: {api_url} - Status Code: {response.status_code}")  # Log URL and status code
            
            if response.status_code == 200:
                data = response.json()
                reviews = data.get("data", {}).get("ratings", [])
                
                if reviews and product_name is None and product_image is None:
                    original_item_info = reviews[0].get("original_item_info", {})
                    product_name = original_item_info.get("name", "Unknown Product")
                    product_image = original_item_info.get("image", "")
                
                if not reviews:
                    print(f"No more reviews found at offset: {offset}. Exiting loop.")  # Log when no reviews found
                    break
                
                for review in reviews:
                    comment = review.get("comment")
                    rating = review.get("rating_star")
                    ctime = review.get("ctime")
                    review_time = datetime.utcfromtimestamp(ctime) if ctime else None

                    if comment:
                        reviews_list.append({
                            "username": review.get("author_username"),
                            "review": comment,
                            "rating": rating,
                            "review_time": review_time
                        })

                offset += limit
                print(f"Fetched {len(reviews)} reviews. Moving to offset {offset}.")  # Log the number of reviews fetched
                time.sleep(0.5)  # Delay to avoid hitting rate limits
            else:
                print(f"Failed to fetch reviews: Status code {response.status_code}")
                break
        except requests.exceptions.RequestException as e:
            print("Error during API request:", e)
            break

    if reviews_list:
        reviews_list = sorted(reviews_list, key=lambda x: x['review_time'], reverse=True)
        for review in reviews_list:
            review["review_time"] = review["review_time"].strftime('%d %B %Y %H:%M:%S') if review["review_time"] else None

        result = {
            "product_name": product_name,
            "product_image": product_image,
            "total_reviews": len(reviews_list),
            "reviews": reviews_list
        }
        
        # Cache the results
        cache_reviews(cache_file, result)
        
        return result
    else:
        return "No reviews available"

####################################################################################################
# Endpoint

# Endpoint untuk mendapatkan ulasan Shopee
@app.route('/get_shopee_reviews', methods=['POST'])
def get_reviews():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"error": "URL not provided"}), 400

    url = data['url']
    reviews = get_shopee_reviews(url)

    if isinstance(reviews, str):
        return jsonify({"error": reviews}), 400

    return jsonify(reviews), 200

# Endpoint untuk membersihkan data ulasan
@app.route('/clean_review_data', methods=['POST'])
def clean_review_data_endpoint():
    data = request.json
    if not data or 'reviews' not in data:
        return jsonify({"error": "Reviews not provided"}), 400

    cleaned_reviews = []
    for review in data['reviews']:
        cleaned_review_text = clean_review_data(review['review'])
        cleaned_reviews.append({
            "username": review['username'],
            "review": cleaned_review_text,
            "rating": review['rating'],
            "review_time": review['review_time']
        })

    result = {
        "product_name": data.get("product_name", "Unknown"),
        "product_image": data.get("product_image", "Unknown"),
        "total_reviews": len(cleaned_reviews),
        "reviews": cleaned_reviews
    }
    
    return jsonify(result), 200

# Endpoint untuk analisa anomali pada ulasan
@app.route('/analyze_anomalies', methods=['POST'])
def analyze_anomalies():
    data = request.json
    if not data or 'reviews' not in data:
        return jsonify({"error": "Reviews not provided"}), 400

    reviews = data['reviews']
    
    # Ground truth labels (for example purposes, this should be real ground truth data)
    # 1: anomaly, 0: normal
    ground_truth = [1 if review['rating'] <= 3 else 0 for review in reviews]  # Dummy ground truth
    
    # Extract features: review length and rating
    feature_array = np.array([[len(review['review'].split()), review['rating']] for review in reviews])

    # Initialize Isolation Forest
    isolation_forest = IsolationForest(
        n_estimators=1000,
        max_samples='auto',
        contamination=0.2,
        random_state=42,
        bootstrap=False,
        n_jobs=-1
    )
    
    # Fit model
    isolation_forest.fit(feature_array)

    # Predict anomalies
    anomaly_predictions = isolation_forest.predict(feature_array)
    decision_scores = isolation_forest.decision_function(feature_array)

    # Normalize scores to [0, 1]
    normalized_scores = (decision_scores - decision_scores.min()) / (decision_scores.max() - decision_scores.min())

    # Anomaly detection result
    anomalies = []
    for i, prediction in enumerate(anomaly_predictions):
        if prediction == -1:  # If this is an anomaly
            # Pastikan data review ada
            review = reviews[i]
            rating = review.get('rating')
            review_text = review.get('review')
            review_time = review.get('review_time')

            # Jika rating atau review_text tidak ada, skip ke iterasi berikutnya
            if rating is None or review_text is None:
                continue

            review_length = len(review_text.split())
            anomaly_score = normalized_scores[i]

            # Anomaly conclusion based on review content
            conclusion = ""

            if rating >= 4:  # Positive anomaly
                # Check if review lacks a strong reason
                if review_length < 10:  # Example threshold for a brief review
                    conclusion = "Anomali positif: Review ini memiliki rating tinggi tetapi kurang memberikan alasan yang kuat."
                # Check if review is inconsistent with majority of comments
                elif review_text.lower() not in ' '.join([r['review'].lower() for r in reviews if r['rating'] >= 4]):
                    conclusion = "Anomali positif: Review ini memiliki rating tinggi tetapi tidak sesuai dengan mayoritas komentar lainnya."
                else:
                    conclusion = "Anomali positif: Review ini memiliki rating tinggi tetapi tidak sesuai dengan mayoritas komentar lainnya"

            elif rating <= 3:  # Negative anomaly
                # Check if review lacks explanation
                if review_length < 10:  # Example threshold for a brief review
                    conclusion = "Anomali negatif: Review ini memiliki rating rendah tetapi tidak memberikan alasan yang kuat."
                # Check if review is inconsistent with majority of comments
                elif review_text.lower() not in ' '.join([r['review'].lower() for r in reviews if r['rating'] <= 3]):
                    conclusion = "Anomali negatif: Review ini memiliki rating rendah tetapi tidak sesuai dengan mayoritas komentar lainnya."
                else:
                    conclusion = "Anomali negatif: Review ini memiliki rating rendah tetapi tidak sesuai dengan mayoritas komentar lainnya."

            anomalies.append({
                "username": review.get('username'),
                "review": review_text,
                "rating": rating,
                "review_time": review_time,
                "anomaly": True,
                "conclusion": conclusion,
                "anomaly_score": anomaly_score
            })

    # Calculate confusion matrix and accuracy
    pred_labels = [1 if pred == -1 else 0 for pred in anomaly_predictions]  # Convert -1 to 1 (anomaly) and 1 to 0 (normal)

    cm = confusion_matrix(ground_truth, pred_labels)
    accuracy = accuracy_score(ground_truth, pred_labels)

    result = {
        "product_name": data.get("product_name", "Unknown"),
        "product_image": data.get("product_image", "Unknown"),
        "total_reviews": len(reviews),
        "total_anomalies": len(anomalies),
        "anomalies": anomalies,
        "accuracy": accuracy,
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(ground_truth, pred_labels)
    }

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)