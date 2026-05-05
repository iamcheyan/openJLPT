import http.server
import socketserver
import os
import sys
import json
import random
import urllib.request
import ssl

# 允许未经验证的 SSL（针对某些 CDN 环境）
ssl._create_default_https_context = ssl._create_unverified_context

PORT = 8080
LIBS_DIR = "assets/libs"
DICT_DIR = os.path.join(LIBS_DIR, "dict")

KUROMOJI_JS_URL = "https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/build/kuromoji.js"
DICT_BASE_URL = "https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/dict/"
DICT_FILES = [
    "base.dat.gz", "check.dat.gz", "tid.dat.gz", "tid_map.dat.gz", "tid_pos.dat.gz",
    "unk.dat.gz", "unk_char.dat.gz", "unk_compat.dat.gz", "unk_invoke.dat.gz", "unk_map.dat.gz", "unk_pos.dat.gz"
]

def ensure_assets():
    """检查并下载离线所需的库文件"""
    if not os.path.exists(DICT_DIR):
        os.makedirs(DICT_DIR)
        print(f"[*] 创建目录: {DICT_DIR}")

    # 下载 kuromoji.js
    js_path = os.path.join(LIBS_DIR, "kuromoji.js")
    if not os.path.exists(js_path):
        print(f"[*] 正在下载核心库: {KUROMOJI_JS_URL} ...")
        try:
            urllib.request.urlretrieve(KUROMOJI_JS_URL, js_path)
            print(" [+] 下载完成.")
        except Exception as e:
            print(f" [!] 下载失败: {e}")

    # 下载词典文件
    for file in DICT_FILES:
        file_path = os.path.join(DICT_DIR, file)
        if not os.path.exists(file_path):
            url = DICT_BASE_URL + file
            print(f"[*] 正在下载词典文件: {file} ...")
            try:
                urllib.request.urlretrieve(url, file_path)
                print(f" [+] {file} 下载完成.")
            except Exception as e:
                print(f" [!] {file} 下载失败: {e}")

class ExamHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 兼容旧路径，如果访问 /template/ 则尝试重定向或直接提供服务
        if self.path.startswith('/template/'):
            new_path = self.path.replace('/template/', '/')
            self.path = new_path
            
        # 如果访问根目录，返回 index.html
        if self.path == '/':
            self.path = '/index.html'
            
        return super().do_GET()

if __name__ == "__main__":
    # 启动前确保资源就绪
    print("-" * 40)
    print("OpenJLPT 离线资源检查器")
    ensure_assets()
    print("-" * 40)

    # 启动服务器
    Handler = ExamHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)
