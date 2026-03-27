import feedparser
import requests
import zipfile
import io
import os
import argparse
from datetime import datetime


RSS_URL = "https://udi.nmpa.gov.cn/rss/download.html?files=monthly"
DOWNLOAD_DIR = "downloads_monthly"

on_data_parsed_callback = None
monthly_dataframes = []


def set_data_callback(callback):
    """设置数据解析完成后的回调函数
    callback(df, source_info) -> None
    source_info: dict, 包含 'date', 'source_file' 等信息
    """
    global on_data_parsed_callback
    on_data_parsed_callback = callback


def parse_rss():
    """解析RSS订阅，获取所有可用的下载链接"""
    print(f"正在解析RSS: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)

    items = []
    for entry in feed.entries:
        title = entry.title
        if "UDID_MONTH_UPDATE_" in title:
            date_str = title.replace("UDID_MONTH_UPDATE_", "").replace(".zip", "")
            try:
                date = datetime.strptime(date_str, "%Y%m")
            except:
                date = None
        else:
            date = None

        items.append(
            {
                "title": title,
                "description": entry.description,
                "link": entry.link,
                "pubdate": entry.get("pubDate", ""),
                "date": date,
                "date_str": date_str if date else None,
            }
        )
    print(f"找到 {len(items)} 个下载链接")
    return items


def list_available_dates(items):
    """列出所有可用的月份"""
    print("\n可用的下载月份:")
    for item in items:
        if item["date"]:
            print(f"  {item['date'].strftime('%Y-%m')} - {item['title']}")
        else:
            print(f"  未知月份 - {item['title']}")
    print()


def download_zip(url, filename):
    """下载zip文件"""
    print(f"正在下载: {filename}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def extract_and_convert(zip_content, output_dir):
    """解压zip文件并转换为Excel"""
    global monthly_dataframes
    os.makedirs(output_dir, exist_ok=True)
    monthly_dataframes = []

    with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
        print(f"zip文件包含: {zf.namelist()}")

        for file_name in zf.namelist():
            if file_name.endswith(".zip"):
                print(f"处理日度压缩包: {file_name}")
                day_zip_content = zf.read(file_name)
                extract_daily_zip(day_zip_content, output_dir)

    merge_and_save_monthly(output_dir)


def extract_daily_zip(day_zip_content, month_output_dir):
    """解压日度zip文件并提取数据"""
    global monthly_dataframes

    with zipfile.ZipFile(io.BytesIO(day_zip_content)) as day_zf:
        print(f"  日度zip包含: {day_zf.namelist()}")

        for file_name in day_zf.namelist():
            if file_name.endswith(".xml"):
                print(f"  处理XML文件: {file_name}")
                xml_content = day_zf.read(file_name)
                df = parse_xml_to_dataframe(xml_content, file_name)
                if df is not None:
                    monthly_dataframes.append(df)
            elif file_name.endswith((".xls", ".xlsx")):
                print(f"  处理Excel文件: {file_name}")
                excel_content = day_zf.read(file_name)
                df = parse_excel_to_dataframe(excel_content)
                if df is not None:
                    monthly_dataframes.append(df)


def merge_and_save_monthly(month_output_dir):
    """合并所有日度数据并保存为月度文件"""
    global monthly_dataframes, on_data_parsed_callback

    if not monthly_dataframes:
        print("警告: 没有数据可合并")
        return

    import pandas as pd

    print(f"\n正在合并 {len(monthly_dataframes)} 个文件...")
    merged_df = pd.concat(monthly_dataframes, ignore_index=True)

    if "deviceRecordKey" in merged_df.columns:
        merged_df = merged_df.sort_values("deviceRecordKey")

    print(f"合并后共 {len(merged_df)} 条记录")

    if on_data_parsed_callback:
        source_info = {
            "date": os.path.basename(month_output_dir),
            "source_file": "monthly_merged",
            "source_type": "merged",
        }
        on_data_parsed_callback(merged_df, source_info)

    excel_filename = os.path.join(
        month_output_dir, f"{os.path.basename(month_output_dir)}_merged.xlsx"
    )
    merged_df.to_excel(excel_filename, index=False, engine="openpyxl")
    print(f"已保存合并文件: {excel_filename}")


def parse_xml_to_dataframe(xml_content, xml_filename):
    """将XML内容解析为DataFrame"""
    import xml.etree.ElementTree as ET
    import pandas as pd

    root = ET.fromstring(xml_content)

    records = []

    devices = root.find("devices")
    if devices is not None:
        for device in devices.findall("device"):
            record = {}
            for child in device:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                record[tag] = (
                    child.text.strip() if child.text and child.text.strip() else ""
                )
            records.append(record)
    else:
        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if len(child) == 0:
                continue
            if tag == "devices":
                for device in child.findall("device"):
                    record = {}
                    for subchild in device:
                        subtag = (
                            subchild.tag.split("}")[-1]
                            if "}" in subchild.tag
                            else subchild.tag
                        )
                        record[subtag] = (
                            subchild.text.strip()
                            if subchild.text and subchild.text.strip()
                            else ""
                        )
                    records.append(record)

    if not records:
        print(f"警告: 无法从 {xml_filename} 中提取数据")
        return None

    df = pd.DataFrame(records)
    print(f"  成功提取 {len(records)} 条记录")
    return df


def parse_excel_to_dataframe(excel_content):
    """将Excel内容解析为DataFrame"""
    import pandas as pd

    df = pd.read_excel(io.BytesIO(excel_content))
    print(f"  成功读取 {len(df)} 条记录")
    return df


def find_by_month(items, month_str):
    """根据月份字符串查找下载项"""
    for item in items:
        if item["date_str"] == month_str:
            return item
    return None


def download_single(item):
    """下载单个文件"""
    print(f"\n选择文件: {item['title']}")
    print(f"发布日期: {item['pubdate']}")

    zip_content = download_zip(item["link"], item["title"])

    output_dir = os.path.join(DOWNLOAD_DIR, item["date_str"])

    extract_and_convert(zip_content, output_dir)

    print(f"\n完成！文件已保存到: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="UDI月度数据下载工具")
    parser.add_argument("-m", "--month", help="指定下载月份，格式YYYYMM，如 202603")
    parser.add_argument(
        "-l", "--list", action="store_true", help="列出所有可用的下载月份"
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="下载所有可用月份的数据"
    )
    args = parser.parse_args()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    items = parse_rss()

    if not items:
        print("没有找到下载链接")
        return

    if args.list:
        list_available_dates(items)
        return

    if args.month:
        item = find_by_month(items, args.month)
        if not item:
            print(f"错误: 找不到月份为 {args.month} 的数据")
            print("\n可用的月份:")
            list_available_dates(items)
            return
        download_single(item)
    elif args.all:
        for item in items:
            if item["date"]:
                download_single(item)
    else:
        latest = items[0]
        for item in items:
            if item["date"] and (not latest["date"] or item["date"] > latest["date"]):
                latest = item
        download_single(latest)


if __name__ == "__main__":
    # ============================================================
    # 数据入库示例：解析完成后插入 Oracle 或 Hive
    # ============================================================
    # 使用方式：
    # 1. 设置回调函数，解析完数据后会调用该函数
    # 2. 在回调函数中自行实现入库逻辑
    #
    # def my_data_handler(df, source_info):
    #     '''
    #     df: pandas DataFrame, 解析好的数据
    #     source_info: dict, 包含 'date', 'source_file', 'source_type' 字段
    #     '''
    #
    #     # --- Oracle 入库示例 ---
    #     # import cx_Oracle
    #     # conn = cx_Oracle.connect('user/password@host:port/service')
    #     # df.to_sql('your_table', conn, if_exists='append', index=False)
    #     # conn.close()
    #
    #     # --- Hive 入库示例 ---
    #     # from pyspark.sql import SparkSession
    #     # spark = SparkSession.builder.appName("udid_daq").enableHiveSupport().getOrCreate()
    #     # spark_df = spark.createDataFrame(df)
    #     # spark_df.write.insertInto('your_db.your_table', overwrite=False)
    #
    #     pass
    #
    # set_data_callback(my_data_handler)
    # ============================================================

    main()
