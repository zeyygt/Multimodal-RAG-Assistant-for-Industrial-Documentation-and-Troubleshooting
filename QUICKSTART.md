# 🚀 Hızlı Başlangıç Rehberi (Quick Start Guide)

## İlk Kurulum (First Time Setup)

### 1. Python Bağımlılıklarını Kur

```bash
# Virtual environment oluştur
python -m venv venv

# Aktive et
source venv/bin/activate

# Paketleri yükle
pip install -r requirements.txt
```

### 2. Frontend Bağımlılıklarını Kur

```bash
cd web
npm install
cd ..
```

### 3. API Anahtarını Ekle

`.env` dosyası oluştur ve OpenAI API anahtarını ekle:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

API key almak için: https://platform.openai.com/api-keys

### 4. PDF Dosyalarını İşle

```bash
# PDF'leri data/ klasörüne koy
mkdir -p data
cp /path/to/your/file.pdf data/

# İşleme pipeline'ını çalıştır
source venv/bin/activate
python src/main.py
```

Bu adım:
- PDF'den metin ve resim çıkarır
- OCR yapar
- Chunk'lar oluşturur
- Embedding'ler üretir
- FAISS index oluşturur

**Süre:** ~100 sayfa için 2-5 dakika

## Uygulamayı Çalıştırma (Running the App)

### Otomatik Başlatma (Recommended)

```bash
./start.sh
```

Bu script hem backend'i hem frontend'i başlatır.

### Manuel Başlatma

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python api.py
```

**Terminal 2 - Frontend:**
```bash
cd web
npm start
```

## Tarayıcıda Aç

http://localhost:3000

## Örnek Sorular

- "Cihazı nasıl resetlerim?"
- "Güvenlik önlemleri nelerdir?"
- "Kurulum adımlarını göster"
- "Hangi araçlara ihtiyacım var?"

## Sorun Giderme (Troubleshooting)

### "Index not loaded" hatası
`python src/main.py` ile önce dökümanları işleyin.

### Port kullanımda
```bash
# Backend için (8000)
lsof -ti:8000 | xargs kill -9

# Frontend için (3000)
lsof -ti:3000 | xargs kill -9
```

### Memory hatası
`config.py`'de `CHUNK_SIZE`'ı azaltın.

### Model indirme yavaş
İlk çalıştırmada modeller (~2GB) indirilir. İnternet bağlantınızı kontrol edin.

## Klasör Yapısı

```
rag_project/
├── data/              # Buraya PDF'leri koy
├── output/            # İşlenmiş veriler buraya kaydedilir
│   ├── chunks.json
│   ├── embeddings.npy
│   ├── images/        # Çıkarılan resimler
│   └── faiss_index/
├── src/               # Python backend kodu
├── web/               # React frontend
└── api.py             # FastAPI server
```

## Faydalı Komutlar

```bash
# CLI arayüzü ile test et (web UI olmadan)
source venv/bin/activate
python src/interactive_search.py

# API health check
curl http://localhost:8000/api/health

# Yeni PDF ekle ve yeniden işle
cp new_file.pdf data/
python src/main.py

# Logs'ları temizle
rm -rf output/
```

## Performans İpuçları

1. **İlk çalıştırma:** Model indirme nedeniyle yavaş olabilir
2. **CPU kullanımı:** İşleme sırasında yüksek CPU kullanımı normal
3. **RAM:** ~4GB RAM gerekli
4. **Sorgu hızı:** ~2 saniye (reranking ile)
5. **Batch işleme:** Birden fazla PDF'i birlikte işleyin

## Yardım

Detaylı bilgi için `README.md` dosyasına bakın.

---

**Not:** GPU olmadan çalışır ama GPU ile 5-10x daha hızlı olur.
