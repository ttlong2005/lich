import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests

st.set_page_config(page_title="Quản Lý Sự Kiện Gia Đình", page_icon="📅")

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

# --- HÀM KẾT NỐI GOOGLE SHEETS ---
def get_sheet():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối: {str(e)}")
        return None

# --- GIAO DIỆN CHÍNH ---
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

        # --- XỬ LÝ DỮ LIỆU & TÍNH SỐ NGÀY SẮP ĐẾN ---
        days_left_list = []
        for index, row in df.iterrows():
            try:
                day, month = map(int, str(row['Ngày']).split('/'))
                event_date = datetime(now.year, month, day)
                
                # Nếu ngày sự kiện đã qua trong năm nay, tính cho năm sau
                if (event_date - now).days < -1:
                    event_date = datetime(now.year + 1, month, day)
                
                diff = (event_date - now).days + 1
                days_left_list.append(diff)
                
                # GỬI THÔNG BÁO CỤ THỂ KHI CÁCH ĐÚNG 3 NGÀY
                if diff == 3:
                    msg = (f"🔔 *NHẮC NHỞ SỰ KIỆN SẮP ĐẾN*\n"
                           f"📌 *Sự kiện:* {row['Tên']}\n"
                           f"📅 *Ngày diễn ra:* {row['Ngày']}\n"
                           f"⏳ *Còn lại:* 3 ngày nữa")
                    send_telegram(msg)
            except:
                days_left_list.append(None)

        df['Số ngày sắp đến'] = days_left_list

        # --- HIỂN THỊ ---
        st.subheader("📢 Nhật ký thông báo")
        upcoming = df[df['Số ngày sắp đến'] == 3]
        if not upcoming.empty:
            for _, r in upcoming.iterrows():
                st.info(f"🚀 Đã gửi Telegram báo sắp đến ngày: **{r['Tên']}** ({r['Ngày']})")
        else:
            st.write("Hôm nay chưa có sự kiện nào cần báo (chỉ báo khi cách đúng 3 ngày).")

        st.write("---")
        st.subheader("📋 Danh sách sự kiện")
        
        # Làm đẹp bảng hiển thị
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
                    st.success("Đã lưu thành công!")
                    st.rerun()
