/**
 * Yol Hasar Tespit Sistemi - Frontend Kontrolcüsü
 * Sorumluluk: Konum verisi toplama, görsel yükleme, API haberleşmesi, güvenlik ve sonuç görselleştirme.
 */

// DOM Element Referansları
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const img = document.getElementById('img');
const canvas = document.getElementById('canvas');
const container = document.getElementById('container');
const sendBtn = document.getElementById('sendBtn');
const ctx = canvas.getContext('2d');

// Sabitler
const CONFIDENCE_THRESHOLD = 0.71; // Modelin tespitlerine güven eşiği
const API_BASE_URL = 'http://127.0.0.1:8000';

// Oturum ve Güvenlik Yönetimi
let sessionId = localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
localStorage.setItem('sessionId', sessionId);
let lastLocation = "Location_Unknown";
let authToken = null; // JWT Token için değişken

/**
 * Otomatik Kimlik Doğrulama (Geliştirme / Prototip İçin)
 * Sayfa yüklendiğinde arka planda API'den token alır.
 */
async function authenticateSystem() {
    try {
        const params = new URLSearchParams();
        params.append('username', 'admin');
        params.append('password', 'adana123');

        const response = await fetch(`${API_BASE_URL}/token`, {
            method: 'POST',
            body: params
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            console.log("Sisteme başarıyla giriş yapıldı, yetki token'ı alındı.");
        } else {
            console.error("Kimlik doğrulama başarısız. API erişimi reddedilebilir.");
        }
    } catch (err) {
        console.error("Yetkilendirme sunucusuna ulaşılamadı:", err);
    }
}

// Sayfa yüklendiği gibi sessizce token al
window.addEventListener('DOMContentLoaded', authenticateSystem);

/**
 * Hibrid Konum Fonksiyonu: 
 * Modern tarayıcı API'sini kullanır, başarısızlık durumunda IP üzerinden konum tahmini yapar.
 */
async function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve("Geolocation_Not_Supported");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => resolve(`${pos.coords.latitude},${pos.coords.longitude}`),
            async (err) => {
                console.warn(`GPS erişimi reddedildi veya başarısız: ${err.message}. IP tabanlı servis kullanılıyor.`);
                try {
                    const response = await fetch('https://ipapi.co/json/');
                    const data = await response.json();
                    resolve(data.latitude && data.longitude ? `${data.latitude},${data.longitude}` : "Location_Fetch_Failed");
                } catch (e) {
                    resolve("IP_API_Failed");
                }
            },
            { enableHighAccuracy: false, timeout: 5000, maximumAge: 0 }
        );
    });
}

// Görsel Yükleme ve Analiz Akışı
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Token kontrolü
    if (!authToken) {
        alert("Sisteme henüz güvenli bağlantı sağlanamadı, lütfen sayfayı yenileyin.");
        return;
    }

    // Görseli arayüzde önizle
    img.src = URL.createObjectURL(file);
    container.style.display = 'block';
    await new Promise(resolve => img.onload = resolve);
    
    // Canvas boyutlarını görsel ile eşitle
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    // Konum verisini güncelle
    lastLocation = await getUserLocation();

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Backend'e analiz isteği gönder (JWT Token Header'a Eklendi)
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData,
            headers: { 
                'X-Session-ID': sessionId, 
                'X-Location': lastLocation,
                'Authorization': `Bearer ${authToken}` // 401 Hatasını çözen güvenlik anahtarı
            }
        });

        if (!response.ok) throw new Error(`Sunucu Hatası: ${response.status}`);
        
        const data = await response.json();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Tespitleri doğrula ve çiz
        const validDetections = data.detections?.filter(d => d.confidence >= CONFIDENCE_THRESHOLD) || [];

        if (validDetections.length > 0) {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 4;
            const scaleX = canvas.width / img.naturalWidth;
            const scaleY = canvas.height / img.naturalHeight;

            validDetections.forEach(det => {
                const [x1, y1, x2, y2] = Array.isArray(det.bbox[0]) ? det.bbox[0] : det.bbox;
                ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
            });
            sendBtn.style.display = 'block';
        } else {
            alert("Herhangi bir çukur tespit edilemedi. Lütfen farklı bir açı deneyin.");
            location.reload();
        }
    } catch (err) {
        console.error("Analiz sürecinde hata:", err);
        alert("Analiz başarısız oldu. Lütfen bağlantınızı kontrol edin.");
    }
});

// Rapor Gönderme İşlemi
sendBtn.addEventListener('click', async () => {
    try {
        // Backend'e rapor isteği gönder (JWT Token Header'a Eklendi)
        const response = await fetch(`${API_BASE_URL}/report`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` // 401 Hatasını çözen güvenlik anahtarı
            },
            body: JSON.stringify({ session_id: sessionId, location: lastLocation })
        });
        
        if (response.ok) {
            alert("Rapor belediyeye başarıyla iletildi. Katkılarınız için teşekkürler!");
            location.reload();
        } else {
            throw new Error("Rapor gönderimi başarısız.");
        }
    } catch (err) {
        alert("Bağlantı hatası: Rapor gönderilemedi.");
    }
});