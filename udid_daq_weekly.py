# -*- coding: utf-8 -*-
"""
UDI 周度数据下载工具
====================

从 NMPA UDI 数据库下载周度汇总数据（自动合并 7 个日度包）。

用法:
    python udid_daq_weekly.py              # 下载最新周度数据
    python udid_daq_weekly.py -l           # 列出可用周期
    python udid_daq_weekly.py -d 20260322  # 下载指定周期（结束日期）
    python udid_daq_weekly.py -a           # 下载所有可用周期
    python udid_daq_weekly.py --excel      # 输出 Excel 格式
    python udid_daq_weekly.py --db oracle  # 写入数据库

作者: geekerxu
版本: 3.0.0
"""

# ============================================================================
# 编码设置
# ============================================================================
from core import setup_encoding

setup_encoding()

# ============================================================================
# 标准库导入
# ============================================================================
import argparse

# ============================================================================
# 本地模块导入
# ============================================================================
from core import UDIDownloader, ensure_download_dir, print_completion


# ============================================================================
# 主函数
# ============================================================================
def main() -> None:
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description="UDI 周度数据下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="列出所有可用的下载周期",
    )
    parser.add_argument(
        "-d",
        "--date",
        help="指定下载周期的结束日期，格式 YYYYMMDD，如 20260322",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="下载所有可用周期的数据",
    )
    parser.add_argument(
        "--excel",
        action="store_true",
        help="输出为 Excel 格式（默认 CSV）",
    )
    parser.add_argument(
        "--db",
        choices=["oracle", "mysql", "hive"],
        help="指定数据库类型，写入数据库",
    )

    args = parser.parse_args()

    # 确保下载目录存在
    ensure_download_dir()

    # 创建下载器
    output_format = "excel" if args.excel else "csv"
    downloader = UDIDownloader("weekly", output_format, args.db)

    # 解析 RSS
    items = downloader.parse_rss()
    if not items:
        print("[ERROR] 没有找到下载链接")
        return

    # 执行操作
    if args.list:
        downloader.list_available()
        return

    if args.all:
        downloader.download_all()
        print_completion()
        return

    if args.date:
        item = downloader.find_by_date(args.date)
        if not item:
            print(f"[ERROR] 未找到周期结束日期为 {args.date} 的数据")
            downloader.list_available()
            return
        downloader.download_single(item)
        print_completion()
        return

    # 默认下载最新
    downloader.download_latest()
    print_completion()


# ============================================================================
# 程序入口
# ============================================================================
if __name__ == "__main__":
    main()
