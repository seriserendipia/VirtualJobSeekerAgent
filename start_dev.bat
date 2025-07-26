@echo off
echo 正在构建 manifest.json...
python build_manifest.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 构建完成！现在可以加载 Chrome 扩展了
    echo.
    echo 📁 扩展目录: %~dp0frontend
    echo.
    echo 🔧 如需修改配置，请编辑 .env 文件
) else (
    echo.
    echo ❌ 构建失败，请检查配置
)

pause
