# -*- coding: utf-8 -*-
"""
UDI 数据下载工具 - 交互式界面
==============================

提供交互式菜单界面，支持：
- 全量/日度/周度/月度数据下载
- 列出可用版本
- 数据库配置
- 并行度设置

用法:
    python udid_daq_interactive.py

作者: geekerxu
版本: 3.1.0
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
# 交互式菜单类
# ============================================================================
class UDIInteractiveMenu:
    """UDI 数据下载交互式菜单"""

    def __init__(self):
        self.data_type = "full"
        self.output_format = "csv"
        self.db_type = None
        self.max_workers = 2
        self.running = True

    def clear_screen(self):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        """打印标题"""
        print("=" * 60)
        print("        UDI 数据下载工具 - 交互式界面 v3.1.0")
        print("=" * 60)
        print()

    def print_current_settings(self):
        """打印当前设置"""
        type_names = {
            "daily": "日度",
            "weekly": "周度",
            "monthly": "月度",
            "full": "全量",
        }
        print("当前设置:")
        print(f"  - 数据类型: {type_names.get(self.data_type, self.data_type)}")
        print(f"  - 输出格式: {self.output_format.upper()}")
        print(f"  - 数据库: {self.db_type or '不写入数据库'}")
        print(f"  - 并行度: {self.max_workers} 个工作进程")
        print()

    def print_main_menu(self):
        """打印主菜单"""
        self.print_header()
        self.print_current_settings()
        print("请选择操作:")
        print()
        print("  [1] 下载数据")
        print("  [2] 列出可用版本")
        print("  [3] 切换数据类型")
        print("  [4] 切换输出格式")
        print("  [5] 数据库配置")
        print("  [6] 并行度设置")
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
        self.clear_screen()
        self.print_header()
        print("选择数据类型:")
        print()
        print("  [1] 全量数据 (full)")
        print("  [2] 日度数据 (daily)")
        print("  [3] 周度数据 (weekly)")
        print("  [4] 月度数据 (monthly)")
        print("  [0] 返回")
        print()

        choice = self.get_input("请输入选项 [0-4]: ")

        type_map = {
            "1": "full",
            "2": "daily",
            "3": "weekly",
            "4": "monthly",
        }

        if choice in type_map:
            self.data_type = type_map[choice]
            print(f"\n已切换到: {self.data_type}")
            input("\n按回车键继续...")

    def select_output_format(self):
        """选择输出格式"""
        self.clear_screen()
        self.print_header()
        print("选择输出格式:")
        print()
        print("  [1] CSV (推荐，大数据量)")
        print("  [2] Excel (仅适用于小数据量)")
        print("  [0] 返回")
        print()

        choice = self.get_input("请输入选项 [0-2]: ")

        if choice == "1":
            self.output_format = "csv"
            print("\n已切换到: CSV")
            input("\n按回车键继续...")
        elif choice == "2":
            self.output_format = "excel"
            print("\n已切换到: Excel")
            print("注意: 全量数据禁止使用 Excel 格式！")
            input("\n按回车键继续...")

    def configure_database(self):
        """配置数据库"""
        self.clear_screen()
        self.print_header()
        print("数据库配置:")
        print()
        print("  [1] Oracle")
        print("  [2] MySQL")
        print("  [3] Hive")
        print("  [4] 不写入数据库")
        print("  [0] 返回")
        print()

        choice = self.get_input("请输入选项 [0-4]: ")

        db_map = {
            "1": "oracle",
            "2": "mysql",
            "3": "hive",
            "4": None,
        }

        if choice in db_map:
            self.db_type = db_map[choice]
            if self.db_type:
                print(f"\n已配置: {self.db_type}")
            else:
                print("\n已取消数据库写入")
            input("\n按回车键继续...")

    def configure_parallelism(self):
        """配置并行度"""
        self.clear_screen()
        self.print_header()
        print("并行度设置:")
        print()
        print(f"  当前并行度: {self.max_workers} 个工作进程")
        print("  (建议设置为 CPU 核心数)")
        print()
        print("  [1] 自动检测 (CPU 核心数)")
        print("  [2] 手动输入")
        print("  [0] 返回")
        print()

        choice = self.get_input("请输入选项 [0-2]: ")

        if choice == "1":
            import multiprocessing

            self.max_workers = multiprocessing.cpu_count()
            print(f"\n已设置并行度: {self.max_workers}")
            input("\n按回车键继续...")
        elif choice == "2":
            try:
                workers = int(self.get_input("请输入并行度 (1-16): "))
                if 1 <= workers <= 16:
                    self.max_workers = workers
                    print(f"\n已设置并行度: {self.max_workers}")
                else:
                    print("\n输入无效，请输入 1-16 之间的数字")
            except ValueError:
                print("\n输入无效")
            input("\n按回车键继续...")

    def download_data(self):
        """下载数据"""
        self.clear_screen()
        self.print_header()

        # 检查输出格式限制
        if self.data_type == "full" and self.output_format == "excel":
            print("[错误] 全量数据禁止使用 Excel 格式！")
            print("请先切换输出格式为 CSV。")
            input("\n按回车键返回...")
            return

        type_names = {
            "daily": "日度",
            "weekly": "周度",
            "monthly": "月度",
            "full": "全量",
        }

        print(f"准备下载: {type_names.get(self.data_type, self.data_type)} 数据")
        print()

        print("  [1] 下载最新数据")
        print("  [2] 列出并选择下载")
        print("  [0] 返回")
        print()

        choice = self.get_input("请输入选项 [0-2]: ")

        if choice == "1":
            self._do_download_latest()
        elif choice == "2":
            self._download_selected()

    def _do_download_latest(self):
        """执行下载最新数据"""
        print("\n开始下载...")
        print("-" * 40)

        ensure_download_dir()

        downloader = UDIDownloader(self.data_type, self.output_format, self.db_type)

        items = downloader.parse_rss()
        if not items:
            print("[错误] 没有找到下载链接")
            input("\n按回车键返回...")
            return

        try:
            filepath = downloader.download_latest()
            if filepath:
                print_completion()
            else:
                print("\n[完成] 下载完成")
        except Exception as e:
            print(f"\n[错误] 下载失败: {e}")

        input("\n按回车键返回...")

    def _download_selected(self):
        """列出并选择下载"""
        print("\n正在获取可用版本列表...")
        print("-" * 40)

        downloader = UDIDownloader(self.data_type, self.output_format, self.db_type)

        items = downloader.parse_rss()
        if not items:
            print("[错误] 没有找到下载链接")
            input("\n按回车键返回...")
            return

        downloader.list_available()

        print("  [0] 返回")
        print()

        # 显示带编号的列表
        for idx, item in enumerate(items, 1):
            date_str = item.get("date_str", "未知")
            print(f"  [{idx}] {date_str}")

        print()
        choice = self.get_input("请选择要下载的版本 [0-{}]: ".format(len(items)))

        try:
            idx = int(choice)
            if idx == 0:
                return
            if 1 <= idx <= len(items):
                selected = items[idx - 1]
                print(f"\n开始下载: {selected.get('date_str', '未知')}")
                print("-" * 40)

                ensure_download_dir()

                try:
                    filepath = downloader.download_single(selected)
                    if filepath:
                        print_completion()
                    else:
                        print("\n[完成] 下载完成")
                except Exception as e:
                    print(f"\n[错误] 下载失败: {e}")

                input("\n按回车键返回...")
            else:
                print("\n无效的选择")
                input("\n按回车键返回...")
        except ValueError:
            print("\n无效的输入")
            input("\n按回车键返回...")

    def list_versions(self):
        """列出可用版本"""
        self.clear_screen()
        self.print_header()

        print("正在获取可用版本列表...")
        print("-" * 40)

        downloader = UDIDownloader(self.data_type, self.output_format, self.db_type)

        items = downloader.parse_rss()
        if items:
            downloader.list_available()
        else:
            print("没有找到可用版本")

        input("\n按回车键返回...")

    def run(self):
        """运行主循环"""
        while self.running:
            self.clear_screen()
            self.print_main_menu()

            choice = self.get_input("请输入选项 [0-6]: ")

            if choice == "1":
                self.download_data()
            elif choice == "2":
                self.list_versions()
            elif choice == "3":
                self.select_data_type()
            elif choice == "4":
                self.select_output_format()
            elif choice == "5":
                self.configure_database()
            elif choice == "6":
                self.configure_parallelism()
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
