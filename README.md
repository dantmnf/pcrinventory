# PCR Inventory

公主连结 Re:Dive 全自动仓库识别工具，支持国服、日服、台服。

\* 国服、日服仅训练过对应字体，未实际测试。

## 安装

### 从源代码安装

需要 Python 3.8 或以上版本。

> ⚠ **不建议从 GitHub 下载 zip 源码包安装**：这样做会丢失版本信息，且不便于后续更新。

```bash
git clone https://github.com/dantmnf/pcrinventory
cd pcrinventory

#### 建议使用 venv 避免依赖包冲突
python3 -m venv venv
# 在 Windows cmd 中：
venv\Scripts\activate.bat
# 在 PowerShell 中：
& ./venv/[bS]*/Activate.ps1
# 在 bash/zsh 中：
source venv/bin/activate
#### venv end

pip install -r requirements.txt
```

### 二进制包（Windows）

TODO：从 Actions artifacts 或 Releases 中下载 PyInstaller 打包后的二进制包，二进制包随源代码同步更新。

### OCR 依赖

从**源代码**安装时，需要安装 tesseract OCR 并将其 **DLL**（`libtesseract-*.dll`、`tesseract*.dll` 或 `libtesseract.so.*` 等）加入到 DLL 搜索路径（`PATH`、`ld.so.conf`、`LD_LIBRARY_PATH` 或 `DYLD_LIBRARY_PATH` 等）中，请参阅 [OCR 安装说明](https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper/wiki/OCR-%E5%AE%89%E8%A3%85%E8%AF%B4%E6%98%8E)。

项目内自带识别模型，安装时不需要额外选择任何语言资料。

**二进制包**自带 tesseract 库，无需额外安装。

##  **环境与分辨率**

脚本可以自适应分辨率（宽高比不小于 16:9，即`宽度≥高度×16/9`，且高度不小于 720），作者测试过的分辨率有 <span style="opacity: 0.5">1280x720、1440x720、</span>1920x1080、2160x1080。

例外：宽高比过大时会产生黑边 padding，影响自适应分辨率定位。

## **ADB 连接**

请确认 `adb devices` 中列出了目标模拟器/设备：

    $ adb devices
    emulator-5554   device

如何连接 ADB 请参考各模拟器的文档、论坛等资源。

如果 `adb devices` 中列出了目标模拟器/设备，但脚本不能正常连接，或遇到其他问题，请尝试使用[最新的 ADB 工具](https://developer.android.google.cn/studio/releases/platform-tools)。

### 常见问题

#### ADB server 相关

* 部分模拟器（如 MuMu、BlueStacks）需要自行启动 ADB server。
* 部分模拟器（如 MuMu、BlueStacks Hyper-V）不使用标准模拟器 ADB 端口，ADB server 无法自动探测，需要另行 adb connect。
* 部分模拟器（如夜神）会频繁使用自带的旧版本 ADB 挤掉用户自行启动的新版 ADB。

可以参阅[配置说明](#额外设置)以配置自动解决以上问题。

#### 其他

* 部分非 VMM 模拟器（声称“不需要开启 VT”，如 MuMu 星云引擎）不提供 ADB 接口。

## **额外设置**

关于额外设置请移步到 [config/config-template.yaml](config/config-template.yaml) 中查看

## **日志说明**
图像识别日志为 `log/*.html`，识别模块初始化时会清空原有内容。

多开时日志文件名会出现实例 ID，如 `pcr.addons.inventory.1.html`。

**报告 issue 时，建议附上日志以便定位问题。**

## 使用说明

```
$ python3 pcrinventory.py
commands (prefix abbreviation accepted):
    connect [connector type] [connector args ...]
        连接到设备
        支持的设备类型：
        connect adb [serial or tcpip endpoint]
    inventory
        仓库识别。
        需要进入仓库画面并滚动到最顶端。需要宽高比不小于 16:9，高度不小于 720，且游戏显示没有黑边。
    exit
pcrhelper>
```

在 `pcrhelper> ` 提示符下：

* 输入 `connect adb [device]` 命令连接到特定模拟器或设备。
  * 使用 `adb devices` 中的设备名；
  * 如果设备名为 `IP地址:端口号` 形式，会在需要时自动调用 `adb connect`。
* 进入仓库画面后，输入 `inventory` 开始识别仓库。

识别完毕后，会以 `物品ID 数量` 格式输出识别的物品，可用于导入 [公主连结 Box](https://pcr.satroki.tech/) 工具。
```
pcrhelper> inventory
 Ξ new: [('106612', 1), ('106611', 1), ('106582', 1), ('106581', 1), ('106552', 1), ('106551', 1), ('106521', 1), ('106461', 1), ('106431', 1), ('106401', 1), ('106372', 1), ('106371', 1), ('106342', 1), ('106341', 1), ('106312', 1)]
...
 Ξ new: [('101131', 143), ('101101', 153), ('101071', 122), ('101011', 101)]
106612 1
106611 1
106582 1
106581 1
106552 1
...
101101 153
101071 122
101011 101
pcrhelper> 
```

## 已知问题

* 当前识别方式（截图与所有已知物品比较）在当前数据量（735 种已知物品）下速度较慢（15 个物品约 750ms）
* 物品图标干扰数量提取时，OCR 会识别错误：

    ![](https://user-images.githubusercontent.com/2252500/141682428-b85bcfdb-1588-457c-93b0-523cb9389d44.png)

## Credits

程序架构来自 https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper 。

物品图标来自 https://pcr.satroki.tech/ ，版权归原作者（Cygames）所有。
