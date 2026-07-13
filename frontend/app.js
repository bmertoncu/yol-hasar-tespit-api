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
const API_BASE_URL = 'https://vowel-amaze-cackle.ngrok-free.dev';
const ADANA_BOUNDS = { minLat: 36.0, maxLat: 38.5, minLon: 34.0, maxLon: 37.0 };

let sessionId = localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
localStorage.setItem('sessionId', sessionId);
let lastLocation = null;

/**
 * Konum Fonksiyonu - Tüm Tarayıcılar İçin Evrensel Hata Yakalama
 */
async function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve({ error: "Tarayıcı Desteklemiyor" });
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude });
            },
            (err) => {
                let reason = "Bilinmeyen Hata";
                if (err.code === 1) reason = "İzin Reddedildi";
                if (err.code === 2) reason = "Konum Bulunamadı (Sinyal Yok)";
                if (err.code === 3) reason = "Zaman Aşımı";
                
                resolve({ error: reason });
            },
            { 
                enableHighAccuracy: false, 
                timeout: 20000,           
                maximumAge: 0             
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
    let locResult = await getUserLocation();
    
    // Evrensel Hata Yönetimi: Tüm platformlar (iOS, Android, Chrome, WhatsApp vb.) için kapsayıcı uyarı
    if (locResult.error) {
        if (locResult.error === "İzin Reddedildi") {
            alert(
                "Konum izni reddedildi veya uygulama tarafından engellendi!\n\n" +
                "👉 Linki WhatsApp/Instagram içinden açtıysanız, menüden 'Tarayıcıda Aç' (Chrome/Safari) seçeneğini kullanın.\n" +
                "👉 Normal tarayıcıdaysanız, adres çubuğundaki 'Kilit' veya adres çubuğundaki bilgi simgesine tıklayarak konum erişimine izin verin."
            );
        } else {
            alert(`Konum alınamadı: ${locResult.error}. Lütfen cihazınızın Konum (GPS) özelliğinin açık olduğundan emin olup tekrar deneyin.`);
        }
        location.reload(); 
        return;
    }

    // 2. Adana Sınır Kontrolü
    const lat = locResult.lat;
    const lon = locResult.lon;
    
    if (lat < ADANA_BOUNDS.minLat || lat > ADANA_BOUNDS.maxLat || 
        lon < ADANA_BOUNDS.minLon || lon > ADANA_BOUNDS.maxLon) {
        alert("Sistemimiz şu an sadece Adana sınırları içinde çalışmaktadır.");
        location.reload();
        return;
    }

    lastLocation = `${lat},${lon}`;

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
        alert("Sunucu ile bağlantı kurulamadı. Lütfen internet bağlantınızı kontrol edin."); 
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