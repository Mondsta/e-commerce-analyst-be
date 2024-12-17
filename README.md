# Backend Setup (Flask API)

## Prerequisites

Sebelum menjalankan aplikasi, pastikan Anda memiliki hal-hal berikut:

1. **Python 3.8+** terinstall di komputer Anda.
2. **Pip** (Python package manager) terinstall.
3. **File konfigurasi** yang disebut `.env.local` telah dibuat di root direktori project.

---

## Environment Setup

Ikuti langkah-langkah berikut untuk mengatur lingkungan pengembangan backend Flask:

### 1. Menyiapkan Virtual Environment

Disarankan untuk menggunakan virtual environment untuk mengisolasi dependensi Python.

- **Membuat virtual environment**:

  ```bash
  python -m venv venv
  ```

- **Mengaktifkan virtual environment**:

  - Untuk **macOS/Linux**:

    ```bash
    source venv/bin/activate
    ```

  - Untuk **Windows**:

    ```bash
    venv\Scripts\activate
    ```

### 2. Menginstal Dependencies

Setelah mengaktifkan virtual environment, install dependensi yang diperlukan untuk menjalankan aplikasi Flask.

- **Install dependencies**:

  ```bash
  pip install -r requirements.txt
  ```

  Pastikan file `requirements.txt` ada di direktori utama proyek Anda dan berisi daftar paket yang diperlukan.

### 3. Menyiapkan File Konfigurasi

Buat file **`.env.local`** di direktori utama project dan tambahkan konfigurasi berikut:

```bash
NEXT_PUBLIC_NODE_ENV=development || production
APP_VERSION=$npm_package_version
NEXT_PUBLIC_BASE_API_URL=http://localhost:5000
PORT=8000
```

### 4. Menyiapkan Direktori Cache

Buat direktori **`cache/`** untuk menyimpan data cache yang dihasilkan oleh aplikasi.

```bash
mkdir cache
```

---

## Menjalankan Aplikasi

Setelah mengatur semua konfigurasi, Anda dapat menjalankan aplikasi backend dengan langkah berikut:

### 1. Menjalankan Backend

Jalankan aplikasi Flask menggunakan perintah berikut:

```bash
python app.py
```

Aplikasi Flask akan berjalan di `http://localhost:5000`.

### 2. Menjalankan Frontend

Untuk menjalankan frontend, pastikan backend sudah berjalan terlebih dahulu, kemudian jalankan frontend menggunakan **Yarn**.

- **Jalankan frontend**:

  ```bash
  yarn dev
  ```

Frontend akan berjalan di `http://localhost:8000`.

---

## Struktur Direktori

```plaintext
project-root/
│
├── datatraining/
│   └── data_training_normalisasi_kata.csv  # File untuk normalisasi slang
├── cache/                 # Menyimpan cache hasil scraping
├── app.py                 # Aplikasi Flask
├── requirements.txt       # Dependencies untuk Python
├── .env.local             # File konfigurasi environment
└── README.md              # Dokumentasi
```

---

## Pengembangan Lebih Lanjut

Jika Anda ingin melakukan pengembangan lebih lanjut, pastikan untuk mengikuti langkah-langkah ini untuk memulai:

```bash
# Aktifkan virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Jalankan aplikasi Flask
python app.py
```
