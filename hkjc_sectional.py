import os
import pandas as pd
from io import StringIO

def parse_csv_with_metadata(csv_filename: str):
    """
    讀取包含 metadata + 馬匹分段的 CSV。
    返回：df(馬匹表格), metadata_lines(前面的文字行)
    """
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"找不到檔案：{csv_filename}")

    with open(csv_filename, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    # 找「三、各馬匹分段與位置數據」那一行
    table_start = None
    for i, line in enumerate(lines):
        if "三、各馬匹分段與位置數據" in line:
            table_start = i + 1  # 表頭在下一行
            break

    if table_start is None:
        raise ValueError(f"{csv_filename} 中找不到『三、各馬匹分段與位置數據』這一段")

    # 取 metadata 文字（上半部）
    metadata_lines = [line.strip() for line in lines[:table_start] if line.strip()]

    # 取表格部份（從表頭行開始）
    table_lines = lines[table_start:]
    table_content = "".join(table_lines)
    df = pd.read_csv(StringIO(table_content), sep="\t")

    return df, metadata_lines


def load_race_from_csv(race_date: str, race_no: int):
    """
    從 sectional_YYYYMMDD_N.csv 讀取一場賽事的分段時間數據。
    race_date 格式：'dd/mm/yyyy' 例如 '03/12/2025'
    race_no：場次號碼 1-13
    """
    d, m, y = race_date.split("/")
    date_key = f"{y}{m}{d}"
    csv_filename = f"sectional_{date_key}_{race_no}.csv"

    df, metadata_lines = parse_csv_with_metadata(csv_filename)

    # 將 DataFrame 轉成 list[dict]
    horses = df.to_dict(orient="records")

    # 計算段數（第1段時間、第2段時間…）
    segment_count = len(
        [c for c in df.columns if c.startswith("第") and c.endswith("時間")]
    )

    return {
        "csv_filename": csv_filename,
        "metadata_lines": metadata_lines,
        "segment_count": segment_count,
        "horses": horses,
        "df": df,
    }


def load_day_races(race_date: str, max_race_no: int):
    """
    讀取同一日所有場次的 sectional_YYYYMMDD_N.csv，合併成一個 DataFrame。
    回傳：df_all, available_races, metadata_dict(每場的 metadata)
    """
    all_rows = []
    available_races = 0
    metadata_dict = {}

    for rn in range(1, max_race_no + 1):
        d, m, y = race_date.split("/")
        date_key = f"{y}{m}{d}"
        csv_filename = f"sectional_{date_key}_{rn}.csv"

        if not os.path.exists(csv_filename):
            continue

        try:
            df, metadata_lines = parse_csv_with_metadata(csv_filename)
            available_races += 1
            metadata_dict[rn] = metadata_lines

            for _, row in df.iterrows():
                row_dict = row.to_dict()
                row_dict["場次"] = rn
                all_rows.append(row_dict)

        except Exception as e:
            continue

    if not all_rows:
        raise ValueError(f"找不到 {race_date} 的任何 sectional_YYYYMMDD_N.csv 檔案")

    df_all = pd.DataFrame(all_rows)

    # 將名次轉成數字（方便排序）
    if "名次" in df_all.columns:
        df_all["名次"] = pd.to_numeric(df_all["名次"], errors="coerce")

    return df_all, available_races, metadata_dict


# ============================================================================
# ✨ 新增函數：頭馬沿途走位提取
# ============================================================================

def get_leader_walk_position(csv_filename: str):
    """
    從 CSV 中提取頭馬 (名次=1) 的沿途走位

    參數:
        csv_filename: CSV 檔案名稱 (e.g., 'sectional_20251203_1.csv')

    返回:
        str: 頭馬的沿途走位 (e.g., '3-3-1---'), 如無則返回 None
    """
    try:
        df, _ = parse_csv_with_metadata(csv_filename)

        # 找到名次=1的馬 (頭馬)
        if '名次' in df.columns and '沿途走位' in df.columns:
            leader = df[df['名次'] == 1]

            if not leader.empty:
                return leader['沿途走位'].values[0]

    except Exception as e:
        print(f"警告: 提取頭馬走位失敗 - {e}")

    return None
