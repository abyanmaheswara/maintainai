# ⚙️ MaintainAI — Predictive Maintenance Diagnostic System

AI-powered app untuk diagnosa kerusakan mesin industri menggunakan Gemini API.

## 🚀 Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan app
```bash
streamlit run app.py
```

### 3. Dapetin Gemini API Key
- Buka [aistudio.google.com](https://aistudio.google.com)
- Login pake Google account
- Klik "Get API Key" → "Create API Key"
- Copy dan paste ke sidebar app

## 🧠 Fitur
- Input gejala mesin: suara, suhu, getaran, performa
- AI analisis pake Gemini 2.0 Flash (gratis!)
- Output: tingkat keparahan, komponen berisiko, rekomendasi aksi
- Riwayat analisis tersimpan di sesi

## 🛠️ Tech Stack
- **Frontend**: Streamlit
- **AI**: Google Gemini 2.0 Flash API
- **Language**: Python

## 📁 Struktur Project
```
ai-maintenance/
├── app.py           # Main application
├── requirements.txt # Dependencies
└── README.md        # This file
```

---
Made with ❤️ · Polman Bandung · TRI
