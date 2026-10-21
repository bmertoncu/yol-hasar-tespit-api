# Belediye Araçları Canlı Yol Hasar Tespit Sistemi

Belediye hizmet araçlarına entegre edilen kameralar aracılığıyla yollardaki çukur ve yüzey bozukluklarını otonom olarak tespit eden bilgisayarlı görü servisi.

## Özellikler
- YOLOv8 modeli ile gerçek zamanlı kamera akışı ve video üzerinden hasar tespiti.
- Ardışık karelerde aynı hasarın tekrar raporlanmasını önleyen IoU (Intersection over Union) filtresi.
- Haversine formülü ile 15 metre çap ve 5 dakika süre bazlı coğrafi mükerrer kayıt engelleme.
- JWT tabanlı araç kimlik doğrulaması ve OpenCV ile otomatik hasar işaretleme.

## Kurulum ve Çalıştırma

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Akış Testi
Farklı bir terminalde sanal ortamı aktif ederek kamera veya video akış testini başlatabilirsiniz:

```bash
python tests/test_stream.py
# veya video dosyası üzerinden test için:
python tests/test_video.py
```
