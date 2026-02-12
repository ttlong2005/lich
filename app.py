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
    # 1. Thử tính ngày âm đó ở năm ngoái (cho các ngày cuối năm âm rơi vào đầu năm dương)
    # 2. Thử tính cho năm nay
    # 3. Thử tính cho năm sau
    years_to_check = [now.year - 1, now.year, now.year + 1]
    potential_dates = []

    for y in years_to_check:
        try:
            lunar = Lunar.fromYmd(y, lunar_month, lunar_day)
            solar = lunar.getSolar()
            dt_solar = datetime(solar.getYear(), solar.getMonth(), solar.getDay())
            # Chỉ lấy các ngày chưa qua hoặc chỉ mới qua tối đa 1 ngày (để báo đúng ngày)
            if (dt_solar.date() - now.date()).days >= -1:
                potential_dates.append(dt_solar)
        except:
            continue
    
    # Chọn ngày gần nhất trong tương lai
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
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        now = datetime.now()
        days_left_list = []

        for index, row in df.iterrows():
            try:
                day, month = map(int, str(row['Ngày']).split('/'))
                
                if "Âm lịch" in str(row['Loại']):
                    event_date = get_solar_from_lunar(day, month)
                else:
                    # Dương lịch
                    event_date = datetime(now.year, month, day)
                    if (event_date.date() - now.date()).days < -1:
                        event_date = datetime(now.year + 1, month, day)
                
                if event_date:
                    diff = (event_date.date() - now.date()).days
                    days_left_list.append(diff)
                    
                    # Thông báo nếu đúng 3 ngày (hoặc hôm nay nếu anh muốn)
                    if diff == 3:
                        send_telegram(f"🔔 *NHẮC NHỞ:* {row['Tên']} ({row['Ngày']}) còn 3 ngày!")
                else:
                    days_left_list.append(None)
            except:
                days_left_list.append(None)

        df['Số ngày sắp đến'] = days_left_list
        # Hiển thị bảng và sắp xếp
        df_display = df.sort_values(by='Số ngày sắp đến', ascending=True)
        st.dataframe(df_display, width='stretch')

        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên:")
            d_input = st.text_input("Ngày (VD: 27/12):")
            l_input = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and d_input:
                    sheet.append_row([name, d_input, l_input])
                    st.success("Đã lưu!")
                    st.rerun()
