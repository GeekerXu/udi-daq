# -*- coding: utf-8 -*-
"""
UDI XML 解析模块
================

提供 UDI 数据 XML 文件的解析功能。

功能:
    - parse_xml_to_records: 将 XML 内容解析为记录列表
    - records_to_dataframe: 将记录列表转换为 DataFrame

作者: geekerxu
版本: 3.0.0
"""

# ============================================================================
# 标准库导入
# ============================================================================
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


# ============================================================================
# XML 清理函数
# ============================================================================
def _clean_xml_content(xml_content: bytes) -> bytes:
    """
    清理 XML 内容中的非法字符

    XML 1.0 规范禁止某些控制字符（如 0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F），
    但数据源可能包含这些字符，需要在解析前移除。

    参数:
        xml_content: 原始 XML 字节内容

    返回:
        清理后的 XML 字节内容
    """
    # 先解码为字符串
    try:
        text = xml_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = xml_content.decode("gbk")
        except UnicodeDecodeError:
            text = xml_content.decode("utf-8", errors="ignore")

    # 移除 XML 1.0 禁止的控制字符（保留 \t, \n, \r）
    # 非法字符: 0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F
    illegal_chars = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
    cleaned_text = illegal_chars.sub("", text)

    # 另外处理一些常见的非法 XML 实体
    cleaned_text = cleaned_text.replace("&nbsp;", " ")
    cleaned_text = re.sub(
        r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", cleaned_text
    )

    return cleaned_text.encode("utf-8")


# ============================================================================
# XML 解析函数
# ============================================================================
def parse_xml_to_records(xml_content: bytes) -> List[Dict[str, str]]:
    """
    将 XML 内容解析为设备记录列表

    参数:
        xml_content: XML 文件的字节内容

    返回:
        包含所有设备记录的列表，每条记录是字段名到值的映射字典

    异常:
        ET.ParseError: XML 格式错误时抛出

    示例:
        >>> xml_data = b'<root><devices><device><deviceRecordKey>ABC123</deviceRecordKey></device></devices></root>'
        >>> records = parse_xml_to_records(xml_data)
        >>> print(records[0]['deviceRecordKey'])
        ABC123
    """
    # 清理 XML 内容
    cleaned_content = _clean_xml_content(xml_content)

    root = ET.fromstring(cleaned_content)
    records: List[Dict[str, str]] = []

    # 直接查找 devices 节点
    devices = root.find("devices")
    if devices is not None:
        for device in devices.findall("device"):
            record = _extract_device_record(device)
            if record:
                records.append(record)
        return records

    # 遍历子节点查找 devices（处理命名空间）
    for child in root:
        tag = _get_local_tag(child.tag)
        if tag == "devices" and len(child) > 0:
            for device in child.findall("device"):
                record = _extract_device_record(device)
                if record:
                    records.append(record)

    return records


def _extract_device_record(device_node: ET.Element) -> Optional[Dict[str, str]]:
    """
    从 device 节点提取记录

    参数:
        device_node: XML 设备节点

    返回:
        设备记录字典，如果节点为空则返回 None
    """
    record: Dict[str, str] = {}

    for child in device_node:
        tag = _get_local_tag(child.tag)
        text = child.text
        record[tag] = text.strip() if text and text.strip() else ""

    return record if record else None


def _get_local_tag(tag: str) -> str:
    """
    获取标签的本地名称（去除命名空间）

    参数:
        tag: 完整标签名

    返回:
        本地标签名
    """
    return tag.split("}")[-1] if "}" in tag else tag


# ============================================================================
# DataFrame 转换函数
# ============================================================================
def records_to_dataframe(
    records: List[Dict[str, str]],
    sort_key: str = "deviceRecordKey",
):
    """
    将记录列表转换为 pandas DataFrame

    参数:
        records: parse_xml_to_records 返回的记录列表
        sort_key: 排序字段名，默认为 deviceRecordKey

    返回:
        pandas DataFrame 对象
    """
    import pandas as pd

    df = pd.DataFrame(records)

    if not df.empty and sort_key and sort_key in df.columns:
        df = df.sort_values(sort_key)

    return df
