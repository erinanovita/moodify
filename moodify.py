import streamlit as st
import pandas as pd
import datetime
import time
import random

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Moodify - Serene Health & Mind",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Integrasi opsional Google Gemini API
try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
except ImportError:
    HAS_GEMINI_LIB = False

# --- 2. Custom CSS Modern & Serene (Dark Mode Elegan + Flexible Light Mode) ---
st.markdown(""" <style> /* Styling Dasar & Font */ .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; } /* Hide Streamlit default header/footer */ header {visibility: hidden;} footer {visibility: hidden;} /* Card Design - Serene Theme */ .moodify-card { background-color: var(--secondary-background-color, #1e293b); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 24px; margin-bottom: 20px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); transition: all 0.3s ease; } .moodify-card:hover { border-color: rgba(59, 130, 246, 0.4); } /* Hero Banner */ .moodify-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #ffffff !important; border-radius: 24px; padding: 28px; margin-bottom: 24px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 12px 30px rgba(15, 23, 42, 0.4); } .moodify-banner h2, .moodify-banner h3, .moodify-banner p { color: #ffffff !important; } /* Badge Status */ .badge-pill { background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; display: inline-block; margin-bottom: 10px; } /* Custom Result Box */ .result-box { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #3b82f6; border-radius: 16px; padding: 20px; margin-top: 15px; } /* Tab Custom Styling */ .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 8px; } .stTabs [data-baseweb="tab"] { border-radius: 16px !important; padding: 8px 18px !important; font-size: 14px !important; font-weight: 600 !important; } .stTabs [aria-selected="true"] { background-color: rgba(59, 130, 246, 0.2) !important; color: #3b82f6 !important; } </style> """, unsafe_allow_html=True)

# --- 3. Session State Initialization ---
if "mood_logs" not in st.session_state:
    st.session_state.mood_logs = [
        {"Waktu": "2026-09-14 09:00", "Mood": "Baik 🙂", "Intensitas": 7, "Pemicu": "Pekerjaan", "Catatan": "Menyelesaikan proyek tepat waktu."},
        {"Waktu": "2026-09-15 10:30", "Mood": "Sangat Baik 😄", "Intensitas": 9, "Pemicu": "Kesehatan", "Catatan": "Tidur nyenyak 8 jam."}
    ]

if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = [
        {"tanggal": "2026-09-15", "judul": "Hari yang Indah & Tenang ✨", "isi": "Hari ini saya menyadari betapa pentingnya mengambil jeda sejenak dari hiruk-pikuk pekerjaan. Berjalan sebentar di pagi hari memberikan kesegaran pikiran yang luar biasa.", "emoji": "😄"},
        {"tanggal": "2026-09-14", "judul": "Langkah Kecil Membangun Kepercayaan Diri 🌟", "isi": "Mencoba menolak permintaan kerja berlebih tanpa rasa bersalah. Ternyata menetapkan batasan (boundaries) itu sangat melegakan.", "emoji": "😌"}
    ]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant", 
            "content": "Halo! Saya **AI Teman Curhat Moodify**. Saya di sini siap mendengarkan cerita, kecemasan, atau keluh kesahmu secara mendalam tanpa menghakimi. Apa yang sedang memenuhi pikiran atau perasaanmu hari ini?"
        }
    ]

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

if "haid_data" not in st.session_state:
    st.session_state.haid_data = {
        "tgl_mulai": datetime.date(2026, 9, 1),
        "durasi_siklus": 28,
        "lama_haid": 6
    }

if "pengingat" not in st.session_state:
    st.session_state.pengingat = [
        {"id": 1, "waktu": datetime.time(20, 0), "pesan": "Waktunya refleksi & isi jurnal harianmu 📝", "aktif": True, "last_triggered": None},
        {"id": 2, "waktu": datetime.time(12, 0), "pesan": "Ambil napas dalam-dalam & istirahatkan mata 💧", "aktif": True, "last_triggered": None}
    ]

if "habits" not in st.session_state:
    st.session_state.habits = [
        {"nama": "Minum Air Putih 2 Liter", "kategori": "Kesehatan", "streak": 5, "selesai_hari_ini": True},
        {"nama": "Meditasi / Olah Napas 10 Menit", "kategori": "Mental", "streak": 3, "selesai_hari_ini": False},
        {"nama": "Tidur Cepat (Sebelum Jam 11 Malam)", "kategori": "Istirahat", "streak": 2, "selesai_hari_ini": True},
        {"nama": "Jalan Kaki / Olahraga Ringan", "kategori": "Fisik", "streak": 1, "selesai_hari_ini": False}
    ]

# --- 4. Notifikasi Toast In-App ---
now = datetime.datetime.now()
current_time = now.time()
today_date_str = now.strftime("%Y-%m-%d")

for p in st.session_state.pengingat:
    if p["aktif"]:
        if current_time >= p["waktu"] and p.get("last_triggered") != today_date_str:
            st.toast(f"🔔 **PENGINGAT:** {p['pesan']}", icon="🌱")
            p["last_triggered"] = today_date_str

# --- 5. Header Utama & Navigasi ---
st.markdown("<h1 style='text-align: center; margin-bottom: 2px;'>🌱 Moodify</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.8; margin-bottom: 20px;'>Ruang Aman untuk Tumbuh, Refleksi, dan Mengenal Diri</p>", unsafe_allow_html=True)

nav_tabs = st.tabs([
    "🏠 Beranda", 
    "📊 Mood Tracker", 
    "🎯 Habit Tracker",
    "🩸 Siklus Haid", 
    "💬 Ruang Curhat AI", 
    "📝 Jurnal", 
    "🧩 Tes Psikologi", 
    "📚 Edukasi Mental", 
    "🧘 Relaksasi",
    "⏰ Pengingat"
])

# ==========================================
# 1. BERANDA (HOME)
# ==========================================
with nav_tabs[0]:
    afirmasi_list = [
        "Perasaanmu valid. Kamu berhak mengambil jeda tanpa perlu merasa bersalah.",
        "Masa lalu tidak mendefinisikan siapa dirimu hari ini. Setiap hari adalah lembaran baru.",
        "Kamu tidak harus menyelesaikan semua hal sekaligus. Cukup fokus pada satu langkah kecil.",
        "Bersikaplah lembut pada dirimu sendiri. Kamu telah berjuang sangat baik hingga titik ini.",
        "Batasan yang kamu buat adalah bentuk rasa hormat dan kasih sayang pada dirimu sendiri."
    ]
    afirmasi_today = random.choice(afirmasi_list)
    
    st.markdown(f""" <div class='moodify-banner'> <span class='badge-pill'>AFIRMASI HARIAN</span> <h3 style='margin-top: 10px; font-weight: 600;'>"{afirmasi_today}"</h3> <p style='font-size: 13px; opacity: 0.85; margin-top: 10px;'>Pesan baru siap menyemangati harimu setiap kali dibuka.</p> </div> """, unsafe_allow_html=True)
    
    st.subheader("Ringkasan Kesehatan Mentalmu")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown(f""" <div class='moodify-card' style='text-align: center;'> <div style='font-size: 32px;'>📊</div> <h4>Mood Terakhir</h4> <p style='font-size: 18px; font-weight: bold; color: #60a5fa;'> {st.session_state.mood_logs[-1]['Mood'] if st.session_state.mood_logs else 'Belum ada'} </p> </div> """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown(f""" <div class='moodify-card' style='text-align: center;'> <div style='font-size: 32px;'>📝</div> <h4>Entri Jurnal</h4> <p style='font-size: 18px; font-weight: bold; color: #60a5fa;'>{len(st.session_state.journal_entries)} Catatan Tersimpan</p> </div> """, unsafe_allow_html=True)
        
    with col_c:
        completed_habits = sum([1 for h in st.session_state.habits if h['selesai_hari_ini']])
        st.markdown(f""" <div class='moodify-card' style='text-align: center;'> <div style='font-size: 32px;'>🎯</div> <h4>Kebiasaan Hari Ini</h4> <p style='font-size: 18px; font-weight: bold; color: #60a5fa;'>{completed_habits} / {len(st.session_state.habits)} Selesai</p> </div> """, unsafe_allow_html=True)

# ==========================================
# 2. MOOD TRACKER
# ==========================================
with nav_tabs[1]:
    st.subheader("📊 Pelacak Suasana Hati & Emosi")
    st.write("Catat perubahan emosimu untuk mengenali pola psikologis dan pemicunya.")
    
    col_input, col_view = st.columns([1, 1.2])
    
    with col_input:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### ✍️ Catat Mood Saat Ini")
        mood_pilihan = st.select_slider(
            "Bagaimana perasaanmu secara umum?",
            options=["Sangat Buruk 😭", "Buruk 🙁", "Netral 😐", "Baik 🙂", "Sangat Baik 😄"],
            value="Baik 🙂"
        )
        intensitas = st.slider("Skala Intensitas Emosi (1-10):", 1, 10, 7)
        pemicu = st.multiselect(
            "Apa faktor pemicu utama emosimu?",
            ["Pekerjaan/Tugas", "Hubungan Pasangan", "Keluarga", "Teman/Sosial", "Kesehatan Fisik", "Kualitas Tidur", "Finansial", "Cuaca/Lingkungan"]
        )
        catatan_mood = st.text_area("Catatan singkat perasaanmu:", placeholder="Misal: Merasa lelah setelah rapat, tapi senang proyek lancar.", height=100)
        
        if st.button("Simpan Catatan Mood", use_container_width=True):
            st.session_state.mood_logs.append({
                "Waktu": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Mood": mood_pilihan,
                "Intensitas": intensitas,
                "Pemicu": ", ".join(pemicu) if pemicu else "Tidak ada spesifik",
                "Catatan": catatan_mood if catatan_mood else "-"
            })
            st.success("Mood berhasil dicatat!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_view:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Tren & Riwayat Intensitas")
        if st.session_state.mood_logs:
            df_mood = pd.DataFrame(st.session_state.mood_logs)
            st.line_chart(df_mood["Intensitas"])
            
            st.markdown("##### 📜 Riwayat Terbaru")
            st.dataframe(df_mood[["Waktu", "Mood", "Intensitas", "Pemicu", "Catatan"]].tail(5), use_container_width=True)
        else:
            st.info("Belum ada riwayat mood. Mulai catat emosimu di samping!")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 3. HABIT TRACKER (BARU)
# ==========================================
with nav_tabs[2]:
    st.subheader("🎯 Pelacak Kebiasaan Positif (Habit Tracker)")
    st.write("Membangun kebiasaan kecil setiap hari adalah fondasi utama kesehatan mental yang stabil.")
    
    col_h_left, col_h_right = st.columns([1, 1])
    
    with col_h_left:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### ✨ Daftar Kebiasaan Hari Ini")
        for idx, h in enumerate(st.session_state.habits):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{h['nama']}** <br><span style='font-size: 11px; opacity: 0.7;'>Kategori: {h['kategori']} | 🔥 Streak: {h['streak']} hari</span>", unsafe_allow_html=True)
            with c2:
                status_selesai = st.checkbox("Selesai", value=h['selesai_hari_ini'], key=f"habit_{idx}")
                if status_selesai != h['selesai_hari_ini']:
                    st.session_state.habits[idx]['selesai_hari_ini'] = status_selesai
                    if status_selesai:
                        st.session_state.habits[idx]['streak'] += 1
                    else:
                        st.session_state.habits[idx]['streak'] = max(0, st.session_state.habits[idx]['streak'] - 1)
                    st.rerun()
            with c3:
                if st.button("🗑️ Hapus", key=f"del_habit_{idx}"):
                    st.session_state.habits.pop(idx)
                    st.rerun()
            st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_h_right:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### ➕ Tambah Kebiasaan Baru")
        nama_habit_baru = st.text_input("Nama Kebiasaan:", placeholder="Misal: Membaca 10 halaman buku")
        kategori_habit = st.selectbox("Pilih Kategori:", ["Kesehatan", "Mental", "Fisik", "Istirahat", "Produktivitas", "Spiritual"])
        
        if st.button("Simpan Kebiasaan Baru", use_container_width=True):
            if nama_habit_baru:
                st.session_state.habits.append({
                    "nama": nama_habit_baru,
                    "kategori": kategori_habit,
                    "streak": 1,
                    "selesai_hari_ini": False
                })
                st.success("Kebiasaan berhasil ditambahkan!")
                st.rerun()
            else:
                st.warning("Nama kebiasaan tidak boleh kosong.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 4. SIKLUS HAID & HORMON
# ==========================================
with nav_tabs[3]:
    st.subheader("🩸 Siklus Haid & Pengaruh Hormonal")
    st.write("Perubahan hormon sangat memengaruhi suasana hati, energi, dan kecemasan. Pantau siklusmu di sini.")
    
    col_h1, col_h2 = st.columns([1, 1.2])
    
    with col_h1:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚙️ Pengaturan Kalender Siklus")
        
        tgl_haid = st.date_input("Hari Pertama Haid Terakhir:", value=st.session_state.haid_data["tgl_mulai"])
        durasi_siklus = st.number_input("Rata-rata Panjang Siklus (Hari):", min_value=21, max_value=40, value=st.session_state.haid_data["durasi_siklus"])
        lama_haid = st.number_input("Lama Periode Haid (Hari):", min_value=3, max_value=10, value=st.session_state.haid_data["lama_haid"])
        
        if st.button("Perbarui Siklus", use_container_width=True):
            st.session_state.haid_data = {"tgl_mulai": tgl_haid, "durasi_siklus": durasi_siklus, "lama_haid": lama_haid}
            st.success("Data siklus berhasil diperbarui!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_h2:
        start_date = st.session_state.haid_data["tgl_mulai"]
        cycle_len = st.session_state.haid_data["durasi_siklus"]
        period_len = st.session_state.haid_data["lama_haid"]
        
        today = datetime.date.today()
        next_period = start_date + datetime.timedelta(days=cycle_len)
        fertile_start = start_date + datetime.timedelta(days=cycle_len - 16)
        fertile_end = start_date + datetime.timedelta(days=cycle_len - 12)
        day_in_cycle = (today - start_date).days + 1
        
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown(f"#### 📅 Siklus Saat Ini: **Hari ke-{day_in_cycle}**")
        st.write(f"🩸 **Estimasi Haid Berikutnya:** {next_period.strftime('%d %B %Y')}")
        st.write(f"🌸 **Estimasi Masa Subur:** {fertile_start.strftime('%d %b')} - {fertile_end.strftime('%d %b %Y')}")
        
        st.markdown("---")
        st.markdown("##### 🧠 Analisis Kondisi Psikologis & Hormon:")
        if day_in_cycle <= period_len:
            st.warning("<b>Fase Menstruasi (Hari 1-5):</b> Estrogen & Progesteron berada di titik terendah. Efek: Tubuh mudah lelah, kram, dan emosi sensitif. <b>Saran:</b> Istirahat ekstra, minum air hangat, & kurangi kafein.")
        elif day_in_cycle <= (cycle_len - 14):
            st.success("<b>Fase Folikuler (Hari 6-13):</b> Kadar Estrogen meningkat pesat. Efek: Energi melonjak, suasana hati ceria, konsentrasi tinggi, dan percaya diri. <b>Saran:</b> Waktu terbaik untuk berolahraga & menyelesaikan tugas berat.")
        elif day_in_cycle <= (cycle_len - 10):
            st.info("<b>Fase Ovulasi (Hari 14-16):</b> Puncak hormon Estrogen & Luteinizing. Efek: Bersosialisasi lebih menyenangkan, komunikasi lancar, dan dorongan sosial kuat.")
        else:
            st.error("<b>Fase Luteal / PMS (Hari 17-28):</b> Progesteron naik lalu turun tajam. Efek: Rentan cemas, overthinking, perubahan mood mendadak, atau <i>brain fog</i>. <b>Saran:</b> Lakukan relaksasi, validasi emosimu, dan hindari keputusan impulsif.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. RUANG CURHAT AI CERDAS (POWERED BY GEMINI)
# ==========================================
with nav_tabs[4]:
    st.subheader("💬 Ruang Curhat AI Cerdas")
    st.write("Tempat aman untuk menumpahkan seluruh isi hati. AI diprogram sebagai teman curhat hangat, cerdas, dan empatis tanpa menghakimi.")
    
    # Pengaturan API Key Gemini
    with st.expander("🔑 Pengaturan Integrasi Gemini API (Klik di sini)", expanded=not bool(st.session_state.gemini_api_key)):
        st.write("Masukkan Google Gemini API Key milikmu agar AI terhubung langsung ke model Google Gemini resmi. Jika dikosongkan, aplikasi menggunakan mesin respons empati lokal.")
        api_input = st.text_input("Gemini API Key:", value=st.session_state.gemini_api_key, type="password", placeholder="AIzaSy...")
        col_k1, col_k2 = st.columns([1, 4])
        with col_k1:
            if st.button("Simpan Key", use_container_width=True):
                st.session_state.gemini_api_key = api_input.strip()
                st.success("API Key berhasil disimpan!")
                st.rerun()
        with col_k2:
            if st.session_state.gemini_api_key:
                st.markdown("<span style='color: #4ade80; font-weight: bold;'>🟢 Gemini API Key Terpasang & Aktif</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #fbbf24;'>🟡 Menggunakan Mesin Offline Bawaan</span>", unsafe_allow_html=True)

    # Box Percakapan
    st.markdown("<div class='moodify-card' style='max-height: 480px; overflow-y: auto;'>", unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    st.markdown("</div>", unsafe_allow_html=True)
            
    if user_prompt := st.chat_input("Tuliskan apa yang kamu rasakan atau pikirkan di sini..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.rerun()

    # Generate AI Response
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        user_msg = st.session_state.chat_history[-1]["content"]
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            used_gemini = False
            reply_text = ""
            
            # 1. Panggil Gemini API dengan Fallback Model Otomatis yang Aman
            if st.session_state.gemini_api_key and HAS_GEMINI_LIB:
                try:
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    
                    system_prompt = (
                        "Kamu adalah 'Moodify AI', seorang psikolog & teman curhat yang sangat empatis, hangat, ramah, intuitif, dan responsif. "
                        "Gaya bicaramu seperti teman baik yang bijak dan penuh kasih. "
                        "Aturan interaksi:\n"
                        "1. Selalu validasi emosi dan perasaan pengguna terlebih dahulu.\n"
                        "2. Jawab secara kontekstual dan dinamis berdasarkan seluruh percakapan sebelumnya.\n"
                        "3. Jangan mengulang-ulang kalimat template atau salam yang sama.\n"
                        "4. Berikan pandangan yang menenangkan dan 1-2 pertanyaan pemantik atau saran praktis jika relevan.\n"
                        "5. Gunakan bahasa Indonesia yang santai, hangat, dan luwes."
                    )
                    
                    model_candidates = [
                        'gemini-3.8-flash', 
                        'gemini-3.7-flash', 
                        'gemini-3.6-flash', 
                        'gemini-3.5-flash', 
                        'gemini-3.1-pro-preview', 
                        'gemini-2.5-flash',
                        'gemini-1.5-flash'
                    ]
                    selected_model = None
                    
                    for m_name in model_candidates:
                        try:
                            test_model = genai.GenerativeModel(model_name=m_name)
                            selected_model = m_name
                            break
                        except Exception:
                            continue
                            
                    if not selected_model:
                        selected_model = 'gemini-1.5-flash'
                    
                    model = genai.GenerativeModel(
                        model_name=selected_model,
                        system_instruction=system_prompt
                    )
                    
                    gemini_history = []
                    for h in st.session_state.chat_history[:-1]:
                        role = "user" if h["role"] == "user" else "model"
                        gemini_history.append({"role": role, "parts": [h["content"]]})
                    
                    chat_session = model.start_chat(history=gemini_history)
                    gemini_response = chat_session.send_message(user_msg)
                    reply_text = gemini_response.text
                    used_gemini = True
                    
                except Exception as e:
                    reply_text = ""
                    st.toast(f"⚠️ Catatan API: Mengalihkan ke mode offline karena gangguan jaringan/key.", icon="⚠️")
            
            # 2. Offline Empathy Generator
            if not used_gemini:
                u = user_msg.lower()
                
                if any(w in u for w in ["sedih", "nangis", "kecewa", "patah hati", "hancur", "sepi", "ditinggal"]):
                    reply_text = random.choice([
                        "Aku benar-benar merasakan kepedihan dari ceritamu. Menangis atau merasa hancur adalah respons alami ketika hatimu sedang terluka. Luapkan saja semuanya di sini, kamu aman. Apa hal terberat yang paling menyakitkan dari situasi ini?",
                        "Rasa sedih itu seperti ombak, terkadang terasa sangat menggulung dan menyiksa. Tapi ingat, kamu tidak sendirian menghadapinya. Ceritakan padaku, apa yang paling kamu butuhkan dari dirimu atau orang sekitar saat ini?"
                    ])
                elif any(w in u for w in ["cemas", "overthinking", "takut", "bingung", "panik", "pusing"]):
                    reply_text = random.choice([
                        "Pikiran yang berputar tanpa henti memang sangat menguras tenaga. Sering kali ketakutan di pikiran kita terasa jauh lebih menakutkan daripada kenyataan. Coba ambil napas dalam 3 detik... hembuskan. Dari semua skenario yang dipikirkan, mana yang terasa paling mengganggu?",
                        "Overthinking sering muncul saat kita mencoba mengontrol hal-hal di luar kendali kita. Mari kita urai pelan-pelan: apakah ada satu hal kecil yang bisa kamu lakukan atau selesaikan sekarang juga?"
                    ])
                elif any(w in u for w in ["capek", "lelah", "stres", "burnout", "penat", "muak"]):
                    reply_text = random.choice([
                        "Rasa lelah fisik dan emosional yang kamu pikul itu nyata. Kamu sudah bertahan sangat jauh, dan bersikap lelah itu wajar sekali. Bolehkah kamu mengizinkan dirimu berhenti sejenak dan beristirahat tanpa rasa bersalah hari ini?",
                        "Tubuh dan pikiranmu sedang memberi sinyal bahwa kapasitasmu sudah penuh. Jangan dipaksa terus berjalan. Apa aktivitas santai yang paling bisa membuatmu merasa lebih rileks saat ini?"
                    ])
                elif any(w in u for w in ["makasih", "terima kasih", "makasi", "thanks", "ok", "oke"]):
                    reply_text = "Sama-sama! Aku selalu ada di sini kapan pun kamu butuh ruang untuk bercerita atau sekadar melepas lelah. Jangan ragu untuk sapa aku lagi ya! 🤗"
                else:
                    reply_text = (
                        f"Aku mendengarkanmu dengan penuh perhatian. Mengungkapkan isi pikiran lewat kata-kata seperti ini adalah bentuk kepedulianmu pada kesehatan mentalmu sendiri.\n\n"
                        f"Bagaimana rasanya setelah mengungkapkan hal itu? Ada bagian lain dari ceritamu yang ingin kamu luapkan lebih dalam?"
                    )

            full_resp = ""
            for words in reply_text.split(" "):
                full_resp += words + " "
                time.sleep(0.02)
                message_placeholder.markdown(full_resp + "▌")
            message_placeholder.markdown(full_resp)
            
        st.session_state.chat_history.append({"role": "assistant", "content": reply_text})

# ==========================================
# 6. JURNAL PRIBADI REFLEKTIF
# ==========================================
with nav_tabs[5]:
    st.subheader("📝 Jurnal Refleksi Diri")
    st.write("Menulis jurnal (*journaling*) secara terbukti ilmiah membantu mengurai kecemasan dan meningkatkan kesadaran emosional.")
    
    col_j1, col_j2 = st.columns([1, 1.2])
    
    with col_j1:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### ✍️ Tulis Entri Jurnal Baru")
        judul_jurnal = st.text_input("Judul Catatan:")
        emoji_jurnal = st.selectbox("Emoji Representasi Mood:", ["😄 Ceria", "😌 Tenang", "😐 Netral", "😔 Sedih", "😭 Hancur", "🧘 Bermeditasi"])
        
        prompt_pilihan = st.selectbox("Gunakan Pertanyaan Pemantik Refleksi (Opsional):", [
            "-- Pilih Prompt --",
            "Apa 3 hal kecil yang patut aku syukuri hari ini?",
            "Pikiran apa yang paling menyita energiku hari ini dan bagaimana aku meresponsnya?",
            "Apa hal terpenting yang dipelajari oleh diriku hari ini?",
            "Pesan penuh kasih sayang untuk diriku di masa depan..."
        ])
        
        if prompt_pilihan != "-- Pilih Prompt --":
            st.info(f"💡 **Prompt:** {prompt_pilihan}")
            
        isi_jurnal = st.text_area("Isi Catatan Jurnalmu:", height=180, placeholder="Tuliskan dengan bebas tanpa ragu...")
        
        if st.button("Simpan ke Jurnal Pribadi", use_container_width=True):
            if judul_jurnal and isi_jurnal:
                st.session_state.journal_entries.insert(0, {
                    "tanggal": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "judul": judul_jurnal,
                    "isi": isi_jurnal,
                    "emoji": emoji_jurnal.split()[0]
                })
                st.success("Entri jurnal tersimpan!")
                st.rerun()
            else:
                st.warning("Judul dan isi catatan wajib diisi.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_j2:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### 📖 Riwayat & Koleksi Jurnal")
        
        search_query = st.text_input("🔍 Cari dalam jurnal...", placeholder="Ketik kata kunci...")
        
        filtered_entries = st.session_state.journal_entries
        if search_query:
            filtered_entries = [e for e in filtered_entries if search_query.lower() in e['judul'].lower() or search_query.lower() in e['isi'].lower()]
            
        if filtered_entries:
            for j in filtered_entries:
                st.markdown(f""" <div style='background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 16px; margin-bottom: 12px;'> <div style='display: flex; justify-content: space-between; align-items: center;'> <span class='badge-pill'>{j['tanggal']}</span> <span style='font-size: 24px;'>{j['emoji']}</span> </div> <h4 style='margin: 8px 0; color: #60a5fa;'>{j['judul']}</h4> <p style='font-size: 14px; opacity: 0.9; line-height: 1.6;'>{j['isi']}</p> </div> """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada catatan jurnal yang cocok.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 7. TES PSIKOLOGI LENGKAP (SKALA LIKERT 20 PERTANYAAN)
# ==========================================
with nav_tabs[6]:
    st.subheader("🧩 Kuis & Tes Refleksi Diri Lengkap (Skala Likert)")
    st.write("Jawab 20 pernyataan komprehensif berikut untuk evaluasi mendalam kepribadian MBTI, Inner Child, dan Gaya Hubunganmu.")
    
    tes_pilihan = st.radio(
        "Pilih Tes Psikologi:",
        ["🎭 Tes MBTI Komprehensif (20 Pertanyaan)", "🌧️ Tes Luka Inner Child & Trauma", "❤️ Tes Bahasa Cinta & Kelekatan"],
        horizontal=True
    )
    
    st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
    
    # Skala Likert Options
    skala_options = [
        "Sangat Tidak Setuju", 
        "Tidak Setuju", 
        "Netral", 
        "Setuju", 
        "Sangat Setuju"
    ]
    
    if "MBTI Komprehensif" in tes_pilihan:
        st.markdown("### 🎭 Tes MBTI 20 Pertanyaan Lengkap")
        st.write("Pilih tingkat kesesuaian pernyataan berikut dengan dirimu sehari-hari:")
        
        mbti_questions = [
            ("1. Saya merasa lebih berenergi dan bersemangat setelah berkumpul di tempat ramai.", "E"),
            ("2. Saya lebih suka merenung dan menikmati waktu sendirian di rumah setelah lelah beraktivitas.", "I"),
            ("3. Saya lebih mempercayai pengalaman nyata dan fakta praktis daripada teori abstrak.", "S"),
            ("4. Saya sering memikirkan masa depan, makna tersirat, dan pola jangka panjang.", "N"),
            ("5. Dalam mengambil keputusan, saya mengandalkan analisis logis dan objektivitas.", "T"),
            ("6. Saya sangat mempertimbangkan perasaan dan dampak emosional orang lain saat memutuskan sesuatu.", "F"),
            ("7. Saya menyukai jadwal, rencana terstruktur, dan ketepatan waktu yang jelas.", "J"),
            ("8. Saya lebih menyukai fleksibilitas, kebebasan spontan, dan membiarkan opsi terbuka.", "P"),
            ("9. Saya mudah memulai obrolan dengan orang baru yang belum saya kenal.", "E"),
            ("10. Saya lebih suka mendengarkan daripada berbicara di dalam kelompok besar.", "I"),
            ("11. Saya lebih menyukai instruksi kerja langkah demi langkah yang pasti.", "S"),
            ("12. Saya suka bereksperimen dengan cara-cara baru yang belum pernah dicoba orang lain.", "N"),
            ("13. Keadilan dan kebenaran objektif lebih penting daripada menjaga perasaan agar tidak tersinggung.", "T"),
            ("14. Harmoni kelompok dan kedamaian perasaan orang lain adalah prioritas utama saya.", "F"),
            ("15. Meja kerja atau kamar saya tertata sangat rapi dan terorganisir.", "J"),
            ("16. Saya nyaman bekerja dalam situasi yang dinamis dan berubah-ubah secara mendadak.", "P"),
            ("17. Saya merasa lelah secara mental jika harus berlama-lama sendiri tanpa interaksi sosial.", "E"),
            ("18. Saya butuh waktu jeda yang tenang untuk memproses pikiran sebelum memberikan tanggapan.", "I"),
            ("19. Saya lebih fokus pada detail nyata yang ada di hadapan saya saat ini.", "S"),
            ("20. Saya sering membayangkan berbagai kemungkinan imajinatif di luar realitas fisik.", "N")
        ]
        
        user_scores_mbti = {}
        for idx, (q_text, dim) in enumerate(mbti_questions):
            ans = st.radio(q_text, skala_options, key=f"mbti_q_{idx}", index=2)
            user_scores_mbti[idx] = (dim, skala_options.index(ans) - 2) # Skala dari -2 (Sangat Tidak Setuju) sampai +2 (Sangat Setuju)
            
        if st.button("Hitung Hasil Tes MBTI Komprehensif", use_container_width=True):
            # Kalkulasi sederhana berdasarkan skor dimensi
            dim_sums = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
            for idx, (dim, val) in user_scores_mbti.items():
                if val > 0:
                    dim_sums[dim] += val
                elif val < 0:
                    # Kebalikannya
                    opposite = {"E": "I", "I": "E", "S": "N", "N": "S", "T": "F", "F": "T", "J": "P", "P": "J"}
                    dim_sums[opposite[dim]] += abs(val)
                    
            res_e_i = "E" if dim_sums["E"] >= dim_sums["I"] else "I"
            res_s_n = "S" if dim_sums["S"] >= dim_sums["N"] else "N"
            res_t_f = "T" if dim_sums["T"] >= dim_sums["F"] else "F"
            res_j_p = "J" if dim_sums["J"] >= dim_sums["P"] else "P"
            final_mbti = f"{res_e_i}{res_s_n}{res_t_f}{res_j_p}"
            
            st.markdown(f""" <div class='result-box'> <h3 style='color: #60a5fa;'>Hasil Analisis MBTI Anda: {final_mbti}</h3> <p>Berdasarkan 20 pertanyaan mendalam dengan skala kesesuaian:</p> </div> """, unsafe_allow_html=True)
            
            if final_mbti in ["INFJ", "INFP"]:
                st.write("✨ **Tipe Kepribadian Intuitif & Perasa:** Anda memiliki kedalaman emosi yang luar biasa, berjiwa idealis, sangat peka terhadap dinamika perasaan orang lain, serta menyukai makna autentik dalam hidup.")
            elif final_mbti in ["INTJ", "INTP"]:
                st.write("✨ **Tipe Pemikir Mandiri (Analyst):** Anda memiliki ketajaman analitis yang tinggi, menyukai pemecahan masalah yang rumit, mandiri, dan berorientasi pada inovasi masa depan.")
            elif final_mbti in ["ENFP", "ENTP", "ENFJ", "ENTJ"]:
                st.write("✨ **Tipe Pemimpin & Penggerak (Extrovert):** Anda memiliki energi sosial yang dinamis, pandai menginspirasi orang lain, visioner, dan sangat aktif mewujudkan ide-ide besar.")
            else:
                st.write(f"✨ **Tipe Kepribadian Seimbang ({final_mbti}):** Kombinasi ketahanan mental, kepraktisan, dan kemampuan adaptasi yang sangat baik dalam menghadapi lingkungan sekitar.")

    elif "Inner Child" in tes_pilihan:
        st.markdown("### 🌧️ Tes Evaluasi Inner Child & People Pleasing")
        st.write("Seberapa setuju Anda dengan pernyataan berikut:")
        
        ic_q = [
            "1. Saya sering merasa cemas berlebihan jika orang lain menunjukkan kekecewaan kepada saya.",
            "2. Saya merasa harus selalu tampil sempurna agar layak dicintai dan dihargai.",
            "3. Saya sangat sulit berkata 'Tidak' saat diminta tolong meskipun jadwal saya sudah penuh.",
            "4. Saya sering memendam emosi sendiri karena takut dianggap merepotkan orang lain.",
            "5. Saya merasa bertanggung jawab atas kebahagiaan orang-orang di sekitar saya."
        ]
        
        ic_ans = [st.select_slider(q, skala_options, value="Netral", key=f"ic_{i}") for i, q in enumerate(ic_q)]
        
        if st.button("Analisis Inner Child", use_container_width=True):
            score_ic = sum([skala_options.index(a) for a in ic_ans])
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            if score_ic <= 7:
                st.success("🟢 **Batas Emosional Sehat:** Anda memiliki batasan diri yang baik dan tidak terbebani ekspektasi berlebih.")
            elif score_ic <= 15:
                st.warning("🟡 **Kecenderungan People Pleasing:** Anda sering mengorbankan kebutuhan pribadi demi menjaga perasaan orang lain. Mulailah belajar memprioritaskan diri sendiri.")
            else:
                st.error("🔴 **Indikasi Luka Inner Child / Beban Emosional Tinggi:** Anda membawa beban ekspektasi masa lalu yang menuntut kesempurnaan. Praktikkan self-compassion dan validasi perasaanmu.")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("### ❤️ Tes Bahasa Cinta & Kelekatan")
        ll_ans = st.radio("Manakah bentuk apresiasi yang paling membuat Anda merasa dicintai?", [
            "Mendengar kata-kata pujian & peneguhan positif (Words of Affirmation)",
            "Menghabiskan waktu kebersamaan yang berkualitas tanpa gangguan gadget (Quality Time)",
            "Menerima hadiah penuh perhatian dari orang tersayang (Receiving Gifts)",
            "Bantuan nyata meringankan pekerjaan saat lelah (Acts of Service)",
            "Sentuhan fisik penuh kehangatan seperti pelukan (Physical Touch)"
        ])
        if st.button("Lihat Hasil Bahasa Cinta", use_container_width=True):
            st.markdown(f""" <div class='result-box'> <h3 style='color: #60a5fa;'>Bahasa Cinta Utama Anda: {ll_ans}</h3> <p>Memahami bahasa cinta ini akan membantu Anda mengomunikasikan kebutuhan emosional secara jelas kepada pasangan atau orang terdekat.</p> </div> """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 8. EDUKASI MENTAL KOMPREHENSIF (DITAMBAHKAN LEBIH BANYAK)
# ==========================================
with nav_tabs[7]:
    st.subheader("📚 Edukasi & Artikel Kesehatan Mental Komprehensif")
    st.write("Kumpulan artikel mendalam untuk memperkaya wawasan psikologi, mengatasi kecemasan, dan membangun ketahanan mental.")
    
    materi_db = [
        {
            "judul": "🌀 Menghentikan Overthinking & Ruminasi Mental",
            "kategori": "Kecemasan",
            "isi": """ <b>Apa itu Overthinking?</b> Overthinking atau ruminasi adalah kecenderungan memikirkan suatu kejadian secara berulang-ulang tanpa menghasilkan solusi nyata. Hal ini memicu aktivasi amigdala (pusat rasa takut di otak) secara terus-menerus. <b>Dampak Psikologis & Fisik:</b> • Gangguan tidur kronis (insomnia). • Kelelahan mental dan otot tegang di area leher serta bahu. • Penurunan kemampuan mengambil keputusan (<i>analysis paralysis</i>). <b>Langkah Penanganan Praktis:</b> 1. <b>Brain Dump:</b> Tuliskan semua ketakutanmu di kertas dalam rentang waktu 10 menit tanpa sensor. 2. <b>Aturan 5 Menit:</b> Tanyakan pada diri, <i>"Apakah ada tindakan nyata yang bisa saya lakukan dalam 5 menit ke depan?"</i> Jika tidak, tunda memikirkannya. 3. <b>Alihkan Sensori:</b> Basuh wajah dengan air dingin untuk merangsang saraf vagus yang menenangkan detak jantung. """
        },
        {
            "judul": "🔋 Burnout vs Lelah Biasa: Cara Mengenali & Memulihkannya",
            "kategori": "Kesehatan Kerja",
            "isi": """ <b>Perbedaan Utama:</b> Lelah biasa akan berangsur hilang setelah kamu tidur nyenyak satu malam. Namun, <b>Burnout</b> adalah kondisi kelelahan emosional, fisik, dan mental kronis akibat stres berkepanjangan yang tidak tertangani. <b>3 Gejala Utama Burnout:</b> 1. <b>Exhaustion:</b> Merasa terkuras habis secara fisik dan emosional. 2. **Cynicism / Depersonalization:** Merasa sinis, acuh tak acuh, atau kehilangan makna pada pekerjaan/tugas harian. 3. **Ineffectiveness:** Merasa tidak kompeten dan semua usahamu sia-sia. <b>Strategi Pemulihan:</b> • Tetapkan <i>Hard Boundaries</i> (misal: Tidak membuka email atau pesan kerja di atas jam 8 malam). • Praktikkan <i>Micro-Rest</i> (jeda 5 menit setiap 1 jam fokus bekerja). """
        },
        {
            "judul": "🛡️ Seni Berkata 'Tidak' & Menetapkan Batasan (Boundaries)",
            "kategori": "Pengembangan Diri",
            "isi": """ <b>Mengapa Kita Sulit Berkata 'Tidak'?</b> Banyak orang tumbuh dengan keyakinan bahwa menolak permintaan orang lain adalah wujud dari sikap jahat atau egois. Padahal, tanpa batasan yang jelas, kamu sedang mengorbankan kesehatan mentalmu demi kenyamanan orang lain. <b>Cara Menolak dengan Santun & Tegas:</b> • <i>"Terima kasih sudah menawarkan, tapi kapasitas saya saat ini sedang penuh."</i> • <i>"Saya ingin sekali membantu, tapi jadwal saya tidak memungkinkan minggu ini."</i> Ingat: <b>"No" is a complete sentence.</b> Kamu tidak wajib memberikan alasan panjang lebar untuk memvalidasi penolakanmu. """
        },
        {
            "judul": "🧠 Gejala ADHD pada Dewasa & Mengatasi Executive Dysfunction",
            "kategori": "Neurodivergent",
            "isi": """ <b>Memahami ADHD Dewasa:</b> Attention Deficit Hyperactivity Disorder (ADHD) pada orang dewasa sering kali tidak terlihat sebagai hiperaktivitas fisik, melainkan sebagai kecemasan internal, <i>time blindness</i> (sulit memperkirakan waktu), dan kelupaan kronis. <b>Tanda-tanda Executive Dysfunction:</b> • Sulit memulai tugas sederhana (seperti mencuci piring atau membalas pesan) meski sangat ingin melakukannya. • <i>Hyperfocus</i> pada hal kegemaran hingga lupa makan dan waktu. """
        },
        {
            "judul": "💔 Memahami & Menyembuhkan Trauma Pengabaian (Abandonment Wound)",
            "kategori": "Psikologi Hubungan",
            "isi": """ <b>Apa itu Abandonment Wound?</b> Luka pengabaian adalah rasa takut yang mendalam akan ditinggalkan atau diabaikan oleh orang terdekat. Hal ini sering kali berakar dari pengalaman masa kecil atau hubungan masa lalu yang tidak aman. <b>Pola Perilaku yang Sering Muncul:</b> • Menuntut kepastian berlebihan dari pasangan atau teman. • Menghindari kedekatan emosional karena takut tersakiti duluan (self-sabotage). <b>Langkah Pemulihan:</b> • Belajar menjadi tempat aman bagi diri sendiri (reparenting inner child). • Komunikasikan rasa cemas secara terbuka tanpa menyalahkan orang lain. """
        },
        {
            "judul": "🌱 Mengatasi Imposter Syndrome: Merasa Bodoh Padahal Berprestasi",
            "kategori": "Karier & Mental",
            "isi": """ <b>Definisi Imposter Syndrome:</b> Kondisi psikologis di mana seseorang merasa dirinya adalah seorang 'penipu' dan sukses yang diraih hanyalah karena faktor keberuntungan, bukan kemampuan nyata. <b>Cara Mengatasinya:</b> 1. Catat setiap pencapaian kecil maupun besar dalam sebuah jurnal khusus. 2. Sadari bahwa tidak ada orang yang tahu segalanya sejak awal; belajar adalah proses seumur hidup. """
        },
        {
            "judul": "🌙 Sleep Hygiene: Panduan Ilmiah Tidur Nyenyak untuk Kesehatan Otak",
            "kategori": "Kesehatan Fisik",
            "isi": """ <b>Pentingnya Tidur Berkualitas:</b> Kurang tidur kronis secara langsung memicu penurunan suasana hati, mudah marah, dan melemahkan daya ingat otak dalam memproses emosi. <b>Tips Sleep Hygiene:</b> • Matikan layar gadget (blue light) minimal 45 menit sebelum tidur. • Jaga suhu kamar tetap sejuk dan redupkan lampu. • Hindari kafein dan makanan berat 4 jam sebelum beristirahat. """
        }
    ]
    
    for m in materi_db:
        with st.expander(f"{m['judul']} ({m['kategori']})"):
            st.markdown(m['isi'], unsafe_allow_html=True)

# ==========================================
# 9. RUANG RELAKSASI & MEDITASI
# ==========================================
with nav_tabs[8]:
    st.subheader("🧘 Ruang Relaksasi & Olah Napas")
    st.write("Gunakan fitur ini saat kamu merasa panik, cemas, atau butuh ketenangan sebelum tidur.")
    
    col_r1, col_r2 = st.columns([1, 1])
    
    with col_r1:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### 🫁 Latihan Napas Box Breathing (4-4-4-4)")
        st.write("Metode napas teruji yang digunakan untuk menenangkan sistem saraf otonom.")
        
        if st.button("Mulai Sesi Olah Napas (1 Menit)", use_container_width=True):
            status_box = st.empty()
            progress_bar = st.progress(0)
            
            for cycle in range(3):
                status_box.info(f"🌀 **Siklus {cycle+1}/3:** Tarik Napas perlahan lewat hidung (4 detik)... 🌬️")
                time.sleep(4)
                
                status_box.warning(f"⏱️ **Siklus {cycle+1}/3:** Tahan Napas (4 detik)...")
                time.sleep(4)
                
                status_box.success(f"💨 **Siklus {cycle+1}/3:** Hembuskan perlahan lewat mulut (4 detik)...")
                time.sleep(4)
                
                status_box.info(f"🧘 **Siklus {cycle+1}/3:** Tahan Kosong (4 detik)...")
                time.sleep(4)
                progress_bar.progress((cycle + 1) / 3)
                
            status_box.success("🎉 Selesai! Rasakan ketenangan di dada dan pikiranmu.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_r2:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### 🎵 Audio Musik Penenang")
        st.write("Dengarkan instrumen relaksasi untuk menemani tidur atau saat membaca.")
        st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 10. PENGINGAT ALARM & PWA
# ==========================================
with nav_tabs[9]:
    st.subheader("⏰ Pengingat Rutinitas & Aplikasi Mobile")
    st.info("📱 **Tips Tampilan HP (PWA):** Buka web aplikasi ini di Google Chrome / Safari HP kamu, lalu pilih menu **'Tambahkan ke Layar Utama' (Add to Home screen)** agar dapat dibuka langsung seperti aplikasi APK biasa!")
    
    col_p1, col_p2 = st.columns([1, 1])
    
    with col_p1:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### ➕ Tambah Pengingat Baru")
        waktu_baru = st.time_input("Pilih Waktu Alarm:", value=datetime.time(21, 0))
        pesan_baru = st.text_input("Pesan Pengingat:", placeholder="Contoh: Waktunya istirahat mata & minum air!")
        
        if st.button("Simpan Pengingat", use_container_width=True):
            if pesan_baru:
                st.session_state.pengingat.append({
                    "id": len(st.session_state.pengingat) + 1,
                    "waktu": waktu_baru,
                    "pesan": pesan_baru,
                    "aktif": True,
                    "last_triggered": None
                })
                st.success("Pengingat berhasil ditambahkan!")
                st.rerun()
            else:
                st.warning("Pesan pengingat tidak boleh kosong.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_p2:
        st.markdown("<div class='moodify-card'>", unsafe_allow_html=True)
        st.markdown("#### 📋 Daftar Pengingat Aktif")
        for idx, p in enumerate(st.session_state.pengingat):
            status_str = "🟢 Aktif" if p["aktif"] else "🔴 Non-aktif"
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{p['waktu'].strftime('%H:%M')}** - {p['pesan']} ({status_str})")
            with c2:
                if st.button("Toggle", key=f"p_toggle_{idx}"):
                    st.session_state.pengingat[idx]["aktif"] = not p["aktif"]
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)