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
    product_name = None  # Awalnya None
    product_image = None  # Tambahkan variabel product_image

    while True:
        api_url = f"https://shopee.co.id/api/v2/item/get_ratings?itemid={item_id}&shopid={shop_id}&limit={limit}&offset={offset}"
        response = requests.get(api_url, headers=headers)
        # print("API URL:", api_url)
        if response.status_code == 200:
            data = response.json()
            # print(data)
            reviews = data.get("data", {}).get("ratings", [])
            
            # Ambil nama dan gambar produk dari review pertama, jika belum ada
            if reviews and product_name is None and product_image is None:
                original_item_info = reviews[0].get("original_item_info", {})
                product_name = original_item_info.get("name", "Unknown Product")
                product_image = original_item_info.get("image", "")

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
            "product_image": product_image,  # Tambahkan output product_image
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

    # Panggilan API untuk mendapatkan ulasan
    api_url = f"https://api.tokopedia.com/v1/product/{product_id}/reviews"  # Contoh URL
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        reviews_list = []  # Ambil ulasan dari data
        
        # Misalkan 'reviews' adalah key yang berisi data ulasan
        for review in data.get("reviews", []):
            reviews_list.append({
                "username": review.get("author_username", "Unknown User"),
                "review": review.get("review_text", ""),  # Misalkan ini adalah teks ulasan
                "rating": review.get("rating_star", 0),  # Misalkan ini adalah rating
                "review_time": datetime.utcfromtimestamp(review.get("created_at", 0)).strftime('%d %B %Y %H:%M:%S')  # Misalkan ini adalah waktu review
            })

        result = {
            "product_name": "Tokopedia Product",  # Atau ambil dari data jika ada
            "product_image": "",  # Tambahkan gambar produk jika tersedia
            "total_reviews": len(reviews_list),
            "reviews": reviews_list
        }
        
        return result
    else:
        return "Failed to retrieve reviews"
    
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
    review_texts = [review['review'] for review in reviews]

    # Ekstraksi fitur
    feature_array = np.array([[len(review['review'].split()), review['rating']] for review in reviews])

    # Inisialisasi Isolation Forest dengan parameter yang dituning
    isolation_forest = IsolationForest(
        n_estimators=10000,          # Jumlah estimators
        max_samples='auto',        # Sampel maksimum per pohon
        contamination=0.1,         # Persentase anomali yang diharapkan
        random_state=42,           # Seed untuk reproduksibilitas
        bootstrap=False,            # Tidak menggunakan bootstrap
        n_jobs=-1                  # Gunakan semua core yang tersedia
    )
    
    # Fit model
    isolation_forest.fit(feature_array)

    # Prediksi anomali dan hitung skor anomali
    anomaly_predictions = isolation_forest.predict(feature_array)
    decision_scores = isolation_forest.decision_function(feature_array)

    # Normalisasi skor ke rentang [0, 1]
    normalized_scores = (decision_scores - decision_scores.min()) / (decision_scores.max() - decision_scores.min())

    # Siapkan hasil dengan skor dan kesimpulan
    anomalies = []
    for i, prediction in enumerate(anomaly_predictions):
        if prediction == -1:  # Jika ini adalah anomali
            conclusion = ""
            if reviews[i]['rating'] >= 4:
                conclusion = "Anomali positif: Review ini memiliki rating tinggi tetapi kurang memberikan alasan yang kuat."
            elif reviews[i]['rating'] <= 4:
                conclusion = "Anomali negatif: Review ini memiliki rating rendah tetapi tidak sesuai dengan mayoritas review yang positif."

            anomalies.append({
                "username": reviews[i]['username'],
                "review": reviews[i]['review'],
                "rating": reviews[i]['rating'],
                "review_time": reviews[i]['review_time'],
                "anomaly": True,
                "conclusion": conclusion,
                "anomaly_score": normalized_scores[i]  # Skor anomali
            })

    # Membuat hasil dengan setiap anomali terpisah
    result = {
        "product_name": data.get("product_name", "Unknown"),
        "product_image": data.get("product_image", "Unknown"),
        "total_reviews": len(reviews),
        "total_anomalies": len(anomalies),
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
                                 "anomaly_score": anomaly['anomaly_score']} 
                               for anomaly in anomalies]
    
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)