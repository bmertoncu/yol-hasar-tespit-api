venvi aç. source venv/bin/activate     
uvicorn'u çalıştır. uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
farklı terminal ve venv.
test scriptini çalıştır. python tests/test_stream.py     


Bu proje, araçlara entegre edilen kameralar aracılığıyla yollardaki yapısal bozuklukları otonom olarak tespit eden bilgisayarlı görü sistemidir.
Özellikler:
Eğitilmiş YOLO nesne tespit modeli ile gerçek zamanlı hasar tespiti.
Kamera akışı veya kayıtlı medya dosyaları üzerinden çıkarım (inference) yapabilme.
Tespit edilen hasarların doğruluk skorlarıyla birlikte sisteme loglanması.
Kurulum ve Çalıştırma:
Terminal üzerinden repoyu bilgisayarınıza indirin ve arac-tespit-sistemi klasörüne girin.
Kendi sanal ortamınızı oluşturun ve aktifleştirin.
Ultralytics ve diğer gereksinimleri yüklemek için pip install -r requirements.txt komutunu kullanın.
Eğittiğiniz YOLO ağırlık dosyasını (best.pt) projedeki models klasörünün içerisine yerleştirin.
Sistemi bir video dosyasında test etmek için terminale python detect.py --source data/test_video.mp4 --weights models/best.pt yazın.
Eğer doğrudan web kamerasından canlı tespit yapmak isterseniz video yolunu silip source değerine 0 yazarak kodu çalıştırın.