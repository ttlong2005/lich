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
        # Lấy thông tin từ Secrets
        token = st.secrets["telegram_token"]
        chat_id = st.secrets["telegram_chat_id"]
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

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
        st.error(f"Lỗi kết nối Robot Google: {str(e)}")
        return None

# --- GIAO DIỆN ĐĂNG NHẬP ---
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
        # NÚT TEST NHANH
        if st.button("🚀 Bấm để Test gửi Telegram ngay bây giờ"):
            res = send_telegram("🔔 Tin nhắn Test: Robot đang hoạt động tốt!")
            if res.get("ok"):
                st.success("✅ Đã gửi! Anh kiểm tra Telegram nhé.")
            else:
                st.error(f"❌ Lỗi Telegram: {res.get('description')}")

        st.write("---")
        
        # ĐỌC DỮ LIỆU
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # --- LOGIC THÔNG BÁO TỰ ĐỘNG (KHOẢNG CÁCH 3 NGÀY) ---
        now = datetime.now()
        st.subheader("📢 Nhật ký thông báo hôm nay:")
        notification_sent = False

        for index, row in df.iterrows():
            try:
                # Xử lý ngày tháng (chấp nhận cả 6/01 và 06/01)
                date_parts = str(row['Ngày']).split('/')
                d = int(date_parts[0])
                m = int(date_parts[1])
                
                event_date = datetime(now.year, m, d)
                diff = (event_date - now).days + 1
                
                # CHỈNH SỬA TẠI ĐÂY: Nếu cách đúng 3 ngày (hoặc anh muốn test thì đổi thành 1)
                if diff == 3:
                    msg = f"🔔 NHẮC NHỞ: Sự kiện '{row['Tên']}' sẽ diễn ra sau 3 ngày nữa ({row['Ngày']})!"
                    res = send_telegram(msg)
                    if res.get("ok"):
                        st.info(f"✅ Đã gửi nhắc nhở cho: {row['Tên']}")
                    notification_sent = True
            except:
                continue
        
        if not notification_sent:
            st.write("Chưa có sự kiện nào cần báo (cách đúng 3 ngày).")

        st.write("---")
        st.subheader("📋 Danh sách sự kiện")
        st.dataframe(df, use_container_width=True)

        with st.expander("➕ Thêm sự kiện mới"):
            name = st.text_input("Tên sự kiện:")
            date_input = st.text_input("Ngày (VD: 15/01):")
            etype = st.selectbox("Loại:", ["Dương lịch", "Âm lịch"])
            if st.button("Lưu"):
                if name and date_input:
                    sheet.append_row([name, date_input, etype])
                    st.success("Đã lưu!")
                    st.rerun()
