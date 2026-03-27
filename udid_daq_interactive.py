import feedparser
import requests
import zipfile
import io
import os
from datetime import datetime


DAILY_RSS_URL = "https://udi.nmpa.gov.cn/rss/download.html?files=daily"
MONTHLY_RSS_URL = "https://udi.nmpa.gov.cn/rss/download.html?files=monthly"
DAILY_DOWNLOAD_DIR = "downloads"
MONTHLY_DOWNLOAD_DIR = "downloads_monthly"

on_data_parsed_callback = None
monthly_dataframes = []


def set_data_callback(callback):
    global on_data_parsed_callback
    on_data_parsed_callback = callback


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print("=" * 60)
    print("       UDI 数据下载工具 (交互式版本)")
    print("=" * 60)


def parse_rss(url):
    print(f"\n正在解析RSS: {url}")
    feed = feedparser.parse(url)

    items = []
    is_monthly = "monthly" in url

    for entry in feed.entries:
        title = entry.title
        if is_monthly and "UDID_MONTH_UPDATE_" in title:
            date_str = title.replace("UDID_MONTH_UPDATE_", "").replace(".zip", "")
            fmt = "%Y%m"
        elif not is_monthly and "UDID_DAY_UPDATE_" in title:
            date_str = title.replace("UDID_DAY_UPDATE_", "").replace(".zip", "")
            fmt = "%Y%m%d"
        else:
            continue

        try:
            date = datetime.strptime(date_str, fmt)
        except:
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

    items.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    print(f"找到 {len(items)} 个下载链接\n")
    return items


def download_zip(url, filename):
    print(f"正在下载: {filename}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def extract_daily_zip(day_zip_content, month_output_dir):
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


def parse_xml_to_dataframe(xml_content, xml_filename):
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
    import pandas as pd

    df = pd.read_excel(io.BytesIO(excel_content))
    print(f"  成功读取 {len(df)} 条记录")
    return df


def extract_and_convert_monthly(zip_content, output_dir):
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


def merge_and_save_monthly(month_output_dir):
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


def extract_and_convert_daily(zip_content, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
        print(f"zip文件包含: {zf.namelist()}")
        for file_name in zf.namelist():
            if file_name.endswith(".xml"):
                print(f"处理XML文件: {file_name}")
                xml_content = zf.read(file_name)
                convert_xml_to_excel(xml_content, file_name, output_dir)
            elif file_name.endswith((".xls", ".xlsx")):
                print(f"处理Excel文件: {file_name}")
                excel_content = zf.read(file_name)
                convert_excel_to_excel(excel_content, file_name, output_dir)


def convert_xml_to_excel(xml_content, xml_filename, output_dir):
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
        return

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
    print(f"成功提取 {len(records)} 条记录 -> {excel_filename}")


def convert_excel_to_excel(excel_content, excel_filename, output_dir):
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
    out_filename = os.path.join(output_dir, f"{base_name}.xlsx")
    df.to_excel(out_filename, index=False, engine="openpyxl")
    print(f"成功转换 -> {out_filename}")


def download_daily(item):
    print(f"\n选择文件: {item['title']}")
    print(f"发布日期: {item['pubdate']}")
    zip_content = download_zip(item["link"], item["title"])
    output_dir = os.path.join(DAILY_DOWNLOAD_DIR, item["date_str"])
    extract_and_convert_daily(zip_content, output_dir)
    print(f"\n完成！文件已保存到: {output_dir}")


def download_monthly(item):
    print(f"\n选择文件: {item['title']}")
    print(f"发布日期: {item['pubdate']}")
    zip_content = download_zip(item["link"], item["title"])
    output_dir = os.path.join(MONTHLY_DOWNLOAD_DIR, item["date_str"])
    extract_and_convert_monthly(zip_content, output_dir)
    print(f"\n完成！文件已保存到: {output_dir}")


def query_daily():
    clear_screen()
    print_banner()
    print(" [日度数据查询模式]\n")
    items = parse_rss(DAILY_RSS_URL)

    if not items:
        print("没有找到下载链接")
        input("\n按回车键返回...")
        return

    print("可用的下载日期:")
    print("-" * 50)
    for i, item in enumerate(items, 1):
        date_display = item["date"].strftime("%Y-%m-%d") if item["date"] else "未知"
        print(f"  {i:3}. {date_display} - {item['title']}")
    print("-" * 50)
    print(f"  0. 返回上一级")
    print()

    while True:
        try:
            choice = input("请选择要查询详情的日期编号 (0返回): ").strip()
            if choice == "0":
                break
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                item = items[idx]
                print(f"\n文件名: {item['title']}")
                print(f"发布日期: {item['pubdate']}")
                print(f"链接: {item['link']}")
                print(f"描述: {item['description']}")
                input("\n按回车键继续...")
                break
            else:
                print("无效选择，请重试")
        except ValueError:
            print("请输入有效数字")


def query_monthly():
    clear_screen()
    print_banner()
    print(" [月度数据查询模式]\n")
    items = parse_rss(MONTHLY_RSS_URL)

    if not items:
        print("没有找到下载链接")
        input("\n按回车键返回...")
        return

    print("可用的下载月份:")
    print("-" * 50)
    for i, item in enumerate(items, 1):
        date_display = item["date"].strftime("%Y-%m") if item["date"] else "未知"
        print(f"  {i:3}. {date_display} - {item['title']}")
    print("-" * 50)
    print(f"  0. 返回上一级")
    print()

    while True:
        try:
            choice = input("请选择要查询详情的月份编号 (0返回): ").strip()
            if choice == "0":
                break
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                item = items[idx]
                print(f"\n文件名: {item['title']}")
                print(f"发布日期: {item['pubdate']}")
                print(f"链接: {item['link']}")
                print(f"描述: {item['description']}")
                input("\n按回车键继续...")
                break
            else:
                print("无效选择，请重试")
        except ValueError:
            print("请输入有效数字")


def download_daily_interactive():
    clear_screen()
    print_banner()
    print(" [日度数据下载模式]\n")
    items = parse_rss(DAILY_RSS_URL)

    if not items:
        print("没有找到下载链接")
        input("\n按回车键返回...")
        return

    print("可用的下载日期:")
    print("-" * 50)
    for i, item in enumerate(items, 1):
        date_display = item["date"].strftime("%Y-%m-%d") if item["date"] else "未知"
        print(f"  {i:3}. {date_display}")
    print("-" * 50)
    print(f"  A. 下载所有日期")
    print(f"  L. 下载最新日期")
    print(f"  0. 返回上一级")
    print()

    while True:
        choice = input("请选择 (0/A/L/编号): ").strip().upper()
        if choice == "0":
            return
        elif choice == "A":
            for item in items:
                if item["date"]:
                    download_daily(item)
            input("\n全部下载完成！按回车键返回...")
            break
        elif choice == "L":
            for item in items:
                if item["date"]:
                    download_daily(item)
                    break
            input("\n下载完成！按回车键返回...")
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    download_daily(items[idx])
                    input("\n下载完成！按回车键返回...")
                    break
                else:
                    print("无效选择，请重试")
            except ValueError:
                print("无效输入，请重试")


def download_monthly_interactive():
    clear_screen()
    print_banner()
    print(" [月度数据下载模式]\n")
    items = parse_rss(MONTHLY_RSS_URL)

    if not items:
        print("没有找到下载链接")
        input("\n按回车键返回...")
        return

    print("可用的下载月份:")
    print("-" * 50)
    for i, item in enumerate(items, 1):
        date_display = item["date"].strftime("%Y-%m") if item["date"] else "未知"
        print(f"  {i:3}. {date_display}")
    print("-" * 50)
    print(f"  A. 下载所有月份")
    print(f"  L. 下载最新月份")
    print(f"  0. 返回上一级")
    print()

    while True:
        choice = input("请选择 (0/A/L/编号): ").strip().upper()
        if choice == "0":
            return
        elif choice == "A":
            for item in items:
                if item["date"]:
                    download_monthly(item)
            input("\n全部下载完成！按回车键返回...")
            break
        elif choice == "L":
            for item in items:
                if item["date"]:
                    download_monthly(item)
                    break
            input("\n下载完成！按回车键返回...")
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    download_monthly(items[idx])
                    input("\n下载完成！按回车键返回...")
                    break
                else:
                    print("无效选择，请重试")
            except ValueError:
                print("无效输入，请重试")


def main_menu():
    while True:
        clear_screen()
        print_banner()
        print("\n请选择操作:\n")
        print("  1. 查询日度数据 (查看可用日期)")
        print("  2. 查询月度数据 (查看可用月份)")
        print("  3. 下载日度数据")
        print("  4. 下载月度数据")
        print("  5. 查看下载目录")
        print("  0. 退出程序")
        print()

        choice = input("请选择 (0-5): ").strip()

        if choice == "1":
            query_daily()
        elif choice == "2":
            query_monthly()
        elif choice == "3":
            download_daily_interactive()
        elif choice == "4":
            download_monthly_interactive()
        elif choice == "5":
            show_downloads()
        elif choice == "0":
            print("\n感谢使用！再见。\n")
            break
        else:
            print("\n无效选择，请重试")
            input()


def show_downloads():
    clear_screen()
    print_banner()
    print(" [下载目录查看]\n")

    print(f"日度数据目录: {DAILY_DOWNLOAD_DIR}")
    if os.path.exists(DAILY_DOWNLOAD_DIR):
        dirs = [
            d
            for d in os.listdir(DAILY_DOWNLOAD_DIR)
            if os.path.isdir(os.path.join(DAILY_DOWNLOAD_DIR, d))
        ]
        dirs.sort(reverse=True)
        if dirs:
            print(f"  共有 {len(dirs)} 个日期的数据")
            print("  最近5个:")
            for d in dirs[:5]:
                files = os.listdir(os.path.join(DAILY_DOWNLOAD_DIR, d))
                print(f"    {d}: {len(files)} 个文件")
        else:
            print("  (空目录)")
    else:
        print("  (目录不存在)")

    print(f"\n月度数据目录: {MONTHLY_DOWNLOAD_DIR}")
    if os.path.exists(MONTHLY_DOWNLOAD_DIR):
        dirs = [
            d
            for d in os.listdir(MONTHLY_DOWNLOAD_DIR)
            if os.path.isdir(os.path.join(MONTHLY_DOWNLOAD_DIR, d))
        ]
        dirs.sort(reverse=True)
        if dirs:
            print(f"  共有 {len(dirs)} 个月份的数据")
            print("  最近5个:")
            for d in dirs[:5]:
                files = os.listdir(os.path.join(MONTHLY_DOWNLOAD_DIR, d))
                print(f"    {d}: {len(files)} 个文件")
        else:
            print("  (空目录)")
    else:
        print("  (目录不存在)")

    input("\n按回车键返回...")


if __name__ == "__main__":
    main_menu()
