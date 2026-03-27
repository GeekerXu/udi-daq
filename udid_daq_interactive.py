# -*- coding: utf-8 -*-
"""
UDI 数据下载工具 - 交互式界面
==============================

交互式菜单界面，支持：
- 查看各类数据的可用版本
- 选择下载数据
- 选择输出格式（CSV/Excel）

用法:
    python udid_daq_interactive.py

作者: geekerxu
版本: 3.2.0
"""

# ============================================================================
# 编码设置
# ============================================================================
from core import setup_encoding

setup_encoding()

# ============================================================================
# 标准库导入
# ============================================================================
import os
import sys

# ============================================================================
# 本地模块导入
# ============================================================================
from core import UDIDownloader, ensure_download_dir, print_completion


# ============================================================================
# 常量定义
# ============================================================================
DATA_TYPES = {
    "1": ("daily", "日度"),
    "2": ("weekly", "周度"),
    "3": ("monthly", "月度"),
    "4": ("full", "全量"),
}

MAX_EXCEL_ROWS = 1_000_000  # Excel 最大行数限制


# ============================================================================
# 交互式菜单类
# ============================================================================
class UDIInteractiveMenu:
    """UDI 数据下载交互式菜单"""

    def __init__(self):
        self.data_type = "daily"
        self.data_type_name = "日度"
        self.output_format = "csv"
        self.downloader = None
        self.running = True

    def clear_screen(self):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        """打印标题"""
        print("=" * 60)
        print("        UDI 数据下载工具 - 交互式界面 v3.2.0")
        print("=" * 60)
        print()

    def print_current_settings(self):
        """打印当前设置"""
        print("当前设置:")
        print(f"  - 数据类型: {self.data_type_name}")
        print(f"  - 输出格式: {self.output_format.upper()}")
        print()

    def print_main_menu(self):
        """打印主菜单"""
        self.print_header()
        self.print_current_settings()
        print("请选择操作:")
        print()
        print("  [1] 切换数据类型")
        print("  [2] 选择输出格式")
        print("  [3] 查看可用版本")
        print("  [4] 下载数据")
        print("  [0] 退出")
        print()

    def get_input(self, prompt: str) -> str:
        """获取用户输入"""
        try:
            return input(prompt).strip()
        except EOFError:
            return ""
        except KeyboardInterrupt:
            print("\n\n用户取消操作")
            return "0"

    def select_data_type(self):
        """选择数据类型"""
        while True:
            self.clear_screen()
            self.print_header()
            print("选择数据类型:")
            print()
            print("  [1] 日度数据 (daily)")
            print("  [2] 周度数据 (weekly)")
            print("  [3] 月度数据 (monthly)")
            print("  [4] 全量数据 (full)")
            print("  [0] 返回")
            print()

            choice = self.get_input("请输入选项 [0-4]: ")

            if choice == "0":
                return
            elif choice in DATA_TYPES:
                self.data_type, self.data_type_name = DATA_TYPES[choice]
                print(f"\n已切换到: {self.data_type_name}")
                input("\n按回车键继续...")
                return
            else:
                print("\n无效的选项")
                input("\n按回车键继续...")

    def select_output_format(self):
        """选择输出格式"""
        while True:
            self.clear_screen()
            self.print_header()
            print("选择输出格式:")
            print()
            print("  [1] CSV (推荐，支持大数据量)")
            print("  [2] Excel (仅适用于小于100万行数据)")
            print("  [0] 返回")
            print()

            choice = self.get_input("请输入选项 [0-2]: ")

            if choice == "0":
                return
            elif choice == "1":
                self.output_format = "csv"
                print("\n已选择: CSV")
                input("\n按回车键继续...")
                return
            elif choice == "2":
                self.output_format = "excel"
                print("\n已选择: Excel")
                print("注意: 数据行数超过100万时将自动切换为 CSV")
                input("\n按回车键继续...")
                return
            else:
                print("\n无效的选项")
                input("\n按回车键继续...")

    def init_downloader(self):
        """初始化下载器"""
        if self.downloader is None or self.downloader.data_type != self.data_type:
            self.downloader = UDIDownloader(self.data_type, self.output_format)

    def list_versions(self):
        """列出可用版本"""
        self.clear_screen()
        self.print_header()

        print(f"正在获取 {self.data_type_name} 数据的可用版本...")
        print("-" * 40)

        self.init_downloader()
        items = self.downloader.parse_rss()

        if items:
            self.downloader.list_available()
        else:
            print("没有找到可用版本")

        input("\n按回车键返回...")

    def download_data(self):
        """下载数据"""
        self.clear_screen()
        self.print_header()

        print(f"正在获取 {self.data_type_name} 数据的可用版本...")
        print("-" * 40)

        self.init_downloader()
        items = self.downloader.parse_rss()

        if not items:
            print("[错误] 没有找到下载链接")
            input("\n按回车键返回...")
            return

        self.downloader.list_available()
        print(f"  [0] 返回")
        print()

        # 显示带编号的列表
        for idx, item in enumerate(items, 1):
            date_str = item.get("date_str", "未知")
            print(f"  [{idx}] {date_str}")

        print()
        choice = self.get_input(f"请选择要下载的版本 [0-{len(items)}]: ")

        if choice == "0":
            return

        try:
            idx = int(choice)
            if 1 <= idx <= len(items):
                selected = items[idx - 1]
                self._do_download(selected)
            else:
                print("\n无效的选择")
                input("\n按回车键返回...")
        except ValueError:
            print("\n无效的输入")
            input("\n按回车键返回...")

    def _do_download(self, item):
        """执行下载"""
        import zipfile
        import io

        date_str = item.get("date_str", "未知")
        print(f"\n开始下载: {date_str}")
        print("-" * 40)

        ensure_download_dir()

        # 重新创建下载器，使用当前选择的格式
        self.downloader = UDIDownloader(self.data_type, self.output_format)

        try:
            # 先获取数据，检查行数
            zip_content = self.downloader.download_zip(item["link"])

            # 如果选择 Excel，需要先检查数据量
            if self.output_format == "excel":
                print("\n[检查] 正在检查数据量...")

                # 快速统计记录数
                record_count = self._count_records(zip_content)

                if record_count > MAX_EXCEL_ROWS:
                    print(
                        f"[警告] 数据量 {record_count:,} 行超过 Excel 限制 ({MAX_EXCEL_ROWS:,} 行)"
                    )
                    print("[提示] 自动切换为 CSV 格式")
                    self.output_format = "csv"
                    self.downloader = UDIDownloader(self.data_type, "csv")
                else:
                    print(f"[检查] 数据量 {record_count:,} 行，可以使用 Excel 格式")

            # 执行下载
            identifier = item.get("period_str") or item.get("date_str") or "unknown"

            if self.data_type == "full":
                filepath = self.downloader.extract_and_save_streaming(
                    zip_content, identifier
                )
            else:
                dfs = self.downloader.extract_to_dataframes(zip_content)
                if dfs:
                    filepath = self.downloader.merge_and_save(dfs, identifier)
                else:
                    filepath = None

            if filepath:
                print_completion()
            else:
                print("\n[完成] 下载完成")

        except Exception as e:
            print(f"\n[错误] 下载失败: {e}")

        input("\n按回车键返回...")

    def _count_records(self, zip_content: bytes) -> int:
        """
        快速统计 ZIP 中的记录数

        参数:
            zip_content: ZIP 文件内容

        返回:
            记录总数
        """
        import io
        import zipfile
        from xml_parser import parse_xml_to_records

        total_count = 0

        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            for file_name in zf.namelist():
                if file_name.endswith(".xml"):
                    try:
                        xml_content = zf.read(file_name)
                        records = parse_xml_to_records(xml_content)
                        if records:
                            total_count += len(records)
                    except Exception:
                        pass
                elif file_name.endswith(".zip"):
                    # 嵌套 ZIP
                    try:
                        nested_content = zf.read(file_name)
                        total_count += self._count_records(nested_content)
                    except Exception:
                        pass

        return total_count

    def run(self):
        """运行主循环"""
        while self.running:
            self.clear_screen()
            self.print_main_menu()

            choice = self.get_input("请输入选项 [0-4]: ")

            if choice == "1":
                self.select_data_type()
            elif choice == "2":
                self.select_output_format()
            elif choice == "3":
                self.list_versions()
            elif choice == "4":
                self.download_data()
            elif choice == "0":
                self.running = False
                self.clear_screen()
                print("\n感谢使用 UDI 数据下载工具！\n")
            else:
                print("\n无效的选项，请重新输入")
                input("\n按回车键继续...")


# ============================================================================
# 程序入口
# ============================================================================
def main():
    """主入口"""
    try:
        menu = UDIInteractiveMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
