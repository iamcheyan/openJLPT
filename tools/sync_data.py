#!/usr/bin/env python3
"""
工具：数据同步
作用：通过 rsync 在本地和远程服务器之间同步题库数据（data/ 目录）。
用法：python3 tools/sync_data.py
"""
import os
import subprocess
import sys

# --- 配置信息 ---
SERVER_IP = "192.168.3.62"
REMOTE_PATH = "~/Development/openjlpt/data/"  # 服务器上的词库路径
LOCAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")  # 本地词库路径

# 从命令行或环境变量获取凭据
def get_credentials():
    # 1. 尝试从命令行参数获取 (例如: python3 sync_data.py user:pass)
    if len(sys.argv) > 1:
        auth = sys.argv[1]
    # 2. 尝试从环境变量获取
    else:
        auth = os.environ.get("OPENJLPT_AUTH")
    
    if not auth or ":" not in auth:
        print("错误: 请提供凭据！")
        print("用法 1 (参数): python3 sync_data.py user:password")
        print("用法 2 (环境变量): export OPENJLPT_AUTH=user:password && python3 sync_data.py")
        sys.exit(1)
        
    user, pw = auth.split(":", 1)
    return user, pw

def check_dependencies():
    """检查是否安装了必要的工具"""
    try:
        subprocess.run(["rsync", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("错误: 本地未安装 'rsync'。请先安装: sudo apt install rsync")
        return False
    return True

def sync():
    if not check_dependencies():
        return

    user, pw = get_credentials()

    # 确保本地目录存在
    if not os.path.exists(LOCAL_PATH):
        os.makedirs(LOCAL_PATH)

    print(f"--- 正在从 {SERVER_IP} 同步最新词库 ---")
    
    # 构造 rsync 命令
    rsync_cmd = [
        "rsync", "-avz", "--delete",
        f"{user}@{SERVER_IP}:{REMOTE_PATH}",
        LOCAL_PATH
    ]

    # 尝试使用 sshpass 实现免密
    try:
        # 检查是否安装了 sshpass
        subprocess.run(["sshpass", "-V"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        final_cmd = ["sshpass", "-p", pw] + rsync_cmd
        print(f"使用用户 '{user}' 进行同步...")
    except FileNotFoundError:
        print("提示: 未安装 'sshpass'，同步时可能需要手动输入密码。")
        final_cmd = rsync_cmd

    try:
        result = subprocess.run(final_cmd)
        if result.returncode == 0:
            print("\n[成功] 词库已同步至最新状态！")
        else:
            print(f"\n[错误] 同步失败，退出码: {result.returncode}")
    except Exception as e:
        print(f"\n[异常] 运行出错: {e}")

if __name__ == "__main__":
    sync()
