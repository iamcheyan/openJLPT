#!/bin/bash
# OpenJLPT 一键编译 + 远程 ADB 部署脚本 (最终增强版)

set -e

# 1. 确保在项目根目录
cd "$(dirname "$0")"

# 解析参数
SYNC_PARAM=$1
DO_SYNC=false

if [[ $SYNC_PARAM == sync:* ]]; then
    DO_SYNC=true
    SYNC_INFO=${SYNC_PARAM#sync:}
    USER_PASS=${SYNC_INFO%@*}
    REMOTE_HOST=${SYNC_INFO#*@}
    REMOTE_USER=${USER_PASS%:*}
    REMOTE_PASS=${USER_PASS#*:}
    echo ">>> 检测到同步需求: 用户=$REMOTE_USER, 主机=$REMOTE_HOST"
fi

echo ">>> 开始准备 Web 资源..."
mkdir -p android/app/src/main/assets/assets
cp template/exam_base.html android/app/src/main/assets/index.html
cp -r assets/* android/app/src/main/assets/assets/
cp manifest.json android/app/src/main/assets/
rm -rf android/app/src/main/assets/assets/libs/dict/*.gz
echo ">>> Web 资源准备就绪。"

echo ">>> 正在启动 Gradle 编译..."
cd android
./gradlew assembleDebug
cd ..

# 生成产物路径
APK_SRC="android/app/build/outputs/apk/debug/app-debug.apk"
APK_NAME="openjlpt-debug.apk"
mkdir -p build_output
cp $APK_SRC "./build_output/$APK_NAME"

echo "--------------------------------------------------"
echo "✅ 编译成功！"

if [ "$DO_SYNC" = true ]; then
    echo ">>> 正在远程推送到 $REMOTE_HOST ..."
    REMOTE_DIR="/Users/$REMOTE_USER/Downloads"
    REMOTE_PATH="$REMOTE_DIR/app-debug.apk"

    if ! command -v sshpass &> /dev/null; then
        echo "⚠️ 错误: 未找到 sshpass 命令，请先执行: sudo apt install sshpass"
        exit 1
    fi

    # 1. 拷贝 APK
    sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no "$APK_SRC" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"

    # 2. 远程卸载、安装、提权并启动
    echo ">>> 正在远程部署到手机..."
    # 执行远程 ADB 命令 (强力路径搜寻版)
    echo ">>> 正在远程部署到手机..."
    sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "
        # 强行把所有可能的坑位都塞进 PATH
        export PATH=\$PATH:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/Users/$REMOTE_USER/Library/Android/sdk/platform-tools
        
        # 再次探测并定义变量
        ADB_CMD=\"adb\"
        if [ -x /opt/homebrew/bin/adb ]; then ADB_CMD=/opt/homebrew/bin/adb; fi
        if [ -x /usr/local/bin/adb ]; then ADB_CMD=/usr/local/bin/adb; fi
        
        echo \"[1/4] 使用 ADB 指令: \$ADB_CMD\"
        
        echo \"[1/4] 关闭安装校验...\"
        \$ADB_CMD shell settings put global verifier_verify_adb_installs 0
        \$ADB_CMD shell settings put global package_verifier_enable 0
        
        echo \"[2/4] 正在卸载旧版本...\"
        \$ADB_CMD uninstall com.openjlpt.app || true
        
        echo \"[3/4] 正在安装新版本...\"
        \$ADB_CMD install -r $REMOTE_PATH
        
        echo \"[4/4] 正在启动 App...\"
        \$ADB_CMD shell monkey -p com.openjlpt.app -c android.intent.category.LAUNCHER 1
    "
    
    echo "🚀 全自动化部署完成！"
else
    FULL_PATH="$(pwd)/build_output/$APK_NAME"
    echo "--------------------------------------------------"
    echo "💡 提示: 最新的 APK 已保存在:"
    echo "   $FULL_PATH"
    echo "--------------------------------------------------"
fi
