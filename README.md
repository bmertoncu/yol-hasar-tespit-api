docker kurma: docker build -t yol-hasar-api
docker çalıştırma: docker run -p 8000:8000 -v "$(pwd):/app" yol-hasar-api

Bu proje, vatandaşların yollardaki hasarları (çukur, çatlak vb.) web üzerinden bildirebilmesi için geliştirilen REST tabanlı API servisidir.
Özellikler:
Vatandaşlardan gelen ihbar verilerinin (konum, hasar türü ve görsel) sisteme kaydedilmesi.
FastAPI ile hızlı ve asenkron HTTP istek yönetimi.
Uvicorn üzerinden yüksek performanslı sunucu yayını.
Kurulum ve Çalıştırma:
Terminal üzerinden repoyu bilgisayarınıza indirin (git clone komutu ile) ve vatandas-ihbar-sistemi klasörünün içine girin.
Proje dizininde Python ile bir sanal ortam oluşturun (python -m venv venv) ve aktifleştirin.
Gerekli kütüphaneleri kurmak için pip install -r requirements.txt komutunu çalıştırın.
Geliştirme sunucusunu başlatmak için uvicorn main:app --reload --host 0.0.0.0 --port 8000 komutunu girin. Sunucu varsayılan olarak localhost üzerinde 8000 portunda çalışacaktır.
(Docker şu anlık iptal edildi önümüzdeki günlerde tekrar konulacaktır.)