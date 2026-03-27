import feedparser
import requests
import zipfile
import io
import os
import argparse
from datetime import datetime


RSS_URL = "https://udi.nmpa.gov.cn/rss/download.html?files=full"
DOWNLOAD_DIR = "downloads_full"

on_data_parsed_callback = None


def set_data_callback(callback):
    """设置数据解析完成后的回调函数"""
    global on_data_parsed_callback
    on_data_parsed_callback = callback


def parse_rss():
    """解析RSS订阅，获取所有可用的下载链接"""
    print(f"正在解析RSS: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)

    items = []
    for entry in feed.entries:
        title = entry.title
        # 全量发布
        if "UDID_FULL_UPDATE_" in title or "UDID_FULLBUILD_" in title:
            date_str = (
                title.replace("UDID_FULL_UPDATE_", "")
                .replace("UDID_FULLBUILD_", "")
                .replace(".zip", "")
            )
            try:
                date = datetime.strptime(date_str, "%Y%m%d")
            except:
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
    """列出所有可用的全量版本日期"""
    print("\n可用的全量版本:")
    for item in items:
        if item["date"]:
            print(f"  {item['date'].strftime('%Y-%m-%d')} - {item['title']}")
        else:
            print(f"  未知日期 - {item['title']}")
    print()


def download_zip(url, filename):
    """下载zip文件"""
    print(f"正在下载: {filename}")
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    return response.content


def extract_and_convert(zip_content, output_dir):
    """解压zip文件并转换为Excel"""
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
        print(f"zip文件包含: {zf.namelist()}")

        for file_name in zf.namelist():
            if file_name.endswith(".xml"):
                print(f"处理XML文件: {file_name}")
                xml_content = zf.read(file_name)
                excel_filename = convert_xml_to_excel(
                    xml_content, file_name, output_dir
                )
                print(f"已转换为Excel: {excel_filename}")
            elif file_name.endswith((".xls", ".xlsx")):
                print(f"处理Excel文件: {file_name}")
                excel_content = zf.read(file_name)
                excel_filename = convert_excel_to_excel(
                    excel_content, file_name, output_dir
                )
                print(f"已转换为Excel: {excel_filename}")


def convert_xml_to_excel(xml_content, xml_filename, output_dir):
    """将XML内容转换为Excel"""
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

    if "deviceRecordKey" in df.columns:
        df = df.sort_values("deviceRecordKey")

    if on_data_parsed_callback:
        source_info = {
            "date": os.path.basename(output_dir),
            "source_file": xml_filename,
            "source_type": "xml",
        }
        on_data_parsed_callback(df, source_info)

    base_name = os.path.splitext(os.path.basename(xml_filename))[0]
    excel_filename = os.path.join(output_dir, f"{base_name}.xlsx")

    df.to_excel(excel_filename, index=False, engine="openpyxl")

    print(f"成功提取 {len(records)} 条记录")
    return excel_filename


def convert_excel_to_excel(excel_content, excel_filename, output_dir):
    """将Excel内容转换为Excel"""
    import pandas as pd

    df = pd.read_excel(io.BytesIO(excel_content))

    if on_data_parsed_callback:
        source_info = {
            "date": os.path.basename(output_dir),
            "source_file": excel_filename,
            "source_type": "excel",
        }
        on_data_parsed_callback(df, source_info)

    base_name = os.path.splitext(os.path.basename(excel_filename))[0]
    excel_filename = os.path.join(output_dir, f"{base_name}.xlsx")

    df.to_excel(excel_filename, index=False, engine="openpyxl")

    return excel_filename


def find_by_date(items, date_str):
    """根据日期字符串查找下载项"""
    for item in items:
        if item["date_str"] == date_str:
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
    parser = argparse.ArgumentParser(description="UDI全量数据下载工具")
    parser.add_argument("-d", "--date", help="指定下载日期，格式YYYYMMDD，如 20260325")
    parser.add_argument(
        "-l", "--list", action="store_true", help="列出所有可用的下载日期"
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="下载所有可用日期的数据"
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

    if args.date:
        item = find_by_date(items, args.date)
        if not item:
            print(f"错误: 找不到日期为 {args.date} 的数据")
            print("\n可用的日期:")
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
    main()
