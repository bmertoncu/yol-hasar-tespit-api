/**
 * Yol Hasar Tespit Sistemi - Frontend Kontrolcüsü (Güvenlik Katmanı Kaldırıldı)
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
const CONFIDENCE_THRESHOLD = 0.71; 
const API_BASE_URL = ' https://loose-colts-hear.loca.lt'; // Kendi Localtunnel adresini buraya yazmayı unutma

// Oturum Yönetimi
let sessionId = localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
localStorage.setItem('sessionId', sessionId);
let lastLocation = "Location_Unknown";

/**
 * Konum Fonksiyonu (Yüksek Hassasiyet ve İzin Kontrolü)
 */
async function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            alert("Cihazınız konum servisini desteklemiyor.");
            resolve("Geolocation_Not_Supported");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => resolve(`${pos.coords.latitude},${pos.coords.longitude}`),
            async (err) => {
                // Kullanıcı izin vermediyse veya süre yetmediyse net bir uyarı çıkar
                if (err.code === err.PERMISSION_DENIED) {
                    alert("Uyarı: Konum izni vermediğiniz için raporunuzun konumu yaklaşık olarak (IP üzerinden) hesaplanacaktır. Lütfen tarayıcı ayarlarından konum erişimine izin verin.");
                } else if (err.code === err.TIMEOUT) {
                    console.warn("GPS sinyali bulma süresi aşıldı.");
                }

                console.warn(`GPS reddedildi/başarısız: ${err.message}. IP tabanlı servis kullanılıyor.`);
                
                try {
                    const response = await fetch('https://ipapi.co/json/');
                    const data = await response.json();
                    resolve(data.latitude && data.longitude ? `${data.latitude},${data.longitude}` : "Location_Fetch_Failed");
                } catch (e) {
                    resolve("IP_API_Failed");
                }
            },
            // KRİTİK GÜNCELLEME: Yüksek hassasiyet açıldı ve bekleme süresi 15 saniyeye çıkarıldı
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    });
}

// Görsel Yükleme ve Analiz
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    img.src = URL.createObjectURL(file);
    container.style.display = 'block';
    await new Promise(resolve => img.onload = resolve);
    
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    lastLocation = await getUserLocation();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData,
            headers: { 
                'X-Session-ID': sessionId, 
                'X-Location': lastLocation,
                'Bypass-Tunnel-Reminder': 'true' // Localtunnel engelini aşmak için gerekli
            }
        });

        if (!response.ok) throw new Error(`Sunucu Hatası: ${response.status}`);
        
        const data = await response.json();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
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
            alert("Çukur tespit edilemedi. Farklı bir açı deneyin.");
            location.reload();
        }
    } catch (err) {
        console.error(err);
        alert("Analiz başarısız oldu.");
    }
});

// Rapor Gönderme
sendBtn.addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/report`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true' // Localtunnel engelini aşmak için gerekli
            },
            body: JSON.stringify({ session_id: sessionId, location: lastLocation })
        });
        
        if (response.ok) {
            alert("Rapor belediyeye başarıyla iletildi! Katkılarınız için teşekkürler.");
            location.reload();
        } else {
            throw new Error("Rapor gönderimi başarısız.");
        }
    } catch (err) {
        alert("Bağlantı hatası.");
    }
});