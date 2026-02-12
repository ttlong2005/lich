import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
from lunarcalendar import Lunar, Converter

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅")

# --- HÀM CHUYỂN ÂM SANG DƯƠNG ---
def get_solar_from_lunar(lunar_day, lunar_month):
    now = datetime.now()
    # Thử tính cho năm hiện tại
    lunar_date = Lunar(now.year, lunar_month, lunar_day)
    solar_date = Converter.LunarToSolar(lunar_date)
    dt_solar = datetime(solar_date.year, solar_date.month, solar_date.day)
    
    # Nếu ngày đó đã qua trong năm nay, tính cho năm sau
    if (dt_solar.date() - now.date()).days < 0:
        lunar_date = Lunar(now.year + 1, lunar_month, lunar_day)
        solar_date = Converter.LunarToSolar(lunar_date)
        dt_solar = datetime(solar_date.year, solar_date.month, solar_date.day)
    return dt_solar

# --- HÀM GỬI TELEGRAM ---
def send_telegram(message):
    try:
        token = st.secrets["telegram_token"]
        chat_id = st.secrets["telegram_chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload)
    except:
        pass

def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối: {str(e)}")
        return None

if "password_correct" not in st.session_state:
    st.subheader("🔒 Đăng nhập hệ thống")
    pw = st.text_input("Mật khẩu:", type="password")
    if st.button("Vào hệ thống"):
        if pw == st.secrets["password"]:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Sai mật khẩu!")
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
                
                if str(row['Loại']).strip() == 'Âm lịch':
                    event_date = get_solar_from_lunar(day, month)
                else:
                    event_date = datetime(now.year, month, day)
                    if (event_date.date() - now.date()).days < 0:
                        event_date = datetime(now.year + 1, month, day)
                
                diff = (event_date.date() - now.date()).days
                days_left_list.append(diff)
                
                # Gửi thông báo chi tiết khi còn đúng 3 ngày
                if diff == 3:
                    loai_lich = "🌙 Âm lịch" if str(row['Loại']).strip() == 'Âm lịch' else "☀️ Dương lịch"
                    msg = (f"🔔 *NHẮC NHỞ SỰ KIỆN SẮP ĐẾN*\n"
                           f"📌 *Sự kiện:* {row['Tên']}\n"
                           f"📅 *Ngày ghi:* {row['Ngày']} ({loai_lich})\n"
                           f"⏳ *Còn lại:* 3 ngày nữa\n"
                           f"📅 *Ngày dương tương ứng:* {event_date.strftime('%d/%m/%Y')}")
                    send_telegram(msg)
            except:
                days_left_list.append(None)

        df['Số ngày sắp đến'] = days_left_list
        st.subheader("📋 Danh sách sự kiện")
        # Hiển thị bảng đã sắp xếp theo ngày gần nhất
        st.dataframe(df.sort_values(by='Số ngày sắp đến'), use_container_width=True)

        with st.expander("➕ Thêm sự kiện mới"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Tên sự kiện:")
                date_input = st.text_input("Ngày (VD: 15/01):")
            with col2:
                etype = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu sự kiện"):
                if name and date_input:
                    sheet.append_row([name, date_input, etype])
                    st.success("Đã lưu!")
                    st.rerun()
