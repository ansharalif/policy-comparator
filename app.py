import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime

st.set_page_config(
    page_title="FTF Policy Comparator (Mini App)",
    page_icon="🌍",
    layout="wide"
)

# =========================
# SAMPLE DATA (Dummy)
# =========================
CSV_DATA = """country,last_update,review_status,prevention,administrative,criminal_justice,surveillance,rehab_reintegration,women_children_notes,notes
Indonesia,2026-02-20,Green,Yes,Partial,Yes,Partial,Yes,Partial,"Pendekatan kombinasi penegakan + pencegahan"
Malaysia,2026-02-10,Yellow,Yes,Yes,Yes,Yes,Partial,Yes,"Penguatan koordinasi lintas lembaga"
Philippines,2026-01-28,Red,Partial,No,Yes,Partial,Partial,No,"Data terbatas pada aspek reintegrasi"
France,2026-02-15,Green,Yes,Yes,Yes,Yes,Yes,Yes,"Instrumen hukum dan pengawasan relatif kuat"
Germany,2026-02-12,Green,Yes,Yes,Yes,Yes,Yes,Yes,"Program reintegrasi cukup berkembang"
Turkey,2026-01-30,Yellow,Partial,Yes,Yes,Yes,Partial,Partial,"Perlu update data perempuan & anak"
Iraq,2026-01-25,Red,Partial,Partial,Yes,Partial,No,No,"Gap data rehabilitasi masih besar"
Kazakhstan,2026-02-05,Yellow,Yes,Yes,Yes,Partial,Yes,Yes,"Menarik untuk pembelajaran repatriasi"
"""

df = pd.read_csv(StringIO(CSV_DATA))

# =========================
# HELPERS
# =========================
POLICY_COLUMNS = [
    "prevention",
    "administrative",
    "criminal_justice",
    "surveillance",
    "rehab_reintegration",
    "women_children_notes",
]

CATEGORY_LABELS = {
    "prevention": "Prevention",
    "administrative": "Administrative Measures",
    "criminal_justice": "Criminal Justice",
    "surveillance": "Surveillance/Monitoring",
    "rehab_reintegration": "Rehabilitation/Reintegration",
    "women_children_notes": "Women & Children",
}

STATUS_EMOJI = {
    "Green": "🟢",
    "Yellow": "🟡",
    "Red": "🔴"
}

YES_SCORE = {"Yes": 1.0, "Partial": 0.5, "No": 0.0}

def normalize_date(series):
    return pd.to_datetime(series, errors="coerce")

def calc_country_completeness(row):
    scores = []
    for col in POLICY_COLUMNS:
        val = str(row[col]).strip()
        scores.append(YES_SCORE.get(val, 0.0))
    return round((sum(scores) / len(scores)) * 100, 1)

def status_badge(status):
    return f"{STATUS_EMOJI.get(status, '⚪')} {status}"

def count_gap_fields(dataframe):
    # Menghitung jumlah "No" sebagai gap data/policy coverage
    gap_count = 0
    for col in POLICY_COLUMNS:
        gap_count += (dataframe[col] == "No").sum()
    return int(gap_count)

df["last_update"] = normalize_date(df["last_update"])
df["completeness_pct"] = df.apply(calc_country_completeness, axis=1)

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filter")
countries = sorted(df["country"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Pilih negara",
    options=countries,
    default=countries
)

selected_status = st.sidebar.multiselect(
    "Status review",
    options=["Green", "Yellow", "Red"],
    default=["Green", "Yellow", "Red"]
)

selected_category = st.sidebar.selectbox(
    "Fokus kategori kebijakan",
    options=["Semua"] + list(CATEGORY_LABELS.keys()),
    format_func=lambda x: "Semua" if x == "Semua" else CATEGORY_LABELS[x]
)

filtered_df = df[
    df["country"].isin(selected_countries) &
    df["review_status"].isin(selected_status)
].copy()

# Jika pilih kategori tertentu, tampilkan yang bukan "No" saja (agar fokus)
if selected_category != "Semua":
    filtered_df = filtered_df[filtered_df[selected_category].isin(["Yes", "Partial"])]

# =========================
# HEADER
# =========================
st.title("🌍 FTF Policy Comparator & Monitoring (Mini App)")
st.caption("Contoh aplikasi semi-manual untuk monitoring & komparasi policy matrix FTF (dummy data).")

# =========================
# KPI CARDS
# =========================
total_country = len(filtered_df)
total_all = len(df)
green_count = int((filtered_df["review_status"] == "Green").sum())
yellow_count = int((filtered_df["review_status"] == "Yellow").sum())
red_count = int((filtered_df["review_status"] == "Red").sum())
avg_completeness = round(filtered_df["completeness_pct"].mean(), 1) if total_country > 0 else 0.0
gap_fields = count_gap_fields(filtered_df) if total_country > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Negara Terfilter", f"{total_country}/{total_all}")
col2.metric("Status Hijau", green_count)
col3.metric("Status Kuning", yellow_count)
col4.metric("Status Merah", red_count)
col5.metric("Rata-rata Kelengkapan", f"{avg_completeness}%")

st.divider()

# =========================
# CHARTS (Native Streamlit, no plotly)
# =========================
left, right = st.columns([1, 1])

with left:
    st.subheader("Progress Kelengkapan per Negara")
    if total_country > 0:
        chart_df = filtered_df[["country", "completeness_pct"]].sort_values("completeness_pct", ascending=False)
        st.bar_chart(chart_df.set_index("country"))
    else:
        st.info("Tidak ada data yang sesuai filter.")

with right:
    st.subheader("Distribusi Status Review")
    if total_country > 0:
        status_counts = (
            filtered_df["review_status"]
            .value_counts()
            .reindex(["Green", "Yellow", "Red"], fill_value=0)
            .rename_axis("status")
            .reset_index(name="jumlah")
        )
        st.bar_chart(status_counts.set_index("status"))
        st.caption(f"Gap field (nilai 'No') terdeteksi: **{gap_fields}**")
    else:
        st.info("Tidak ada data yang sesuai filter.")

st.divider()

# =========================
# TABLE VIEW
# =========================
st.subheader("Tabel Monitoring Policy Matrix (Ringkas)")

display_df = filtered_df.copy()
display_df["review_status"] = display_df["review_status"].apply(status_badge)
display_df["last_update"] = display_df["last_update"].dt.strftime("%Y-%m-%d")

table_cols = [
    "country", "last_update", "review_status",
    "prevention", "administrative", "criminal_justice",
    "surveillance", "rehab_reintegration", "women_children_notes",
    "completeness_pct", "notes"
]

st.dataframe(
    display_df[table_cols],
    use_container_width=True,
    hide_index=True
)

st.divider()

# =========================
# COUNTRY COMPARATOR
# =========================
st.subheader("🔎 Komparasi 2 Negara")

if len(countries) >= 2:
    c1, c2 = st.columns(2)
    with c1:
        country_a = st.selectbox("Negara A", countries, index=0)
    with c2:
        country_b = st.selectbox("Negara B", countries, index=min(1, len(countries)-1))

    row_a = df[df["country"] == country_a].iloc[0]
    row_b = df[df["country"] == country_b].iloc[0]

    compare_rows = []
    for col in POLICY_COLUMNS:
        a_val = row_a[col]
        b_val = row_b[col]

        if a_val == b_val:
            note = "Sama"
        elif (a_val == "Yes" and b_val in ["Partial", "No"]) or (a_val == "Partial" and b_val == "No"):
            note = f"{country_a} lebih kuat"
        elif (b_val == "Yes" and a_val in ["Partial", "No"]) or (b_val == "Partial" and a_val == "No"):
            note = f"{country_b} lebih kuat"
        else:
            note = "Berbeda"

        compare_rows.append({
            "Kategori": CATEGORY_LABELS[col],
            country_a: a_val,
            country_b: b_val,
            "Catatan": note
        })

    compare_df = pd.DataFrame(compare_rows)
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    # Ringkasan naratif otomatis
    score_a = row_a["completeness_pct"]
    score_b = row_b["completeness_pct"]
    if score_a > score_b:
        summary = f"Secara umum **{country_a}** terlihat lebih lengkap dalam data contoh ini ({score_a}%) dibanding **{country_b}** ({score_b}%)."
    elif score_b > score_a:
        summary = f"Secara umum **{country_b}** terlihat lebih lengkap dalam data contoh ini ({score_b}%) dibanding **{country_a}** ({score_a}%)."
    else:
        summary = f"Secara umum **{country_a}** dan **{country_b}** memiliki tingkat kelengkapan yang setara ({score_a}%)."

    st.success(summary)
else:
    st.info("Data negara belum cukup untuk komparasi.")

st.divider()

# =========================
# SOP / UPDATE NOTES SECTION
# =========================
st.subheader("📝 Draft SOP Update (Contoh Ringkas)")
st.markdown("""
1. **Frekuensi update:** mingguan / bulanan (sesuai kebutuhan unit).  
2. **Sumber rujukan:** policy matrix, country page, sumber resmi pemerintah/lembaga internasional.  
3. **Standar pengisian:** gunakan nilai **Yes / Partial / No** agar mudah dibandingkan.  
4. **QC sederhana:** cek tanggal update, konsistensi istilah, dan catatan sumber.  
5. **Output:** tabel monitoring + ringkasan perubahan penting untuk pimpinan/analis.
""")

with st.expander("Lihat raw data (dummy)"):
    st.write(df)

st.caption(
    f"Terakhir dibuka: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    "Aplikasi contoh untuk aktualisasi/latsar (semi-manual)."
)
