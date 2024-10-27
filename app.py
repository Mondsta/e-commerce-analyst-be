from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app, origins='http://localhost:3000')

# Fungsi untuk mengambil ulasan dari Shopee menggunakan metode web scraping
def get_shopee_reviews(url, limit=50):
    pattern = r'-i\.(\d+)\.(\d+)\?'
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

            # Debugging: Memeriksa isi product_info
            print("Product Info:", product_info)

            # Mengambil nama produk dari product_info
            product_name = product_info.get("name") or "No product name found"

            if not reviews:
                break  # Keluar dari loop jika tidak ada lagi ulasan

            for review in reviews:
                comment = review.get("comment")
                rating = review.get("rating_star")
                ctime = review.get("ctime")  # Waktu ulasan dalam Unix timestamp

                # Konversi timestamp Unix ke objek datetime
                review_time = datetime.utcfromtimestamp(ctime) if ctime else None

                if comment:
                    reviews_list.append({
                        "username": review.get("author_username"),
                        "review": comment,
                        "rating": rating,
                        "review_time": review_time
                    })

            offset += limit
        else:
            return "Failed to retrieve reviews"

    if reviews_list:
        # Mengurutkan ulasan berdasarkan review_time secara descending (ulasan terbaru di atas)
        reviews_list = sorted(reviews_list, key=lambda x: x['review_time'], reverse=True)
        
        # Konversi review_time ke format 'Day Month Year Time' setelah sorting
        for review in reviews_list:
            review["review_time"] = review["review_time"].strftime('%d %B %Y %H:%M:%S') if review["review_time"] else None
        
        # Menyusun hasil dalam bentuk dictionary yang diinginkan, dengan total_reviews
        result = {
            "product_name": product_name,
            "total_reviews": len(reviews_list),  # Menambahkan total jumlah ulasan
            "reviews": reviews_list
        }
        
        return result
    else:
        return "No reviews available"

# Endpoint untuk menerima POST request dengan URL Shopee
@app.route('/get_reviews', methods=['POST'])
def get_reviews():
    # Mendapatkan JSON dari request body
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"error": "URL not provided"}), 400

    # Ambil URL dari request body
    url = data['url']

    # Panggil fungsi get_shopee_reviews untuk mendapatkan ulasan
    reviews = get_shopee_reviews(url)

    if isinstance(reviews, str):
        return jsonify({"error": reviews}), 400  # Error handling jika terjadi kesalahan

    # Mengembalikan hasil review dalam format JSON
    return jsonify(reviews), 200

# Menjalankan aplikasi Flask
if __name__ == '__main__':
    app.run(debug=True)