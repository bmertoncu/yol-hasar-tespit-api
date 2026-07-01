const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const img = document.getElementById('img');
const canvas = document.getElementById('canvas');
const container = document.getElementById('container');
const sendBtn = document.getElementById('sendBtn');
const ctx = canvas.getContext('2d');

let sessionId = localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
localStorage.setItem('sessionId', sessionId);
let lastLocation = "Location_Unknown"; 

// --- YENİ: HİBRİT KONUM FONKSİYONU ---
async function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve("Geolocation_Not_Supported");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => resolve(`${pos.coords.latitude},${pos.coords.longitude}`), 
            async (err) => {
                console.warn(`Tarayıcı konumu alamadı (Hata: ${err.message}). IP konumuna geçiliyor...`);
                try {
                    // B PLAN: Tarayıcı izni gerektirmeyen IP tabanlı konum
                    const ipRes = await fetch('https://ipapi.co/json/');
                    const ipData = await ipRes.json();
                    if (ipData.latitude && ipData.longitude) {
                        resolve(`${ipData.latitude},${ipData.longitude}`);
                    } else {
                        resolve("Location_Fetch_Failed");
                    }
                } catch (e) {
                    resolve("IP_API_Failed");
                }
            },
            { enableHighAccuracy: false, timeout: 5000, maximumAge: 0 }
        );
    });
}

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    img.src = URL.createObjectURL(file);
    container.style.display = 'block';
    await new Promise(resolve => img.onload = resolve);
    
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    // YENİ: Akıllı Konum fonksiyonunu çağırıyoruz
    lastLocation = await getUserLocation();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('http://127.0.0.1:8000/predict', { 
            method: 'POST', 
            body: formData,
            headers: { 
                'X-Session-ID': sessionId, 
                'X-Location': lastLocation 
            } 
        });

        if (!res.ok) throw new Error(`HTTP Hata Kodu: ${res.status}`);
        
        const data = await res.json();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (data.detections && data.detections.length > 0) {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 4;
            const scaleX = canvas.width / img.naturalWidth;
            const scaleY = canvas.height / img.naturalHeight;

            data.detections.forEach(det => {
                const [x1, y1, x2, y2] = Array.isArray(det.bbox[0]) ? det.bbox[0] : det.bbox;
                ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
            });
            sendBtn.style.display = 'block'; 
        } else {
            alert("Görselde çukur tespit edilemedi.");
            location.reload(); 
        }
    } catch (err) {
        console.error("Detaylı Hata:", err);
        alert("Analiz başarısız! Hata: " + err.message);
    }
});

sendBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                location: lastLocation
            })
        });
        
        if (response.ok) {
            alert("Rapor belediyeye iletildi, teşekkürler!");
            sendBtn.style.display = 'none'; 
            location.reload(); 
        } else {
            alert("Backend raporu alamadı. Sunucu açık mı kontrol et.");
        }
    } catch (err) {
        alert("Rapor gönderilemedi. Bağlantı hatası.");
    }
});