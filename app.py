import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
from lunar_python import Lunar, Solar

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅")

# --- TỪ ĐIỂN TIẾNG VIỆT CHO CAN CHI ---
CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

def get_vietnamese_year(lunar):
    # Hàm này giúp chuyển các ký tự Hán thành chữ Tiếng Việt chuẩn
    gan_zhi = lunar.getYearInGanZhi() # Trả về VD: "乙巳"
    # Thư viện trả về Can Chi tiếng Việt thông qua các hàm riêng biệt
    return f"{lunar.getYearGan()}{lunar.getYearZhi()} ({lunar.getYear()})"

# --- HÀM CHUYỂN ÂM SANG DƯƠNG CHUẨN XÁC ---
def get_solar_from_lunar(lunar_day, lunar_month):
    now = datetime.now()
    years_to_check = [now.year - 1, now.year, now.year + 1]
    potential_dates = []
    for y in years_to_check:
        try:
            lunar = Lunar.fromYmd(y, lunar_month, lunar_day)
            solar = lunar.getSolar()
            dt_solar = datetime(solar.getYear(), solar.getMonth(), solar.getDay())
            if (dt_solar.date() - now.date()).days >= -1:
                potential_dates.append(dt_solar)
        except: continue
    if potential_dates: return min(potential_dates)
    return None

def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except: return None

# --- GIAO DIỆN ---
if "password_correct" not in st.session_state:
    st.subheader("🔒 Đăng nhập")
    pw = st.text_input("Mật khẩu:", type="password")
    if st.button("Vào hệ thống"):
        if pw == st.secrets["password"]:
            st.session_state.password_correct = True
            st.rerun()
else:
    st.title("📅 Quản Lý Sự Kiện Gia Đình")
    
    # --- HIỂN THỊ NGÀY HÔM NAY ---
    now = datetime.now()
    lunar_now = Lunar.fromDate(now)
    # Lấy Can Chi bằng Tiếng Việt
    nam_can_chi = f"{lunar_now.getYearGan()}{lunar_now.getYearZhi()}"
    tiet_khi = lunar_now.getJieQi() if lunar_now.getJieQi() else "Bình thường"

    st.info(f"""
    📅 **Dương lịch:** {now.strftime('%d/%m/%Y')}  
    🌙 **Âm lịch:** Ngày **{lunar_now.getDay()}/{lunar_now.getMonth()}** - Năm **{nam_can_chi}** ({lunar_now.getYear()})  
    🎋 **Tiết khí:** {tiet_khi}
    """)

    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        days_left_list = []
        for index, row in df.iterrows():
            try:
                day, month = map(int, str(row['Ngày']).split('/'))
                if "Âm lịch" in str(row['Loại']):
                    event_date = get_solar_from_lunar(day, month)
                else:
                    event_date = datetime(now.year, month, day)
                    if (event_date.date() - now.date()).days < -1:
                        event_date = datetime(now.year + 1, month, day)
                if event_date:
                    days_left_list.append((event_date.date() - now.date()).days)
                else: days_left_list.append(None)
            except: days_left_list.append(None)

        df['Số ngày sắp đến'] = days_left_list
        st.subheader("📋 Danh sách sự kiện")
        st.dataframe(df.sort_values(by='Số ngày sắp đến'), width='stretch')

        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên:")
            d_input = st.text_input("Ngày (VD: 27/12):")
            l_input = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and d_input:
                    sheet.append_row([name, d_input, l_input])
                    st.success("Đã lưu!")
                    st.rerun()
