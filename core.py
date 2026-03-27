# -*- coding: utf-8 -*-
"""
UDI 数据下载核心模块
====================

提供所有下载器共享的核心功能，包括：
- RSS 订阅解析
- ZIP 文件下载与解压
- 数据格式转换（XML/Excel → DataFrame）
- 数据合并与保存
- 数据库写入支持
- 流式处理（内存优化）

作者: geekerxu
版本: 3.1.0
"""

# ============================================================================
# 标准库导入
# ============================================================================
import gc
import io
import os
import re
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# ============================================================================
# 第三方库导入
# ============================================================================
import feedparser
import pandas as pd
import requests

# ============================================================================
# 本地模块导入
# ============================================================================
from xml_parser import parse_xml_to_records, records_to_dataframe
from db_helper import (
    save_to_database,
    is_database_enabled,
    get_db_type,
    set_db_config,
)

# ============================================================================
# 常量定义
# ============================================================================
RSS_BASE_URL = "https://udi.nmpa.gov.cn/rss/download.html"
DOWNLOAD_DIR = "download"

DATA_TYPES = {
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "monthly",
    "full": "full",
}

TITLE_PATTERNS = {
    "daily": r"UDID_DAY_UPDATE_(\d{8})",
    "weekly": r"UDID_WEEKLY_UPDATE_(\d{8})_(\d{8})",
    "monthly": r"UDID_MONTH_UPDATE_(\d{6})",
    "full": r"UDID_FULL_RELEASE_(\d{8})",
}


# ============================================================================
# 并行处理辅助函数（模块级，支持pickle）
# ============================================================================
def _parse_xml_worker(xml_content: bytes) -> Optional[pd.DataFrame]:
    """并行XML解析工作函数"""
    try:
        records = parse_xml_to_records(xml_content)
        if records:
            return records_to_dataframe(records)
    except Exception:
        pass
    return None


# ============================================================================
# 核心类定义
# ============================================================================
class UDIDownloader:
    """UDI 数据下载器核心类"""

    def __init__(
        self,
        data_type: str,
        output_format: str = "csv",
        db_type: Optional[str] = None,
    ):
        self.data_type = data_type
        self.output_format = output_format
        self.rss_url = f"{RSS_BASE_URL}?files={DATA_TYPES[data_type]}"
        self._items: List[Dict[str, Any]] = []
        self._on_data_callback: Optional[Callable] = None

        if db_type:
            set_db_config(db_type, {})

    @property
    def items(self) -> List[Dict[str, Any]]:
        return self._items

    def set_data_callback(self, callback: Callable) -> None:
        self._on_data_callback = callback

    # ------------------------------------------------------------------------
    # RSS 解析
    # ------------------------------------------------------------------------
    def parse_rss(self) -> List[Dict[str, Any]]:
        print(f"[INFO] 正在解析 RSS: {self.rss_url}")

        try:
            feed = feedparser.parse(self.rss_url)
        except Exception as e:
            print(f"[ERROR] RSS 解析失败: {e}")
            self._items = []
            return self._items

        self._items = []
        pattern = TITLE_PATTERNS.get(self.data_type)

        for entry in feed.entries:
            title = str(getattr(entry, "title", ""))
            link = str(getattr(entry, "link", ""))
            item = self._parse_title(title, link, pattern)
            if item:
                self._items.append(item)

        self._items.sort(key=lambda x: x.get("date") or datetime.min, reverse=True)
        print(f"[INFO] 找到 {len(self._items)} 个下载链接")
        return self._items

    def _parse_title(
        self, title: str, link: str, pattern: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        if not pattern:
            return None

        match = re.search(pattern, title)
        if not match:
            return {"title": title, "link": link, "date": None, "date_str": None}

        if self.data_type == "daily":
            date_str = match.group(1)
            date = self._parse_date(date_str, "%Y%m%d")
            return {"title": title, "link": link, "date": date, "date_str": date_str}

        elif self.data_type == "weekly":
            start_str, end_str = match.group(1), match.group(2)
            date = self._parse_date(end_str, "%Y%m%d")
            return {
                "title": title,
                "link": link,
                "date": date,
                "date_str": end_str,
                "period_str": f"{start_str}~{end_str}",
            }

        elif self.data_type == "monthly":
            date_str = match.group(1)
            date = self._parse_date(date_str, "%Y%m")
            return {"title": title, "link": link, "date": date, "date_str": date_str}

        elif self.data_type == "full":
            date_str = match.group(1)
            date = self._parse_date(date_str, "%Y%m%d")
            return {"title": title, "link": link, "date": date, "date_str": date_str}

        return None

    def _parse_date(self, date_str: str, fmt: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------------
    # 列表显示
    # ------------------------------------------------------------------------
    def list_available(self) -> None:
        type_names = {
            "daily": "日度",
            "weekly": "周度",
            "monthly": "月度",
            "full": "全量",
        }
        type_name = type_names.get(self.data_type, "未知")

        print(f"\n可用的下载{type_name}数据:")
        if not self._items:
            print("  无可用数据")
        else:
            for item in self._items:
                if item.get("date"):
                    if self.data_type == "weekly":
                        print(f"  {item['period_str']} [{type_name}] - {item['title']}")
                    elif self.data_type == "monthly":
                        print(
                            f"  {item['date'].strftime('%Y-%m')} [{type_name}] - {item['title']}"
                        )
                    else:
                        print(
                            f"  {item['date'].strftime('%Y-%m-%d')} [{type_name}] - {item['title']}"
                        )
                else:
                    print(f"  未知 - {item['title']}")
        print()

    # ------------------------------------------------------------------------
    # 下载功能
    # ------------------------------------------------------------------------
    def download_zip(self, url: str, timeout: int = 600) -> bytes:
        """下载 ZIP 文件（流式下载，显示进度和网速）"""
        import time
        from tqdm import tqdm

        print(f"[INFO] 正在下载: {url}")

        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        chunks: List[bytes] = []
        downloaded = 0
        start_time = time.time()

        with tqdm(total=total_size, unit="B", unit_scale=True, desc="下载进度") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    chunks.append(chunk)
                    downloaded += len(chunk)
                    pbar.update(len(chunk))

        elapsed = time.time() - start_time
        avg_speed = downloaded / elapsed / (1024 * 1024) if elapsed > 0 else 0
        print(
            f"[完成] {downloaded / (1024 * 1024):.1f} MB, 耗时 {elapsed:.1f}s, 平均 {avg_speed:.2f} MB/s"
        )

        return b"".join(chunks)

    # ------------------------------------------------------------------------
    # 解压功能
    # ------------------------------------------------------------------------
    def extract_to_dataframes(self, zip_content: bytes) -> List[pd.DataFrame]:
        """解压 ZIP 文件并返回 DataFrame 列表"""
        import time
        from tqdm import tqdm

        all_dfs: List[pd.DataFrame] = []

        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            file_list = zf.namelist()
            total_size = sum(info.file_size for info in zf.infolist())

            print(f"[解压] 共 {len(file_list)} 个文件")

            start_time = time.time()

            with tqdm(
                total=total_size, unit="B", unit_scale=True, desc="解压进度"
            ) as pbar:
                for file_name in file_list:
                    info = zf.getinfo(file_name)
                    df = self._process_zip_entry(zf, file_name)
                    if df is not None and not df.empty:
                        all_dfs.append(df)
                    pbar.update(info.file_size)

            elapsed = time.time() - start_time
            print(f"[解压完成] 耗时 {elapsed:.1f}s")

        return all_dfs

    def _process_zip_entry(
        self, zf: zipfile.ZipFile, file_name: str
    ) -> Optional[pd.DataFrame]:
        if file_name.endswith(".zip"):
            nested_content = zf.read(file_name)
            return self._extract_nested_zip(nested_content, file_name)
        elif file_name.endswith(".xml"):
            xml_content = zf.read(file_name)
            return self._convert_xml(xml_content, file_name)
        elif file_name.endswith((".xls", ".xlsx")):
            excel_content = zf.read(file_name)
            return self._convert_excel(excel_content)
        return None

    def _extract_nested_zip(
        self, zip_content: bytes, parent_name: str = ""
    ) -> Optional[pd.DataFrame]:
        dfs: List[pd.DataFrame] = []

        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            file_list = [
                f for f in zf.namelist() if f.endswith((".xml", ".xls", ".xlsx"))
            ]

            for file_name in file_list:
                if file_name.endswith(".xml"):
                    xml_content = zf.read(file_name)
                    df = self._convert_xml(xml_content, file_name)
                    if df is not None and not df.empty:
                        dfs.append(df)
                elif file_name.endswith((".xls", ".xlsx")):
                    excel_content = zf.read(file_name)
                    df = self._convert_excel(excel_content)
                    if df is not None and not df.empty:
                        dfs.append(df)

        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return None

    # ------------------------------------------------------------------------
    # 流式处理（内存优化 + 并行加速）
    # ------------------------------------------------------------------------
    def extract_and_save_streaming(
        self, zip_content: bytes, identifier: str, max_workers: int = 2
    ) -> Optional[str]:
        """流式解压 ZIP 并直接写入文件（内存优化 + 并行加速）"""
        import time
        from tqdm import tqdm

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"udid_{self.data_type}_{identifier}_{timestamp}.csv"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        total_records = 0
        start_time = time.time()

        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            file_list = zf.namelist()
            total_size = sum(info.file_size for info in zf.infolist())
            total_size_mb = total_size / (1024 * 1024)

            print(
                f"\n[流式处理] 共 {len(file_list)} 个文件，总大小 {total_size_mb:.1f} MB"
            )
            print(f"[并行度] {max_workers} 个工作进程")
            print(f"[输出文件] {filepath}")

            # 分类文件
            xml_files = []
            other_files = []
            for file_name in file_list:
                if file_name.endswith(".xml"):
                    xml_files.append(file_name)
                elif file_name.endswith((".zip", ".xls", ".xlsx")):
                    other_files.append(file_name)

            print(f"[文件分布] XML: {len(xml_files)}, 其他: {len(other_files)}")

            file_exists = False
            error_count = 0

            with tqdm(
                total=total_size, unit="B", unit_scale=True, desc="处理进度"
            ) as pbar:
                # 并行处理 XML 文件
                if xml_files:
                    # 先读取所有XML内容
                    xml_tasks = []
                    for file_name in xml_files:
                        info = zf.getinfo(file_name)
                        xml_content = zf.read(file_name)
                        xml_tasks.append((file_name, xml_content, info.file_size))

                    # 多进程并行解析
                    with ProcessPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(_parse_xml_worker, task[1]): task
                            for task in xml_tasks
                        }

                        for future in as_completed(futures):
                            task = futures[future]
                            file_name, xml_content, file_size = task

                            try:
                                df = future.result()
                                if df is not None and not df.empty:
                                    df.to_csv(
                                        filepath,
                                        mode="a",
                                        header=not file_exists,
                                        index=False,
                                        encoding="utf-8",
                                    )
                                    file_exists = True
                                    total_records += len(df)
                                    del df
                            except Exception:
                                error_count += 1

                            pbar.update(file_size)
                            gc.collect()

                # 顺序处理其他文件
                for file_name in other_files:
                    info = zf.getinfo(file_name)
                    df = None

                    if file_name.endswith(".zip"):
                        nested_content = zf.read(file_name)
                        df = self._extract_nested_zip(nested_content, file_name)
                    elif file_name.endswith((".xls", ".xlsx")):
                        excel_content = zf.read(file_name)
                        df = self._convert_excel(excel_content)

                    if df is not None and not df.empty:
                        df.to_csv(
                            filepath,
                            mode="a",
                            header=not file_exists,
                            index=False,
                            encoding="utf-8",
                        )
                        file_exists = True
                        total_records += len(df)
                        del df

                    pbar.update(info.file_size)
                    gc.collect()

            elapsed = time.time() - start_time
            avg_speed = total_size_mb / elapsed if elapsed > 0 else 0

            print(f"\n[处理完成] 共 {total_records:,} 条记录")
            print(f"[耗时] {elapsed:.1f}s，平均速度 {avg_speed:.2f} MB/s")
            if error_count > 0:
                print(f"[警告] {error_count} 个文件解析失败")

            if total_records > 0:
                file_size = os.path.getsize(filepath)
                file_size_mb = file_size / (1024 * 1024)
                print(f"[文件大小] {file_size_mb:.1f} MB")
                print(f"[输出路径] {filepath}")
                return filepath

        return None

    # ------------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------------
    def _convert_xml(
        self, xml_content: bytes, xml_filename: str
    ) -> Optional[pd.DataFrame]:
        try:
            records = parse_xml_to_records(xml_content)
            if records:
                return records_to_dataframe(records)
        except Exception as e:
            print(f"[ERROR] XML 解析失败 ({xml_filename}): {e}")
        return None

    def _convert_excel(self, excel_content: bytes) -> Optional[pd.DataFrame]:
        try:
            return pd.read_excel(io.BytesIO(excel_content))
        except Exception as e:
            print(f"[ERROR] Excel 解析失败: {e}")
        return None

    # ------------------------------------------------------------------------
    # 数据保存
    # ------------------------------------------------------------------------
    def merge_and_save(
        self, dataframes: List[pd.DataFrame], identifier: str
    ) -> Optional[str]:
        """合并多个 DataFrame 并保存"""
        import time
        from tqdm import tqdm

        if not dataframes:
            print("[WARN] 没有数据可合并")
            return None

        total_dfs = len(dataframes)
        print(f"\n[合并] 开始合并 {total_dfs} 个数据文件...")

        start_time = time.time()

        # 分批合并
        merged_df = None
        batch_size = max(1, total_dfs // 20)

        for i in tqdm(range(0, total_dfs, batch_size), desc="合并进度"):
            batch = dataframes[i : i + batch_size]
            if merged_df is None:
                merged_df = pd.concat(batch, ignore_index=True)
            else:
                merged_df = pd.concat([merged_df] + batch, ignore_index=True)

        # 排序（带进度）
        if merged_df is not None and "deviceRecordKey" in merged_df.columns:
            total_records = len(merged_df)
            print(f"\n[排序] 按 deviceRecordKey 排序 {total_records:,} 条记录...")
            with tqdm(
                total=100, desc="排序进度", bar_format="{l_bar}{bar}| {n_fmt}%"
            ) as pbar:
                # 排序是原子操作，分阶段显示进度
                pbar.update(10)
                merged_df = merged_df.sort_values("deviceRecordKey")
                pbar.update(90)

        elapsed = time.time() - start_time
        total_records = len(merged_df) if merged_df is not None else 0
        print(f"[合并完成] 共 {total_records:,} 条记录，耗时 {elapsed:.1f}s")

        if merged_df is None:
            return None

        if is_database_enabled():
            if self._save_to_db(merged_df, identifier):
                return None

        return self._save_to_file(merged_df, identifier)

    def _save_to_db(self, df: pd.DataFrame, identifier: str) -> bool:
        source_info = {
            "date": identifier,
            "source_file": f"{self.data_type}_merged",
            "source_type": self.data_type,
            "zip_file": "",
        }

        print(f"[DB] 准备写入 {len(df)} 条记录到 {get_db_type()} 数据库...")
        success = save_to_database(df, source_info)

        if success:
            print("[DB] 写入完成，不保存本地文件")
        else:
            print("[DB] 写入失败，将保存到本地文件")

        return success

    def _save_to_file(self, df: pd.DataFrame, identifier: str) -> str:
        """保存数据到本地文件（带进度条）"""
        import time
        from tqdm import tqdm

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        total_records = len(df)
        print(f"\n[保存] 写入 {total_records:,} 条记录...")

        start_time = time.time()

        if self.output_format == "excel":
            filename = f"udid_{self.data_type}_{identifier}_{timestamp}.xlsx"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            print(f"[保存] 格式: Excel, 文件: {filename}")

            # Excel写入进度
            with tqdm(
                total=100, desc="写入进度", bar_format="{l_bar}{bar}| {n_fmt}%"
            ) as pbar:
                pbar.update(20)
                df.to_excel(filepath, index=False, engine="openpyxl")
                pbar.update(80)
        else:
            filename = f"udid_{self.data_type}_{identifier}_{timestamp}.csv"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            print(f"[保存] 格式: CSV, 文件: {filename}")

            # CSV分块写入进度
            chunk_size = max(1, total_records // 100)
            chunks = range(0, total_records, chunk_size)

            with tqdm(total=total_records, desc="写入进度", unit="行") as pbar:
                first_chunk = True
                for i in chunks:
                    chunk_df = df.iloc[i : i + chunk_size]
                    chunk_df.to_csv(
                        filepath,
                        mode="a",
                        header=first_chunk,
                        index=False,
                        encoding="utf-8",
                    )
                    first_chunk = False
                    pbar.update(len(chunk_df))

        elapsed = time.time() - start_time

        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        print(f"[保存完成] 文件大小: {file_size_mb:.1f} MB, 耗时: {elapsed:.1f}s")
        print(f"[输出路径] {filepath}")

        if self._on_data_callback:
            try:
                self._on_data_callback(df)
            except Exception:
                pass

        return filepath

    # ------------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------------
    def find_by_date(self, date_str: str) -> Optional[Dict[str, Any]]:
        for item in self._items:
            if item.get("date_str") == date_str:
                return item
        return None

    def download_single(self, item: Dict[str, Any]) -> Optional[str]:
        print(f"\n[INFO] 选择文件: {item['title']}")

        zip_content = self.download_zip(item["link"])
        identifier = item.get("period_str") or item.get("date_str") or "unknown"

        # 全量数据使用流式处理
        if self.data_type == "full":
            print("[INFO] 全量数据，使用流式处理（内存优化 + 并行模式）")
            return self.extract_and_save_streaming(zip_content, identifier)

        dfs = self.extract_to_dataframes(zip_content)
        if dfs:
            return self.merge_and_save(dfs, identifier)

        return None

    def download_latest(self) -> Optional[str]:
        if not self._items:
            print("[ERROR] 没有可下载的数据")
            return None

        latest = self._items[0]
        print(f"\n[INFO] 正在下载最新数据: {latest.get('date_str', '未知')}")
        return self.download_single(latest)

    def download_all(self) -> List[str]:
        if not self._items:
            print("[ERROR] 没有可下载的数据")
            return []

        all_dfs: List[pd.DataFrame] = []
        min_identifier: Optional[str] = None
        max_identifier: Optional[str] = None
        saved_files: List[str] = []

        for item in self._items:
            if not item.get("date_str"):
                continue

            print(f"\n[INFO] 正在处理: {item.get('date_str')}...")

            try:
                zip_content = self.download_zip(item["link"])
                dfs = self.extract_to_dataframes(zip_content)
                all_dfs.extend(dfs)

                date_str = item.get("date_str")
                if date_str:
                    if min_identifier is None or date_str < min_identifier:
                        min_identifier = date_str
                    if max_identifier is None or date_str > max_identifier:
                        max_identifier = date_str

            except Exception as e:
                print(f"[ERROR] 下载失败: {e}")

        if all_dfs:
            if self.data_type == "weekly" and min_identifier and max_identifier:
                identifier = f"{min_identifier}~{max_identifier}"
            else:
                identifier = min_identifier or "all"

            filepath = self.merge_and_save(all_dfs, identifier)
            if filepath:
                saved_files.append(filepath)

        return saved_files


# ============================================================================
# 工具函数
# ============================================================================
def setup_encoding() -> None:
    """设置控制台编码（解决 Windows 中文乱码问题）"""
    import sys

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def ensure_download_dir() -> None:
    """确保下载目录存在"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def print_completion() -> None:
    """打印完成信息"""
    print(f"\n[DONE] 完成！文件已保存到: {DOWNLOAD_DIR}")
