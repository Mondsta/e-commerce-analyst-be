from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import string
import emoji
from datetime import datetime
from sklearn.ensemble import IsolationForest
import numpy as np

app = Flask(__name__)
CORS(app, origins='http://localhost:3000')

# Fungsi untuk membersihkan data ulasan
def clean_review_data(review_text):
    # Remove emojis
    review_text = emoji.replace_emoji(review_text, "")
    # Replace colons with a space first
    review_text = review_text.replace(":", " ")
    # Remove all other punctuation
    review_text = review_text.translate(str.maketrans('', '', string.punctuation))
    # Replace multiple spaces with a single space and strip leading/trailing spaces
    review_text = re.sub(r'\s+', ' ', review_text).strip()
    return review_text

# Fungsi untuk mengambil ulasan dari Shopee (tanpa pembersihan data)
def get_shopee_reviews(url, limit=50):
    pattern = r'i\.(\d+)\.(\d+)'
    match = re.search(pattern, url)
    if not match:
        return "Invalid URL"
    shop_id, item_id = match.groups()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    reviews_list = []
    offset = 0
    product_name = ""

    while True:
        api_url = f"https://shopee.co.id/api/v2/item/get_ratings?itemid={item_id}&shopid={shop_id}&limit={limit}&offset={offset}"
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            reviews = data.get("data", {}).get("ratings", [])
            product_info = data.get("data", {}).get("item", {})
            product_name = product_info.get("name") or "No product name found"

            if not reviews:
                break

            for review in reviews:
                comment = review.get("comment")
                rating = review.get("rating_star")
                ctime = review.get("ctime")
                review_time = datetime.utcfromtimestamp(ctime) if ctime else None

                if comment:
                    reviews_list.append({
                        "username": review.get("author_username"),
                        "review": comment,  # Tanpa pembersihan
                        "rating": rating,
                        "review_time": review_time
                    })

            offset += limit
        else:
            return "Failed to retrieve reviews"

    if reviews_list:
        reviews_list = sorted(reviews_list, key=lambda x: x['review_time'], reverse=True)
        for review in reviews_list:
            review["review_time"] = review["review_time"].strftime('%d %B %Y %H:%M:%S') if review["review_time"] else None

        result = {
            "product_name": product_name,
            "total_reviews": len(reviews_list),
            "reviews": reviews_list
        }
        
        return result
    else:
        return "No reviews available"

# Fungsi untuk mengambil ulasan dari Tokopedia (tanpa pembersihan data)
def get_tokopedia_reviews(url):
    pattern = r'tokopedia\.com/([^/]+)/([^/]+)'
    match = re.search(pattern, url)
    if not match:
        return "Invalid URL"
    
    store_name, product_id = match.groups()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    reviews_list = [
        {
            "username": "user_tokopedia1",
            "review": "Ulasan produk dari Tokopedia! Sangat bagus!",  # Tanpa pembersihan
            "rating": 4,
            "review_time": "27 Oktober 2024 14:30:00"
        }
    ]
    
    if reviews_list:
        result = {
            "product_name": "Tokopedia Product",
            "total_reviews": len(reviews_list),
            "reviews": reviews_list
        }
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

# Endpoint untuk mendapatkan ulasan Tokopedia
@app.route('/get_tokopedia_reviews', methods=['POST'])
def get_tokopedia_reviews_endpoint():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"error": "URL not provided"}), 400

    url = data['url']
    reviews = get_tokopedia_reviews(url)

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
    review_texts = [review['review'] for review in reviews]

    # Feature extraction
    feature_array = np.array([[len(review['review']), review['rating']] for review in reviews])

    # Fit Isolation Forest model
    isolation_forest = IsolationForest(contamination=0.1)
    isolation_forest.fit(feature_array)

    # Predict anomalies
    anomaly_predictions = isolation_forest.predict(feature_array)

    # Get decision function scores
    decision_scores = isolation_forest.decision_function(feature_array)

    # Normalize scores to range [0, 1]
    normalized_scores = (decision_scores - decision_scores.min()) / (decision_scores.max() - decision_scores.min())

    # Prepare result with scores
    anomalies = []
    for i, prediction in enumerate(anomaly_predictions):
        if prediction == -1:  # If it's an anomaly
            conclusion = ""
            if reviews[i]['rating'] >= 4:
                conclusion = "Anomali positif: Review ini memiliki rating tinggi tetapi kurang memberikan alasan yang kuat."
            elif reviews[i]['rating'] <= 2:
                conclusion = "Anomali negatif: Review ini memiliki rating rendah tetapi tidak sesuai dengan mayoritas review yang positif."

            anomalies.append({
                "username": reviews[i]['username'],
                "review": reviews[i]['review'],
                "rating": reviews[i]['rating'],
                "review_time": reviews[i]['review_time'],
                "anomaly": True,
                "conclusion": conclusion,
                "anomaly_score": normalized_scores[i]  # Tambahkan skor anomali ke output
            })

    # Membuat hasil dengan setiap anomali terpisah
    result = {
        "product_name": data.get("product_name", "Unknown"),
        "total_reviews": len(reviews),  # Total ulasan semua
        "total_anomalies": len(anomalies),  # Total ulasan anomali
        "anomalies": anomalies
    }
    
    # Mengubah struktur untuk menampilkan setiap anomali dalam format yang diinginkan
    if anomalies:
        result['anomalies'] = [{"anomaly": True,
                                 "conclusion": anomaly['conclusion'],
                                 "rating": anomaly['rating'],
                                 "review": anomaly['review'],
                                 "review_time": anomaly['review_time'],
                                 "username": anomaly['username'],
                                 "anomaly_score": anomaly['anomaly_score']}  # Menyertakan skor anomali
                               for anomaly in anomalies]
    
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)