import os
import json
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy_garden.browser import KivyBrowser  # Trình duyệt nhúng

# Hằng số
SESSION_FILE = "session.dat"
# THAY ĐỔI URL NÀY THÀNH DOMAIN CỦA BẠN
BASE_API_URL = "https://yourdomain.com/traffic-exchange" 

class LoginScreen(Screen):
    pass

class SurfScreen(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class TrafficSurfApp(App):
    # Biến để lưu trữ thông báo lỗi/trạng thái trên màn hình đăng nhập
    login_status_text = StringProperty("Vui lòng nhập thông tin đăng nhập")

    def build(self):
        # Kivy sẽ tự động tải file trafficsurf.kv
        return WindowManager()

    def on_start(self):
        """
        Được gọi khi ứng dụng khởi động.
        Kiểm tra xem có session token đã lưu không.
        """
        Clock.schedule_once(self.check_session, 1)

    def check_session(self, *args):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    token = f.read().strip()
                if token:
                    print("Session token found. Starting surf...")
                    self.start_surfing(token)
                else:
                    self.root.current = 'login_screen'
            except Exception as e:
                print(f"Error reading session file: {e}")
                self.root.current = 'login_screen'
        else:
            print("No session file. Go to login screen.")
            self.root.current = 'login_screen'

    def do_login(self):
        """
        Thực hiện đăng nhập bằng cách gọi API.
        """
        username_input = self.root.get_screen('login_screen').ids.username
        password_input = self.root.get_screen('login_screen').ids.password

        username = username_input.text
        password = password_input.text

        if not username or not password:
            self.login_status_text = "Tên đăng nhập và mật khẩu không được để trống."
            return

        self.login_status_text = "Đang đăng nhập, vui lòng chờ..."

        try:
            api_url = f"{BASE_API_URL}/api/login.php"
            payload = {'username': username, 'password': password}
            
            # Sử dụng Clock để không làm treo giao diện
            def process_response(request, result):
                if request.resp_status == 200:
                    response_data = result
                    if response_data.get("success"):
                        api_token = response_data.get("api_token")
                        # Lưu token vào file
                        with open(SESSION_FILE, "w") as f:
                            f.write(api_token)
                        self.start_surfing(api_token)
                    else:
                        self.login_status_text = response_data.get("message", "Đăng nhập thất bại.")
                else:
                    self.login_status_text = f"Lỗi kết nối: {request.resp_status}"

            # Gửi request bất đồng bộ
            from kivy.network.urlrequest import UrlRequest
            UrlRequest(api_url, req_body=json.dumps(payload), 
                       req_headers={'Content-type': 'application/json'},
                       on_success=lambda req, res: process_response(req, res),
                       on_failure=lambda req, res: process_response(req, res),
                       on_error=lambda req, res: process_response(req, res),
                       timeout=10)

        except Exception as e:
            self.login_status_text = f"Lỗi nghiêm trọng: {e}"

    def start_surfing(self, token):
        """
        Chuyển sang màn hình lướt web và tải URL.
        """
        surf_url = f"{BASE_API_URL}/surf.php?api_token={token}"
        surf_screen = self.root.get_screen('surf_screen')
        browser_widget = surf_screen.ids.browser
        
        # Tải URL vào trình duyệt nhúng
        browser_widget.load_url(surf_url)

        self.root.current = 'surf_screen'

    def do_logout(self):
        """
        Đăng xuất và quay về màn hình đăng nhập.
        """
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        
        # Clear a webview (nếu cần)
        surf_screen = self.root.get_screen('surf_screen')
        browser_widget = surf_screen.ids.browser
        browser_widget.load_url("about:blank") # Load trang trống

        self.root.current = 'login_screen'
        self.login_status_text = "Bạn đã đăng xuất thành công."


if __name__ == '__main__':
    TrafficSurfApp().run()
