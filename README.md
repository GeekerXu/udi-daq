# UDI 数据下载工具

从国家药监局 NMPA UDI 数据库自动下载医疗器械唯一标识（UDI）数据。

## 功能特性

| 特性 | 说明 |
|------|------|
| **四种数据类型** | 日度增量、周度汇总、月度汇总、全量数据 |
| **交互式界面** | 菜单驱动操作，无需记忆命令行参数，默认日度数据 |
| **并行加速** | 多进程并行解析 XML，显著提升处理速度 |
| **进度显示** | tqdm 进度条实时显示下载、解压、处理进度 |
| **流式处理** | 全量数据自动使用内存优化的流式处理模式 |
| **智能格式** | Excel 超过 100 万行自动切换为 CSV |
| **数据库支持** | Oracle、MySQL、Hive 三种数据库 |
| **可执行文件** | 提供 Windows 可执行文件，无需安装 Python |

## 项目结构

```
udid_daq/
├── core.py                    # 核心下载器模块
├── xml_parser.py              # XML 解析模块
├── db_helper.py               # 数据库辅助模块
├── udid_daq_interactive.py    # 交互式界面（推荐）
├── udid_daq_daily.py          # 日度数据命令行工具
├── udid_daq_weekly.py         # 周度数据命令行工具
├── udid_daq_monthly.py        # 月度数据命令行工具
├── udid_daq_full.py           # 全量数据命令行工具
├── db_config.ini.example      # 数据库配置示例
├── download/                  # 数据输出目录
└── dist/                      # 可执行文件目录
```

## 快速开始

### 方式一：交互式界面（推荐）

```bash
# 安装依赖
pip install feedparser requests pandas openpyxl tqdm

# 运行交互式界面
python udid_daq_interactive.py
```

交互式菜单：

```
============================================================
        UDI 数据下载工具 - 交互式界面 v3.2.0
============================================================

当前设置:
  - 数据类型: 日度
  - 输出格式: CSV

请选择操作:

  [1] 切换数据类型
  [2] 选择输出格式
  [3] 查看可用版本
  [4] 下载数据
  [0] 退出

请输入选项 [0-4]:
```

**推荐操作流程**：
1. 切换数据类型 → 选择需要的数据类型（日度/周度/月度/全量）
2. 选择输出格式 → CSV 或 Excel
3. 查看可用版本 → 确认有哪些数据可下载
4. 下载数据 → 选择具体版本下载

### 方式二：可执行文件（无需安装 Python）

从 [Releases](https://github.com/GeekerXu/udi-daq/releases) 页面下载对应平台的可执行文件。

#### 可执行文件说明

| 文件名 | 功能 | 双击运行行为 |
|--------|------|-------------|
| `udid_daq_interactive-*.exe/bin` | 交互式界面 | 弹出菜单，手动选择操作 |
| `udid_daq_daily-*.exe/bin` | 日度数据下载 | 自动下载最新日度数据，输出 CSV |
| `udid_daq_weekly-*.exe/bin` | 周度数据下载 | 自动下载最新周度数据，输出 CSV |
| `udid_daq_monthly-*.exe/bin` | 月度数据下载 | 自动下载最新月度数据，输出 CSV |
| `udid_daq_full-*.exe/bin` | 全量数据下载 | 自动下载最新全量数据，输出 CSV |

#### 使用方式

**交互式版本（推荐）**：双击运行，通过菜单选择数据类型、输出格式、下载版本。

**命令行版本**：
- **双击运行**：自动下载最新数据，输出 CSV 格式到 `download/` 目录
- **传参运行**：支持更多功能，需要在命令行中执行

```bash
# Windows - 在 CMD 或 PowerShell 中运行
udid_daq_daily-windows-x64.exe -l              # 列出可用日期
udid_daq_daily-windows-x64.exe -d 20260326     # 下载指定日期
udid_daq_daily-windows-x64.exe -a              # 下载所有可用日期
udid_daq_daily-windows-x64.exe --excel         # 下载最新，输出 Excel

udid_daq_weekly-windows-x64.exe -l             # 列出可用周期
udid_daq_weekly-windows-x64.exe -d 20260322    # 下载指定周期
udid_daq_weekly-windows-x64.exe -a             # 下载所有可用周期
udid_daq_weekly-windows-x64.exe --excel        # 下载最新，输出 Excel

udid_daq_monthly-windows-x64.exe -l            # 列出可用月份
udid_daq_monthly-windows-x64.exe -m 202603     # 下载指定月份
udid_daq_monthly-windows-x64.exe -a            # 下载所有可用月份
udid_daq_monthly-windows-x64.exe --excel       # 下载最新，输出 Excel

udid_daq_full-windows-x64.exe -l               # 列出可用版本（全量仅支持 CSV）

# Linux - 在终端中运行
chmod +x udid_daq_daily-linux-x64.bin          # 首次运行需添加执行权限
./udid_daq_daily-linux-x64.bin -l              # 列出可用日期
./udid_daq_daily-linux-x64.bin -d 20260326     # 下载指定日期
```

#### 快速使用提示

| 需求 | 操作方式 |
|------|----------|
| 下载最新数据 | 双击对应的可执行文件 |
| 选择数据类型/格式 | 使用交互式版本 `udid_daq_interactive` |
| 查看可用版本 | 命令行执行 `xxx.exe -l` |
| 下载指定日期 | 命令行执行 `xxx.exe -d YYYYMMDD` |
| 输出 Excel | 命令行执行 `xxx.exe --excel` |
| 下载全部数据 | 命令行执行 `xxx.exe -a` |

### 方式三：Python 命令行脚本

已安装 Python 环境的用户可直接运行源码：

```bash
# 安装依赖
pip install feedparser requests pandas openpyxl tqdm

# 日度数据
python udid_daq_daily.py              # 下载最新
python udid_daq_daily.py -l           # 列出可用日期
python udid_daq_daily.py -d 20260326  # 下载指定日期
python udid_daq_daily.py -a           # 下载全部
python udid_daq_daily.py --excel      # 输出 Excel

# 周度数据
python udid_daq_weekly.py              # 下载最新
python udid_daq_weekly.py -l           # 列出可用周期
python udid_daq_weekly.py -d 20260322  # 下载指定周期
python udid_daq_weekly.py -a           # 下载全部
python udid_daq_weekly.py --excel      # 输出 Excel

# 月度数据
python udid_daq_monthly.py             # 下载最新
python udid_daq_monthly.py -l          # 列出可用月份
python udid_daq_monthly.py -m 202603   # 下载指定月份
python udid_daq_monthly.py -a          # 下载全部
python udid_daq_monthly.py --excel     # 输出 Excel

# 全量数据（仅支持 CSV）
python udid_daq_full.py               # 下载最新全量
python udid_daq_full.py -l            # 列出可用版本
```

## 数据类型说明

| 类型 | 说明 | 更新频率 | 文件名示例 |
|------|------|----------|-----------|
| 日度 | 每个工作日的增量更新包 | 每日 | `udid_daily_20260326_20260327_120000.csv` |
| 周度 | 每周汇总（含 7 个日度 ZIP，自动解压合并） | 每周 | `udid_weekly_20260316~20260322_20260327_120000.csv` |
| 月度 | 每月汇总（自动合并当月所有日度数据） | 每月 | `udid_monthly_202602_20260327_120000.csv` |
| 全量 | 完整数据包（仅一个文件） | 不定期 | `udid_full_20260301_20260327_120000.csv` |

## 命令行参数

### 通用参数

| 参数 | 说明 |
|------|------|
| `-l, --list` | 列出可用的数据项 |
| `--excel` | 输出 Excel 格式（默认 CSV） |
| `--db TYPE` | 写入数据库（oracle/mysql/hive） |

### 日度/周度参数

| 参数 | 说明 |
|------|------|
| `-d, --date YYYYMMDD` | 下载指定日期/周期 |
| `-a, --all` | 下载所有可用数据 |

### 月度参数

| 参数 | 说明 |
|------|------|
| `-m, --month YYYYMM` | 下载指定月份 |
| `-a, --all` | 下载所有可用月份 |

## 数据库配置

### 配置方式一：配置文件（推荐）

1. 复制示例文件：
   ```bash
   cp db_config.ini.example db_config.ini
   ```

2. 编辑 `db_config.ini`：
   ```ini
   [oracle]
   host = 192.168.1.100
   port = 1521
   service = ORCL
   user = udi_user
   password = your_password

   [mysql]
   host = 192.168.1.100
   port = 3306
   database = udi_db
   user = udi_user
   password = your_password

   [hive]
   host = 192.168.1.100
   port = 10000
   database = udi_db
   user = udi_user
   password = your_password
   ```

3. 运行时指定数据库：
   ```bash
   python udid_daq_daily.py --db oracle
   python udid_daq_daily.py --db mysql
   python udid_daq_daily.py --db hive
   ```

### 配置方式二：环境变量

```bash
# Oracle
export UDI_ORACLE_HOST=192.168.1.100
export UDI_ORACLE_PORT=1521
export UDI_ORACLE_SERVICE=ORCL
export UDI_ORACLE_USER=udi_user
export UDI_ORACLE_PASSWORD=your_password

# MySQL
export UDI_MYSQL_HOST=192.168.1.100
export UDI_MYSQL_PORT=3306
export UDI_MYSQL_DATABASE=udi_db
export UDI_MYSQL_USER=udi_user
export UDI_MYSQL_PASSWORD=your_password

# Hive
export UDI_HIVE_HOST=192.168.1.100
export UDI_HIVE_PORT=10000
export UDI_HIVE_DATABASE=udi_db
export UDI_HIVE_USER=udi_user
export UDI_HIVE_PASSWORD=your_password
```

### 数据库驱动安装

```bash
pip install cx_Oracle              # Oracle
pip install pymysql                # MySQL
pip install pyhive sasl thrift     # Hive
```

### 数据表结构

详见 `db_helper.py` 中的 `CREATE_TABLE_SQL` 字典，包含：
- Oracle 建表语句
- MySQL 建表语句
- Hive 建表语句

## 输出说明

### 输出目录

所有文件输出到 `download/` 目录。

### 文件命名规则

```
udid_{type}_{identifier}_{timestamp}.{ext}
```

| 组成部分 | 说明 |
|----------|------|
| `type` | 数据类型（daily/weekly/monthly/full） |
| `identifier` | 日期标识 |
| `timestamp` | 下载时间（YYYYMMDD_HHMMSS） |
| `ext` | 文件扩展名（csv/xlsx） |

### 输出优先级

1. 启用数据库且写入成功 → 不保存本地文件
2. 启用数据库但写入失败 → 保存本地文件
3. 未启用数据库 → 直接保存本地文件

## 高级用法

### 自行编译可执行文件

如需自行编译，可使用 PyInstaller：

```bash
# 安装 PyInstaller
pip install pyinstaller

# 编译单个脚本
pyinstaller --onefile --name udid_daq_daily udid_daq_daily.py

# 编译交互式版本
pyinstaller --onefile --name udid_daq_interactive udid_daq_interactive.py
```

编译后的可执行文件位于 `dist/` 目录。

## 常见问题

### Q: 下载失败怎么办？

1. 检查网络连接
2. 确认 RSS 地址可访问：`https://udi.nmpa.gov.cn/rss/download.html`
3. 查看错误信息，部分日期数据可能不存在

### Q: 为什么全量数据不支持 Excel？

全量数据超过 Excel 的行数限制（1,048,576 行），强制输出 CSV。交互式界面中，若选择 Excel 且数据量超过限制，会自动切换为 CSV。

### Q: 如何处理 Windows 控制台中文乱码？

脚本已内置编码设置。如仍有问题，手动执行：

```bash
chcp 65001
python udid_daq_daily.py -l
```

### Q: 数据库连接失败怎么办？

1. 确认已安装对应数据库驱动
2. 检查配置文件或环境变量是否正确
3. 确认数据库服务可访问（网络、防火墙）
4. 运行时会自动测试连接，失败会显示详细错误信息

## 版本历史

### v3.2.0

- 交互式界面菜单顺序优化：切换类型 → 选择格式 → 查看版本 → 下载
- 默认数据类型改为日度（daily）
- 数据库配置支持配置文件（db_config.ini）
- 优化错误提示信息

### v3.1.0

- 增加并行处理：多进程解析 XML，显著提升处理速度
- 增加 tqdm 进度条：美化下载、解压、处理进度显示
- 增加流式处理：全量数据自动使用内存优化的流式模式
- 重写交互式界面：更友好的菜单操作
- 提供 Windows 可执行文件

### v3.0.0

- 重构代码架构，引入核心模块 `core.py`
- 统一代码风格和注释格式
- 优化执行效率，减少重复代码
- 新增交互式界面
- 改进错误处理和日志输出

### v2.3.0

- 删除 all.py（RSS 内容重复）
- 默认输出 CSV，新增 `--excel` 参数
- full 脚本禁止 Excel 输出
- 新增 `--db` 参数控制数据库类型

### v2.2.0

- 统一输出目录为 `download/`
- 统一文件名格式
- 修复 `-a` 参数合并问题

## 许可证

MIT License

## 作者

geekerxu