# -*- coding: utf-8 -*-
"""
UDI 全量数据下载工具
====================

从 NMPA UDI 数据库下载全量数据包（仅一个文件，直接下载最新）。

注意:
    全量数据过大，仅支持 CSV 和数据库输出，禁止输出 Excel。

用法:
    python udid_daq_full.py              # 下载最新全量数据（CSV）
    python udid_daq_full.py -l           # 列出可用版本
    python udid_daq_full.py --db oracle  # 写入数据库

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
        description="UDI 全量数据下载工具（仅一个文件，直接下载最新）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="列出可用版本",
    )
    parser.add_argument(
        "--db",
        choices=["oracle", "mysql", "hive"],
        help="指定数据库类型，写入数据库",
    )

    args = parser.parse_args()

    # 确保下载目录存在
    ensure_download_dir()

    # 创建下载器（全量数据强制 CSV 输出）
    try:
        downloader = UDIDownloader("full", "csv", args.db)
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        return
    except ImportError as e:
        print(f"\n[ERROR] {e}")
        return
    except ConnectionError as e:
        print(f"\n[ERROR] {e}")
        return

    # 解析 RSS
    items = downloader.parse_rss()
    if not items:
        print("[ERROR] 没有找到下载链接")
        return

    # 执行操作
    if args.list:
        downloader.list_available()
        return

    # 默认下载最新（全量包只有一个文件）
    downloader.download_latest()
    print_completion()


# ============================================================================
# 程序入口
# ============================================================================
if __name__ == "__main__":
    main()
