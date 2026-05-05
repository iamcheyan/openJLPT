#!/bin/bash
set -e

REMOTE="tetsuya@192.168.3.62"
REMOTE_APK="/home/tetsuya/Development/openjlpt/build_output/jlpt-drill-debug.apk"
LOCAL_APK="$HOME/Downloads/jlpt-drill-debug.apk"

if [ -n "$1" ] && [ -f "$1" ]; then
	APK="$1"
else
	echo ">>> 正在从远程服务器下载最新 APK..."
	scp "$REMOTE:$REMOTE_APK" "$LOCAL_APK"
	APK="$LOCAL_APK"
fi

echo "APK: $APK"

# 从 APK 二进制 manifest 中提取包名
PKG=$(python3 -c "
import zipfile, sys
with zipfile.ZipFile(sys.argv[1]) as z:
    data = z.read('AndroidManifest.xml')
    i = 0
    while i < len(data) - 1:
        try:
            s = data[i:i+200].decode('utf-16-le', errors='strict').split('\x00')[0]
            if len(s) > 3 and s.count('.') >= 2 and s.replace('.','').replace('_','').isalnum() and s.startswith('com.'):
                print(s); break
        except: pass
        i += 1
" "$APK")

if [ -z "$PKG" ]; then
	echo "无法读取包名"
	exit 1
fi

echo "包名: $PKG"

# 关闭 Play Protect 验证
adb shell settings put global verifier_verify_adb_installs 0
adb shell settings put global package_verifier_enable 0

# 已安装则先卸载
if adb shell pm list packages | grep -q "package:$PKG"; then
	echo "已存在旧版本，卸载中..."
	adb uninstall "$PKG"
fi

echo "安装中..."
adb install "$APK"

echo "启动中..."
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1
