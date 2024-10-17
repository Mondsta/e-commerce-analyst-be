from flask import Flask, request, jsonify
import requests
import re
import pandas as pd
from tabulate import tabulate

app = Flask(__name__)

# Fungsi yang digunakan untuk mengambil ulasan dari Shopee
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

    while True:
        api_url = f"https://shopee.co.id/api/v2/item/get_ratings?itemid={item_id}&shopid={shop_id}&limit={limit}&offset={offset}"
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            reviews = data.get("data", {}).get("ratings", [])
            product_info = data.get("data", {}).get("item", {})

            if not reviews:
                break  # Break the loop if no more reviews are available

            for review in reviews:
                comment = review.get("comment")
                rating = review.get("rating_star")  # Menambahkan rating ulasan
                if comment:  # Check if the comment is not empty
                    reviews_list.append({
                        "username": review.get("author_username"),
                        "review": comment,
                        "rating": rating,  # Menyimpan rating ulasan
                        "product_name": product_info.get("name"),
                    })

            offset += limit
        else:
            return "Failed to retrieve reviews"

    if reviews_list:
        df = pd.DataFrame(reviews_list)
        # Mengubah DataFrame menjadi JSON untuk dikembalikan ke client
        return df.to_dict(orient="records")
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
    return jsonify({"reviews": reviews}), 200

# Menjalankan aplikasi Flask
if __name__ == '__main__':
    app.run(debug=True)