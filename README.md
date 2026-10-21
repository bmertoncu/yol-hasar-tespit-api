# Yol Hasar Tespit API (Vatandaş Bildirim Sistemi)

Vatandaşların yollardaki çukur ve yüzey bozukluklarını konum doğrulamalı olarak bildirebilmesi için geliştirilmiş FastAPI ve YOLOv8 tabanlı web servisi.

## Özellikler
- YOLOv8 (`best.pt`) modeli ile yüklenen görseller üzerinden çukur tespiti.
- Adana il sınırları için istemci taraflı koordinat kontrolü (Geofencing).
- `SlowAPI` ile IP bazlı istek sınırlandırma (Rate Limiting) ve dosya doğrulama.

## Kurulum ve Çalıştırma

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker ile Çalıştırma
```bash
docker build -t yol-hasar-api ./api
docker run -p 8000:8000 yol-hasar-api
```
