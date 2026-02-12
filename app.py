import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
from lunar_python import Lunar, Solar

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅")

# --- HÀM CHUYỂN ÂM SANG DƯƠNG CHUẨN XÁC ---
def get_solar_from_lunar(lunar_day, lunar_month):
    now = datetime.now()
    # Kiểm tra 3 năm để tìm ngày âm gần nhất trong tương lai
    years_to_check = [now.year - 1, now.year, now.year + 1]
    potential_dates = []

    for y in years_to_check:
        try:
            lunar = Lunar.fromYmd(y, lunar_month, lunar_day)
            solar = lunar.getSolar()
            dt_solar = datetime(solar.getYear(), solar.getMonth(), solar.getDay())
            # Lấy ngày chưa qua hoặc chỉ mới qua hôm nay (>= -1)
            if (dt_solar.date() - now.date()).days >= -1:
                potential_dates.append(dt_solar)
        except:
            continue
    
    if potential_dates:
        return min(potential_dates)
    return None

def send_telegram(message):
    try:
        token = st.secrets["telegram_token"]
        chat_id = st.secrets["telegram_chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    except: pass

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
    
    # --- HIỂN THỊ NGÀY HÔM NAY (MỚI) ---
    now = datetime.now()
    solar_now = Solar.fromDate(now)
    lunar_now = Lunar.fromDate(now)
    
    st.info(f"""
    📅 **Hôm nay:** {now.strftime('%d/%m/%Y')} (Dương lịch)  
    🌙 **Âm lịch:** Ngày {lunar_now.getDay()}/{lunar_now.getMonth()} năm {lunar_now.getYearInGanZhi()} ({lunar_now.getYearZhi()})
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
                    diff = (event_date.date() - now.date()).days
                    days_left_list.append(diff)
                    
                    if diff == 3:
                        send_telegram(f"🔔 *NHẮC NHỞ:* {row['Tên']} ({row['Ngày']}) còn 3 ngày nữa!")
                else:
                    days_left_list.append(None)
            except:
                days_left_list.append(None)

        df['Số ngày sắp đến'] = days_left_list
        st.subheader("📋 Danh sách sự kiện")
        df_display = df.sort_values(by='Số ngày sắp đến', ascending=True)
        st.dataframe(df_display, use_container_width=True)

        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên:")
            d_input = st.text_input("Ngày (VD: 27/12):")
            l_input = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and d_input:
                    sheet.append_row([name, d_input, l_input])
                    st.success("Đã lưu!")
                    st.rerun()
