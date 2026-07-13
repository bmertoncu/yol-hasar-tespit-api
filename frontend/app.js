// DOM Elementleri
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const img = document.getElementById('img');
const canvas = document.getElementById('canvas');
const container = document.getElementById('container');
const sendBtn = document.getElementById('sendBtn');
const ctx = canvas.getContext('2d');

// Sabitler
const CONFIDENCE_THRESHOLD = 0.71;
const API_BASE_URL = 'https://true-dingos-eat.loca.lt'; // Ngrok'a geçince burayı güncellemeyi unutma
const ADANA_BOUNDS = { minLat: 36.0, maxLat: 38.5, minLon: 34.0, maxLon: 37.0 };

let sessionId = localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
localStorage.setItem('sessionId', sessionId);
let lastLocation = "Konum belirlenemedi";

/**
 * Konum Fonksiyonu - Sadece Gerçek GPS (IP Sapması İptal Edildi)
 */
async function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve("Konum belirlenemedi");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => resolve(`${pos.coords.latitude},${pos.coords.longitude}`),
            (err) => {
                console.warn("GPS hatası:", err.message);
                resolve("Konum belirlenemedi");
            },
            { 
                enableHighAccuracy: true, // Zorunlu olarak en doğru GPS donanımını kullanır
                timeout: 15000,           // Aramak için 15 saniye mühlet verir
                maximumAge: 0             // Önbellekteki eski konumu değil, o anki taze konumu ister
            }
        );
    });
}

// Görsel Yükleme
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 1. Konum Kontrol Döngüsü
    let loc = await getUserLocation();
    
    // Eğer net GPS verisi alınamadıysa işlemi kesin olarak durdur
    if (loc === "Konum belirlenemedi") {
        alert("Konum belirlenemedi. Cihazınızın GPS (Konum) servisinin açık olduğundan ve tarayıcıya izin verdiğinizden emin olup tekrar deneyin.");
        location.reload(); 
        return;
    }

    // 2. Adana Sınır Kontrolü (Artık IP şaşması yok, %100 gerçek koordinat)
    const [lat, lon] = loc.split(',').map(Number);
    if (lat < ADANA_BOUNDS.minLat || lat > ADANA_BOUNDS.maxLat || 
        lon < ADANA_BOUNDS.minLon || lon > ADANA_BOUNDS.maxLon) {
        alert("Sistemimiz şu an sadece Adana sınırları içinde çalışmaktadır.");
        return;
    }

    lastLocation = loc;

    // 3. Görseli İşle
    img.src = URL.createObjectURL(file);
    container.style.display = 'block';
    await new Promise(resolve => img.onload = resolve);
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData,
            headers: { 'X-Session-ID': sessionId }
        });

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
            alert("Çukur tespit edilemedi.");
            location.reload();
        }
    } catch (err) { 
        console.error("Detaylı Hata:", err);
        alert("Sunucu ile bağlantı kurulamadı. Tünel adresi aktif mi?"); 
    }
});

// Rapor Gönderme
sendBtn.addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, location: lastLocation })
        });
        if (response.ok) {
            alert("Rapor başarıyla iletildi!");
            location.reload();
        }
    } catch (err) { alert("Rapor gönderilemedi."); }
});