# UDID 数据下载工具使用说明

## 工具简介

从国家药监局UDI数据库自动下载UDI数据，支持日度和月度两种下载模式：
- **交互式版本 (udid_daq_interactive.py)**: 图形化交互操作，可查询、可选择、可下载
- **日度数据 (udid_daq_daily.py)**: 命令行下载每日增量数据
- **月度数据 (udid_daq_monthly.py)**: 命令行下载月度数据，自动合并为单个文件

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

## 交互式版本 (推荐)

### 启动

```bash
python udid_daq_interactive.py
```

### 功能菜单

```
请选择操作:

  1. 查询日度数据 (查看可用日期)
  2. 查询月度数据 (查看可用月份)
  3. 下载日度数据
  4. 下载月度数据
  5. 查看下载目录
  0. 退出程序
```

### 功能说明

| 选项 | 功能 | 说明 |
|------|------|------|
| 1 | 查询日度数据 | 查看所有可用的日度下载日期（不下载） |
| 2 | 查询月度数据 | 查看所有可用的月度下载月份（不下载） |
| 3 | 下载日度数据 | 支持选择日期/最新/全部下载 |
| 4 | 下载月度数据 | 支持选择月份/最新/全部下载 |
| 5 | 查看下载目录 | 查看已下载数据统计 |

### 下载选项说明

- **输入编号**: 下载指定日期/月份的数据
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

交互式版本 `udid_daq_interactive.py` 封装了日度和月度下载功能，提供用户友好的交互界面。

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
