# UDI 数据下载工具

从国家药监局 NMPA UDI 数据库自动下载 UDI 数据。

## 功能特性

- **四种数据类型**：日度、周度、月度、全量
- **交互式界面**：菜单驱动操作，无需命令行参数
- **并行加速**：多进程并行解析 XML，显著提升处理速度
- **进度显示**：tqdm 进度条实时显示下载、解压、处理进度
- **流式处理**：全量数据自动使用内存优化的流式处理
- **数据库支持**：Oracle、MySQL、Hive
- **可执行文件**：提供 Windows 可执行文件，无需安装 Python

## 快速开始

### 使用可执行文件（推荐）

```bash
# Windows - 直接运行
dist\udid_daq_windows.exe

# Linux
./dist/udid_daq_linux
```

### Python 环境

```bash
# 安装依赖
pip install feedparser requests pandas openpyxl tqdm

# 运行交互式界面
python udid_daq_interactive.py
```

### 基本用法

```bash
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

# 全量数据
python udid_daq_full.py               # 下载最新全量
python udid_daq_full.py -l            # 列出可用版本
# 注意：全量数据仅支持 CSV，禁止 Excel 输出

# 交互式界面
python udid_daq_interactive.py
```

## 数据类型说明

| 类型 | 说明 | 文件名示例 |
|------|------|-----------|
| 日度 | 每个工作日的增量更新包 | `udid_daily_20260326_20260327_120000.csv` |
| 周度 | 每周汇总（含 7 个日度 ZIP，自动解压合并） | `udid_weekly_20260316~20260322_20260327_120000.csv` |
| 月度 | 每月汇总（自动合并当月所有日度数据） | `udid_monthly_202602_20260327_120000.csv` |
| 全量 | 完整数据包（仅一个文件） | `udid_full_20260301_20260327_120000.csv` |

## 命令行参数

### 通用参数

| 参数 | 说明 |
|------|------|
| `-l, --list` | 列出可用的数据项 |
| `--excel` | 输出 Excel 格式（默认 CSV） |
| `--db TYPE` | 写入数据库（oracle/mysql/hive） |

### 日度参数

| 参数 | 说明 |
|------|------|
| `-d, --date YYYYMMDD` | 下载指定日期 |
| `-a, --all` | 下载所有可用日期 |

### 周度参数

| 参数 | 说明 |
|------|------|
| `-d, --date YYYYMMDD` | 下载指定周期（使用结束日期） |
| `-a, --all` | 下载所有可用周期 |

### 月度参数

| 参数 | 说明 |
|------|------|
| `-m, --month YYYYMM` | 下载指定月份 |
| `-a, --all` | 下载所有可用月份 |

## 数据库配置

### 命令行方式（推荐）

```bash
python udid_daq_daily.py --db oracle
python udid_daq_daily.py --db mysql
python udid_daq_daily.py --db hive
```

### 环境变量方式

```bash
# 启用数据库
export UDI_DB_ENABLED=oracle    # Linux
set UDI_DB_ENABLED=oracle       # Windows

# Oracle 配置
export UDI_ORACLE_HOST=192.168.1.100
export UDI_ORACLE_PORT=1521
export UDI_ORACLE_SERVICE=ORCL
export UDI_ORACLE_USER=udi_user
export UDI_ORACLE_PASSWORD=your_password

# MySQL 配置
export UDI_MYSQL_HOST=192.168.1.100
export UDI_MYSQL_PORT=3306
export UDI_MYSQL_DATABASE=udi_db
export UDI_MYSQL_USER=udi_user
export UDI_MYSQL_PASSWORD=your_password

# Hive 配置
export UDI_HIVE_HOST=192.168.1.100
export UDI_HIVE_PORT=10000
export UDI_HIVE_DATABASE=udi_db
export UDI_HIVE_USER=udi_user
export UDI_HIVE_PASSWORD=your_password
```

### 数据库驱动安装

```bash
pip install cx_Oracle      # Oracle
pip install pymysql        # MySQL
pip install pyhive sasl thrift  # Hive
```

### 建表语句

详见 `db_helper.py` 中的 `CREATE_TABLE_SQL` 字典。

## 输出说明

### 输出目录

所有文件输出到 `download/` 目录。

### 文件命名规则

```
udid_{type}_{identifier}_{timestamp}.{ext}
```

- `type`: 数据类型（daily/weekly/monthly/full）
- `identifier`: 日期标识
- `timestamp`: 下载时间（YYYYMMDD_HHMMSS）
- `ext`: 文件扩展名（csv/xlsx）

### 输出优先级

1. 数据库写入成功 → 不保存本地文件
2. 数据库写入失败 → 保存本地文件
3. 未启用数据库 → 直接保存本地文件

## 交互式界面

运行交互式脚本：

```bash
python udid_daq_interactive.py
```

主菜单：

```
============================
  UDI 数据下载工具 v3.0.0
============================

1. 查询日度数据
2. 查询周度数据
3. 查询月度数据
4. 查询全量数据
---------------------------
5. 下载日度数据
6. 下载周度数据
7. 下载月度数据
8. 下载全量数据
---------------------------
9. 查看下载目录
0. 退出

请选择:
```

## 构建可执行文件

使用 PyInstaller 构建：

```bash
# 安装 PyInstaller
pip install pyinstaller

# Windows
python -m PyInstaller --onefile --name udid_daq_windows udid_daq_interactive.py

# Linux
python -m PyInstaller --onefile --name udid_daq_linux udid_daq_interactive.py
```

编译后的可执行文件位于 `dist/` 目录。

## 常见问题

### Q: 下载失败怎么办？

1. 检查网络连接
2. 确认 RSS 地址可访问：`https://udi.nmpa.gov.cn/rss/download.html`
3. 查看错误信息，部分日期数据可能不存在

### Q: 为什么全量数据不支持 Excel？

全量数据超过 Excel 的行数限制（1,048,576 行），强制输出 CSV。

### Q: 如何处理 Windows 控制台中文乱码？

脚本已内置编码设置。如仍有问题，手动执行：

```bash
chcp 65001
python udid_daq_daily.py -l
```

### Q: 数据库连接失败怎么办？

1. 确认已安装对应驱动
2. 检查环境变量配置是否正确
3. 确认数据库服务可访问

## 版本历史

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