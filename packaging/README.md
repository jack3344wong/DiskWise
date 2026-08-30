# 打包说明

当前项目未自动安装打包依赖。准备发布时：

1. 使用项目环境安装并运行 PyInstaller，读取 `packaging/DiskWise.spec`。
2. 确认生成目录为 `dist/DiskWise/`。
3. 使用 Inno Setup 编译 `packaging/DiskWise.iss`。

窗口、任务栏、桌面/开始菜单快捷方式和安装包均引用 `assets/diskwise.ico`。
