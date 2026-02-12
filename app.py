import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Kiểm tra kết nối", page_icon="🔍")

def get_sheet():
    try:
        # 1. Kiểm tra xem Secrets có biến service_account chưa
        if "service_account" not in st.secrets:
            st.error("❌ Lỗi: Không tìm thấy mục [service_account] trong Secrets!")
            return None
        
        # 2. Đọc cấu hình từ Secrets
        creds_info = dict(st.secrets["service_account"])
        
        # 3. Xử lý ký tự xuống dòng (bắt buộc cho Google)
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        # 4. Thử tạo Credentials
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        
        # 5. Thử kết nối gspread
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["sheet_id"]).get_worksheet(0)
        
    except KeyError as e:
        st.error(f"❌ Thiếu trường thông tin trong JSON: {str(e)}")
    except ValueError as e:
        st.error(f"❌ Định dạng Private Key bị sai: {str(e)}")
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Robot: {str(e)}")
    return None

# Giao diện kiểm tra
st.title("🔍 Kiểm tra cấu hình Robot")

sheet = get_sheet()

if sheet:
    st.success("✅ Tuyệt vời! Robot đã kết nối thành công với Google Sheets.")
    # Thử đọc một chút dữ liệu để chắc chắn
    try:
        data = sheet.get_all_records()
        st.write("Dữ liệu hiện có trên Sheet:", pd.DataFrame(data))
    except:
        st.warning("Kết nối OK nhưng chưa có dữ liệu hoặc tiêu đề trên Sheet.")
else:
    st.info("💡 Anh hãy kiểm tra lại mục Secrets theo hướng dẫn ở trên nhé.")
