# -*- coding: utf-8 -*-
"""
UDI 数据库辅助模块
==================

提供 Oracle、MySQL、Hive 数据库的连接和写入功能。

功能:
    - set_db_config: 设置数据库配置
    - get_db_connection: 获取数据库连接
    - save_to_database: 保存数据到数据库
    - is_database_enabled: 检查数据库是否启用
    - get_db_type: 获取当前数据库类型

作者: geekerxu
版本: 3.0.0
"""

# ============================================================================
# 标准库导入
# ============================================================================
import os
from datetime import datetime
from typing import Any, Dict, Optional

# ============================================================================
# 第三方库导入
# ============================================================================
import pandas as pd

# ============================================================================
# 全局变量
# ============================================================================
# 从环境变量读取数据库配置
_DB_ENABLED = os.environ.get("UDI_DB_ENABLED", "").lower()
_DB_TYPE = _DB_ENABLED if _DB_ENABLED in ("oracle", "mysql", "hive") else None

# 外部传入的数据库配置
_EXTERNAL_DB_CONFIG: Optional[Dict[str, Any]] = None


# ============================================================================
# 配置函数
# ============================================================================
def set_db_config(db_type: str, config: Dict[str, Any]) -> bool:
    """
    设置数据库配置

    参数:
        db_type: 数据库类型 (oracle/mysql/hive)
        config: 配置字典，包含 host, port, service/database, user, password 等字段

    返回:
        True 如果配置有效，False 如果配置不完整

    异常:
        ValueError: 配置不完整时抛出（当 strict=True 时）
    """
    global _EXTERNAL_DB_CONFIG, _DB_ENABLED, _DB_TYPE

    allowed_types = ("oracle", "mysql", "hive")

    if db_type not in allowed_types:
        raise ValueError(f"无效的数据库类型: {db_type}")

    if not isinstance(config, dict):
        raise ValueError("配置应为字典类型")

    # 检查是否有必要的配置信息（环境变量或传入的配置）
    has_config, missing = _check_db_config_available(db_type, config)

    if not has_config:
        error_msg = f"""数据库配置不完整！

请通过环境变量设置 {db_type.upper()} 连接信息:
"""
        if db_type == "oracle":
            error_msg += """  export UDI_ORACLE_HOST=localhost
  export UDI_ORACLE_PORT=1521
  export UDI_ORACLE_SERVICE=ORCL
  export UDI_ORACLE_USER=udi_user
  export UDI_ORACLE_PASSWORD=your_password
"""
        elif db_type == "mysql":
            error_msg += """  export UDI_MYSQL_HOST=localhost
  export UDI_MYSQL_PORT=3306
  export UDI_MYSQL_DATABASE=udi_db
  export UDI_MYSQL_USER=udi_user
  export UDI_MYSQL_PASSWORD=your_password
"""
        elif db_type == "hive":
            error_msg += """  export UDI_HIVE_HOST=localhost
  export UDI_HIVE_PORT=10000
  export UDI_HIVE_DATABASE=udi_db
  export UDI_HIVE_USER=udi_user
  export UDI_HIVE_PASSWORD=your_password
"""
        raise ValueError(error_msg)

    _EXTERNAL_DB_CONFIG = {"db_type": db_type, "config": config}
    _DB_ENABLED = db_type
    _DB_TYPE = db_type

    print(f"[DB][INFO] 数据库配置已设置: {db_type}")
    return True


def _check_db_config_available(db_type: str, config: Dict[str, Any]) -> tuple:
    """
    检查数据库配置是否完整

    参数:
        db_type: 数据库类型
        config: 配置字典

    返回:
        (bool, list): (是否有足够配置, 缺少的配置项列表)
    """
    missing = []

    if db_type == "oracle":
        host = config.get("host") or os.environ.get("UDI_ORACLE_HOST")
        user = config.get("user") or os.environ.get("UDI_ORACLE_USER")
        password = config.get("password") or os.environ.get("UDI_ORACLE_PASSWORD")
        if not host:
            missing.append("UDI_ORACLE_HOST")
        if not user:
            missing.append("UDI_ORACLE_USER")
        if not password:
            missing.append("UDI_ORACLE_PASSWORD")
        return (len(missing) == 0, missing)

    elif db_type == "mysql":
        host = config.get("host") or os.environ.get("UDI_MYSQL_HOST")
        user = config.get("user") or os.environ.get("UDI_MYSQL_USER")
        password = config.get("password") or os.environ.get("UDI_MYSQL_PASSWORD")
        database = config.get("database") or os.environ.get("UDI_MYSQL_DATABASE")
        if not host:
            missing.append("UDI_MYSQL_HOST")
        if not user:
            missing.append("UDI_MYSQL_USER")
        if not password:
            missing.append("UDI_MYSQL_PASSWORD")
        if not database:
            missing.append("UDI_MYSQL_DATABASE")
        return (len(missing) == 0, missing)

    elif db_type == "hive":
        host = config.get("host") or os.environ.get("UDI_HIVE_HOST")
        database = config.get("database") or os.environ.get("UDI_HIVE_DATABASE")
        if not host:
            missing.append("UDI_HIVE_HOST")
        if not database:
            missing.append("UDI_HIVE_DATABASE")
        return (len(missing) == 0, missing)

    return (False, ["未知数据库类型"])


def is_database_enabled() -> bool:
    """
    检查数据库写入是否启用

    返回:
        True 如果数据库已启用
    """
    return _EXTERNAL_DB_CONFIG is not None or _DB_TYPE is not None


def get_db_type() -> Optional[str]:
    """
    获取当前启用的数据库类型

    返回:
        数据库类型字符串，如果未启用则返回 None
    """
    if _EXTERNAL_DB_CONFIG is not None:
        return _EXTERNAL_DB_CONFIG.get("db_type")
    return _DB_TYPE


# ============================================================================
# 连接函数
# ============================================================================
def get_db_connection():
    """
    获取数据库连接

    返回:
        数据库连接对象，如果未配置数据库则返回 None

    异常:
        ImportError: 缺少数据库驱动
        Exception: 连接失败
    """
    # 确定有效的数据库类型和配置
    if _EXTERNAL_DB_CONFIG is not None:
        db_type = _EXTERNAL_DB_CONFIG.get("db_type")
        config = _EXTERNAL_DB_CONFIG.get("config", {})
    else:
        db_type = _DB_TYPE
        config = {}

    if not db_type:
        return None

    try:
        if db_type == "oracle":
            return _connect_oracle(config)
        elif db_type == "mysql":
            return _connect_mysql(config)
        elif db_type == "hive":
            return _connect_hive(config)
    except ImportError as e:
        print(f"[DB][ERROR] 缺少数据库驱动: {e}")
        print("[DB][INFO] 请安装对应驱动:")
        print("  Oracle: pip install cx_Oracle")
        print("  MySQL:  pip install pymysql")
        print("  Hive:   pip install pyhive sasl thrift")
        raise
    except Exception as e:
        print(f"[DB][ERROR] 连接失败: {e}")
        raise

    return None


def _connect_oracle(config: Dict[str, Any]):
    """连接 Oracle 数据库"""
    import cx_Oracle

    host = config.get("host", os.environ.get("UDI_ORACLE_HOST", "localhost"))
    port = config.get("port", os.environ.get("UDI_ORACLE_PORT", "1521"))
    service = config.get("service", os.environ.get("UDI_ORACLE_SERVICE", "ORCL"))
    user = config.get("user", os.environ.get("UDI_ORACLE_USER", "udi_user"))
    password = config.get("password", os.environ.get("UDI_ORACLE_PASSWORD", ""))

    dsn = cx_Oracle.makedsn(host, int(port), service_name=service)
    conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)

    print(f"[DB][INFO] Oracle 连接成功 - {host}:{port}")
    return conn


def _connect_mysql(config: Dict[str, Any]):
    """连接 MySQL 数据库"""
    import pymysql

    host = config.get("host", os.environ.get("UDI_MYSQL_HOST", "localhost"))
    port = config.get("port", os.environ.get("UDI_MYSQL_PORT", "3306"))
    database = config.get("database", os.environ.get("UDI_MYSQL_DATABASE", "udi_db"))
    user = config.get("user", os.environ.get("UDI_MYSQL_USER", "udi_user"))
    password = config.get("password", os.environ.get("UDI_MYSQL_PASSWORD", ""))

    conn = pymysql.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password,
        charset="utf8mb4",
    )

    print(f"[DB][INFO] MySQL 连接成功 - {host}:{port}")
    return conn


def _connect_hive(config: Dict[str, Any]):
    """连接 Hive 数据库"""
    from pyhive import hive

    host = config.get("host", os.environ.get("UDI_HIVE_HOST", "localhost"))
    port = config.get("port", os.environ.get("UDI_HIVE_PORT", "10000"))
    database = config.get("database", os.environ.get("UDI_HIVE_DATABASE", "udi_db"))
    username = config.get("user", os.environ.get("UDI_HIVE_USER", "udi_user"))
    password = config.get("password", os.environ.get("UDI_HIVE_PASSWORD", ""))

    conn = hive.connect(
        host=host,
        port=int(port),
        database=database,
        username=username,
        password=password,
    )

    print(f"[DB][INFO] Hive 连接成功 - {host}:{port}")
    return conn


# ============================================================================
# 数据保存函数
# ============================================================================
def save_to_database(
    df: pd.DataFrame,
    source_info: Dict[str, Any],
    table_name: str = "udi_device_data",
) -> bool:
    """
    将 DataFrame 数据保存到数据库

    参数:
        df: 包含 UDI 数据的 DataFrame
        source_info: 源信息字典，包含 date, source_file, source_type 等字段
        table_name: 目标表名，默认为 udi_device_data

    返回:
        True 如果保存成功
    """
    if not get_db_type() or df is None or df.empty:
        return False

    # 列名映射
    column_mapping = {
        "deviceRecordKey": "device_record_key",
        "prdCode": "prd_code",
        "prdName": "prd_name",
        "orgName": "org_name",
        "orgCode": "org_code",
        "udiDI": "udi_di",
        "udiPI": "udi_pi",
        "prodDesc": "prod_desc",
        "specModel": "spec_model",
        "unit": "unit",
        "specCode": "spec_code",
        "manageClass": "manage_class",
        "deviceClass": "device_class",
        "applyScope": "apply_scope",
        "regApproval": "reg_approval",
        "expiryDate": "expiry_date",
        "storageCond": "storage_cond",
        "contactInfo": "contact_info",
        "notes": "notes",
    }

    # 重命名列
    df_renamed = df.copy()
    df_renamed.rename(columns=column_mapping, inplace=True)

    # 添加元数据列
    df_renamed["data_date"] = source_info.get("date", "")
    df_renamed["data_zip_file"] = source_info.get("zip_file", "")
    df_renamed["download_time"] = datetime.now()
    df_renamed["source_file"] = source_info.get("source_file", "")
    df_renamed["source_type"] = source_info.get("source_type", "")

    try:
        conn = get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # 构建插入 SQL
        columns = df_renamed.columns.tolist()
        placeholders = ", ".join([":" + str(i + 1) for i in range(len(columns))])
        insert_sql = (
            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        )

        # 分批写入
        batch_size = 1000
        total_rows = len(df_renamed)

        for i in range(0, total_rows, batch_size):
            batch = df_renamed.iloc[i : i + batch_size]
            records = batch.to_dict("records")

            # 处理 NaN 值
            for record in records:
                for k, v in record.items():
                    if pd.isna(v):
                        record[k] = None

            cursor.executemany(insert_sql, records)
            conn.commit()
            print(
                f"[DB][INFO] 已写入 {min(i + batch_size, total_rows)}/{total_rows} 条"
            )

        cursor.close()
        conn.close()

        print(f"[DB][INFO] 写入完成，共 {total_rows} 条记录")
        return True

    except Exception as e:
        print(f"[DB][ERROR] 写入失败: {e}")
        return False


# ============================================================================
# 建表语句
# ============================================================================
CREATE_TABLE_SQL = {
    "oracle": """
        CREATE TABLE udi_device_data (
            data_date VARCHAR2(20),
            source_file VARCHAR2(200),
            source_type VARCHAR2(20),
            device_record_key VARCHAR2(100),
            data_zip_file VARCHAR2(200),
            download_time TIMESTAMP,
            prd_code VARCHAR2(100),
            prd_name VARCHAR2(500),
            org_name VARCHAR2(500),
            org_code VARCHAR2(100),
            udi_di VARCHAR2(100),
            udi_pi VARCHAR2(200),
            prod_desc VARCHAR2(1000),
            spec_model VARCHAR2(200),
            unit VARCHAR2(50),
            spec_code VARCHAR2(100),
            manage_class VARCHAR2(50),
            device_class VARCHAR2(50),
            apply_scope VARCHAR2(500),
            reg_approval VARCHAR2(100),
            expiry_date VARCHAR2(50),
            storage_cond VARCHAR2(200),
            contact_info VARCHAR2(200),
            notes VARCHAR2(500),
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "mysql": """
        CREATE TABLE udi_device_data (
            data_date VARCHAR(20),
            source_file VARCHAR(200),
            source_type VARCHAR(20),
            device_record_key VARCHAR(100),
            data_zip_file VARCHAR(200),
            download_time TIMESTAMP,
            prd_code VARCHAR(100),
            prd_name VARCHAR(500),
            org_name VARCHAR(500),
            org_code VARCHAR(100),
            udi_di VARCHAR(100),
            udi_pi VARCHAR(200),
            prod_desc VARCHAR(1000),
            spec_model VARCHAR(200),
            unit VARCHAR(50),
            spec_code VARCHAR(100),
            manage_class VARCHAR(50),
            device_class VARCHAR(50),
            apply_scope VARCHAR(500),
            reg_approval VARCHAR(100),
            expiry_date VARCHAR(50),
            storage_cond VARCHAR(200),
            contact_info VARCHAR(200),
            notes VARCHAR(500),
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "hive": """
        CREATE TABLE IF NOT EXISTS udi_device_data (
            data_date STRING,
            source_file STRING,
            source_type STRING,
            device_record_key STRING,
            data_zip_file STRING,
            download_time TIMESTAMP,
            prd_code STRING,
            prd_name STRING,
            org_name STRING,
            org_code STRING,
            udi_di STRING,
            udi_pi STRING,
            prod_desc STRING,
            spec_model STRING,
            unit STRING,
            spec_code STRING,
            manage_class STRING,
            device_class STRING,
            apply_scope STRING,
            reg_approval STRING,
            expiry_date STRING,
            storage_cond STRING,
            contact_info STRING,
            notes STRING
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\\t'
        STORED AS TEXTFILE
    """,
}
