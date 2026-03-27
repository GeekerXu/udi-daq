# UDID 数据下载工具使用说明

## 工具简介

从国家药监局UDI数据库自动下载UDI数据，支持全部5种下载模式：

| 脚本 | 说明 | 数据类型 |
|------|------|----------|
| `udid_daq_interactive.py` | **全功能交互式版本** | 支持全部5种类型查询和下载 |
| `udid_daq_daily.py` | 命令行日度下载器 | 每日增量更新数据 |
| `udid_daq_weekly.py` | 命令行周度下载器 | 每周增量更新数据 |
| `udid_daq_monthly.py` | 命令行月度下载器 | 每月增量更新数据（自动合并） |
| `udid_daq_all.py` | 命令行全量下载器 | 所有历史版本汇总 |
| `udid_daq_full.py` | 命令行全量包下载器 | 完整数据包下载 |

### 数据源说明

| 类型 | RSS地址 | 说明 |
|------|---------|------|
| 每日发布 | `files=daily` | 每个工作日的增量更新 |
| 每周发布 | `files=weekly` | 每周汇总更新 |
| 每月发布 | `files=monthly` | 每月汇总更新（含日度数据合并） |
| 所有版本 | `files=all` | 完整历史数据 |
| 全量发布 | `files=full` | 完整数据包 |

---

## Windows 可执行文件下载

无需安装Python，直接下载exe文件即可运行！

### 下载地址

前往 [Releases 页面](https://github.com/geekerxu/udid_daq/releases) 下载最新版本的exe文件：

| 文件名 | 说明 |
|--------|------|
| `udid_daq_interactive.exe` | **全功能交互式界面**（推荐） |
| `udid_daq_daily.exe` | 日度数据下载器 |
| `udid_daq_weekly.exe` | 周度数据下载器 |
| `udid_daq_monthly.exe` | 月度数据下载器 |
| `udid_daq_all.exe` | 所有版本下载器 |
| `udid_daq_full.exe` | 全量包下载器 |

### exe 文件使用

#### 交互式版本（推荐）
```
双击 udid_daq_interactive.exe 直接运行
```
支持查询和下载全部5种数据类型。

#### 命令行版本

```cmd
# 日度数据
udid_daq_daily.exe -l           # 列出可用日期
udid_daq_daily.exe              # 下载最新
udid_daq_daily.exe -d 20260325  # 下载指定日期
udid_daq_daily.exe -a           # 下载所有

# 周度数据
udid_daq_weekly.exe -l
udid_daq_weekly.exe
udid_daq_weekly.exe -d 20260325

# 月度数据
udid_daq_monthly.exe -l
udid_daq_monthly.exe
udid_daq_monthly.exe -m 202603

# 所有版本
udid_daq_all.exe -l
udid_daq_all.exe

# 全量包
udid_daq_full.exe -l
udid_daq_full.exe
```

### 注意事项

- exe 文件较大（约 40MB），因为包含了完整的 Python 运行时
- 部分杀毒软件可能会误报，建议将 exe 添加到白名单
- 数据保存在程序所在目录的对应文件夹中

---

## Linux 可执行文件下载

无需安装Python，直接下载可执行文件即可运行！

### 下载地址

前往 [Releases 页面](https://github.com/geekerxu/udid_daq/releases) 下载最新版本的Linux可执行文件：

| 文件名 | 说明 |
|--------|------|
| `udid_daq_interactive` | **全功能交互式界面**（推荐） |
| `udid_daq_daily` | 日度数据下载器 |
| `udid_daq_weekly` | 周度数据下载器 |
| `udid_daq_monthly` | 月度数据下载器 |
| `udid_daq_all` | 所有版本下载器 |
| `udid_daq_full` | 全量包下载器 |

### Linux 使用

```bash
# 添加执行权限
chmod +x udid_daq_interactive

# 直接运行（交互式版本）
./udid_daq_interactive

# 命令行版本示例
chmod +x udid_daq_daily
./udid_daq_daily -l  # 列出可用日期
```

### Linux 版本构建说明

Linux 可执行文件通过 GitHub Actions CI 自动构建。每次发布新版本标签时会自动构建并上传。

如需手动触发构建：
1. 进入项目的 Actions 页面
2. 选择 "Build Linux Executables" workflow
3. 点击 "Run workflow"

### 注意事项

- Linux 二进制文件兼容大多数主流发行版（Ubuntu, Debian, Fedora, Arch 等）
- 依赖 glibc 2.17+（大多数现代Linux发行版都满足）
- 数据下载后保存在程序所在目录的对应文件夹中

---

## 环境依赖

### Python 版本

- Python 3.8 或更高版本

### 必需依赖

```bash
pip install feedparser requests pandas openpyxl
```

### 可选依赖

如需使用数据入库功能，还需要：

```bash
# Oracle 入库
pip install cx_Oracle

# Hive 入库
pip install pyspark
```

---

## Python 环境部署

### 方式一：使用虚拟环境（推荐）

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 安装依赖
pip install feedparser requests pandas openpyxl

# 4. 运行程序
python udid_daq_interactive.py
```

### 方式二：使用 conda

```bash
# 1. 创建 conda 环境
conda create -n udid_daq python=3.10

# 2. 激活环境
conda activate udid_daq

# 3. 安装依赖
pip install feedparser requests pandas openpyxl

# 4. 运行程序
python udid_daq_interactive.py
```

### 方式三：全局安装

```bash
# 直接全局安装依赖
pip install feedparser requests pandas openpyxl

# 运行交互式版本
python udid_daq_interactive.py

# 运行命令行版本
python udid_daq_daily.py
python udid_daq_monthly.py
```

### 依赖说明

| 依赖包 | 用途 |
|--------|------|
| feedparser | 解析 RSS 订阅，获取下载链接 |
| requests | HTTP 请求，下载 ZIP 文件 |
| pandas | 数据处理和 Excel 操作 |
| openpyxl | Excel 文件读写引擎 |

---

## 交互式版本 (推荐)

### 启动

```bash
python udid_daq_interactive.py
```

### 功能菜单

```
请选择操作:

  1. 查询日度数据 (每日发布)
  2. 查询周度数据 (每周发布)
  3. 查询月度数据 (每月发布)
  4. 查询所有版本 (全量历史)
  5. 查询全量版本 (完整数据包)
  -
  6. 下载日度数据
  7. 下载周度数据
  8. 下载月度数据
  9. 下载所有版本
 10. 下载全量版本
  -
 11. 查看下载目录
  0. 退出程序
```

### 功能说明

| 选项 | 功能 | 说明 |
|------|------|------|
| 1 | 查询日度数据 | 查看每日发布数据（不下载） |
| 2 | 查询周度数据 | 查看每周发布数据 |
| 3 | 查询月度数据 | 查看每月发布数据 |
| 4 | 查询所有版本 | 查看所有历史版本 |
| 5 | 查询全量版本 | 查看完整数据包 |
| 6-10 | 下载对应类型 | 支持选择/最新/全部下载 |
| 11 | 查看下载目录 | 查看已下载数据统计 |

### 下载选项说明

- **输入编号**: 下载指定日期/周期的数据
- **输入 L**: 下载最新的数据
- **输入 A**: 下载所有可用数据

---

## 命令行版本

## 日度数据下载 (udid_daq_daily.py)

> 原始命令行版本，保留参数化执行方式

### 列出所有可用的下载日期

```bash
python udid_daq_daily.py -l
```

### 下载最新日期的数据

```bash
python udid_daq_daily.py
```

### 下载指定日期的数据

```bash
python udid_daq_daily.py -d 20260325
```

### 下载所有日期的数据

```bash
python udid_daq_daily.py -a
```

### 数据输出

下载的数据保存在 `downloads/YYYYMMDD/` 目录下，每个日期生成一个 Excel 文件。

---

## 月度数据下载 (udid_daq_monthly.py)

> 原始命令行版本，保留参数化执行方式

### 列出所有可用的下载月份

```bash
python udid_daq_monthly.py -l
```

### 下载最新月份的数据

```bash
python udid_daq_monthly.py
```

### 下载指定月份的数据

```bash
python udid_daq_monthly.py -m 202601
```

### 下载所有月份的数据

```bash
python udid_daq_monthly.py -a
```

### 数据输出

月度数据保存在 `downloads_monthly/YYYYMM/` 目录下，自动将当月所有日度数据合并为单一文件：
- 文件名格式: `YYYYMM_merged.xlsx`（如 `202601_merged.xlsx`）

### 月度数据说明

- 月度包内包含该月每天的增量数据（双层压缩结构）
- 程序会自动解压并合并所有日度数据
- 合并后按 `deviceRecordKey` 字段排序

---

## 周度数据下载 (udid_daq_weekly.py)

> 命令行周度数据下载器

### 列出所有可用的下载周期

```bash
python udid_daq_weekly.py -l
```

### 下载最新周期的数据

```bash
python udid_daq_weekly.py
```

### 下载指定周期的数据

```bash
python udid_daq_weekly.py -d 20260325
```

### 下载所有周期的数据

```bash
python udid_daq_weekly.py -a
```

### 数据输出

周度数据保存在 `downloads_weekly/YYYYMMDD/` 目录下。

---

## 所有版本下载 (udid_daq_all.py)

> 命令行所有历史版本下载器

### 列出所有可用的版本

```bash
python udid_daq_all.py -l
```

### 下载最新版本

```bash
python udid_daq_all.py
```

### 下载指定版本

```bash
python udid_daq_all.py -d 20260325
```

### 下载所有版本

```bash
python udid_daq_all.py -a
```

### 数据输出

所有版本数据保存在 `downloads_all/YYYYMMDD/` 目录下。

### 注意事项

- 所有版本数据量较大，下载时间较长
- 建议使用 `-l` 先查看可用版本

---

## 全量版本下载 (udid_daq_full.py)

> 命令行完整数据包下载器

### 列出所有可用的全量版本

```bash
python udid_daq_full.py -l
```

### 下载最新全量版本

```bash
python udid_daq_full.py
```

### 下载指定版本

```bash
python udid_daq_full.py -d 20260325
```

### 下载所有全量版本

```bash
python udid_daq_full.py -a
```

### 数据输出

全量数据保存在 `downloads_full/YYYYMMDD/` 目录下。

### 注意事项

- 全量包数据量最大，下载需要较长时间
- 建议使用 `-l` 先查看可用版本

---

## 数据入库扩展

解析完成后支持回调函数，可将数据插入 Oracle 或 Hive 表中。

### 使用方式

在 `if __name__ == "__main__"` 块中取消注释并配置回调函数：

```python
def my_data_handler(df, source_info):
    """
    df: pandas DataFrame, 解析好的数据
    source_info: dict, 包含以下字段:
        - date: 数据日期 (如 '20260325' 或 '202601')
        - source_file: 原始文件名 (如 'UDID_DAY_UPDATE_20260325.xml')
        - source_type: 数据源类型 ('xml' 或 'excel'，月度合并时为 'merged')
    """
    
    # --- Oracle 入库示例 ---
    # import cx_Oracle
    # conn = cx_Oracle.connect('user/password@host:port/service')
    # df.to_sql('your_table', conn, if_exists='append', index=False)
    # conn.close()
    
    # --- Hive 入库示例 ---
    # from pyspark.sql import SparkSession
    # spark = SparkSession.builder.appName("udid_daq").enableHiveSupport().getOrCreate()
    # spark_df = spark.createDataFrame(df)
    # spark_df.write.insertInto('your_db.your_table', overwrite=False)
    
    pass

set_data_callback(my_data_handler)
```

### 注意事项

- 回调函数在数据解析完成后、写入 Excel 前触发
- `df` 为 pandas DataFrame，包含所有解析好的字段
- 原始 XML/Excel 中的所有字段都会保留在 DataFrame 中
- 确保入库时表结构与 DataFrame 列名匹配
- 月度数据回调的 `source_type` 为 `'merged'`，表示是合并后的数据

---

## 交互式版本与命令行版本的关系

交互式版本 `udid_daq_interactive.py` 封装了全部5种数据类型的下载功能，提供用户友好的交互界面。

**两者共享相同的核心逻辑：**
- 相同的 RSS 解析
- 相同的 ZIP 下载和解压
- 相同的 XML/Excel 解析
- 相同的数据回调机制

**命令行版本优势：**
- 适合集成到其他自动化流程
- 适合定时任务/调度器调用
- 参数化控制，适合脚本调用

**交互式版本优势：**
- 可视化操作，无需记忆命令参数
- 可随时查询可用数据，不下载
- 灵活的单个/批量下载选择
- 支持全部5种数据类型
