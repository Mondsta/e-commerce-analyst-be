```markdown
# Project Setup

## Prerequisites

Sebelum menjalankan aplikasi, pastikan Anda memiliki hal-hal berikut:

1. **Node.js** dan **Yarn** telah terinstall di komputer Anda.
2. **Python 3.8+** sudah terinstall di komputer Anda.
3. **File konfigurasi** yang disebut `.env.local` telah dibuat di root direktori project.

---

## Environment Setup

Sebelum memulai atau menjalankan aplikasi menggunakan command `yarn dev` di terminal Visual Studio Code, pastikan Anda melakukan langkah-langkah berikut:

### 1. Membuat file `.env.local`

Buat file **`.env.local`** di direktori utama project dan tambahkan konfigurasi berikut:

```bash
NEXT_PUBLIC_NODE_ENV=development || production
APP_VERSION=$npm_package_version
NEXT_PUBLIC_BASE_API_URL=http://localhost:5000
PORT=8000
```

### 2. Menjalankan Backend

**Wajib untuk menjalankan backend terlebih dahulu** sebelum frontend. Backend menggunakan **Python** dengan framework Flask.

- **Aktifkan virtual environment**:
  
  ```bash
  python -m venv venv
  ```

- **Aktifkan environment**:

  - Untuk **macOS/Linux**:

    ```bash
    source venv/bin/activate
    ```

  - Untuk **Windows**:

    ```bash
    venv\Scripts\activate
    ```

- **Install dependencies**:

  ```bash
  pip install -r requirements.txt
  ```

- **Jalankan backend**:

  ```bash
  python app.py
  ```

  Backend akan berjalan di `http://localhost:5000`.

### 3. Menjalankan Frontend

Setelah backend berjalan, **jalankan frontend** menggunakan **Yarn**.

- **Jalankan frontend**:

  ```bash
  yarn dev
  ```

  Frontend akan berjalan di `http://localhost:8000`.

---

## Folder Structure

```plaintext
project-root/
│
├── datatraining/
│   └── data_training_normalisasi_kata.csv
├── cache/                 # Menyimpan cache hasil scraping
├── app.py                 # Flask API
├── requirements.txt       # Dependencies untuk Python
├── .env.local             # Konfigurasi environment
├── pages/
│   └── try/
│       └── detail/
│           └── index.js   # Halaman detail
└── README.md              # Dokumentasi
```

---

## Start Developing

```bash
# Aktifkan virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Jalankan backend Flask
python app.py

# Jalankan frontend Next.js
yarn dev
```

Aplikasi akan berjalan di:

- Backend: `http://localhost:5000`
- Frontend: `http://localhost:8000`

---
