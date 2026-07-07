from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/yangguang/Desktop/PKU-RA")
DASHBOARD_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DASHBOARD_DIR))
from prepare_map_layers import load_map_layers
from prepare_port_groups import build_port_groups
from prepare_policy_layers import load_policy_layers, port_city_labels
WORKBOOK = ROOT / "outputs/port_city_yearbook_merged_panel_three_stage_supersbm.xlsx"
REF_TABLE = ROOT / "outputs/port_city_did_reference_table.csv"
SHEET = "port_city_merged"
PORT_COORD_FALLBACKS = {
    "上海港": (31.2304, 121.4737),
    "天津港": (38.984, 117.727),
    "洋浦港": (19.752, 109.185),
    "八所港": (19.095, 108.632),
}
TEMPLATE = DASHBOARD_DIR / "index.template.html"
OUTPUT = ROOT / "outputs/gpe_methods_dashboard.html"
PAGES_OUTPUT = DASHBOARD_DIR / "index.html"

MAIN_ORDINARY = "GPE_3stage4_CRS_covid"
MAIN_SUPER = "GPE_3stage4_SuperSBM_CRS_covid"

METHODS = [
    {
        "id": "raw_crs",
        "column": "GPE_raw_CRS_4input",
        "label": "原始 SBM · 四投入 CRS",
        "short": "RAW4-C",
        "family": "raw",
        "familyLabel": "原始 SBM",
        "color": "#3F6B8A",
        "note": "四投入、未经 Stage 2 环境调整的 CRS 基准。",
    },
    {
        "id": "raw_vrs",
        "column": "GPE_raw_VRS_4input",
        "label": "原始 SBM · 四投入 VRS",
        "short": "RAW4-V",
        "family": "raw",
        "familyLabel": "原始 SBM",
        "color": "#6B8DA6",
        "note": "四投入、未经 Stage 2 环境调整的 VRS 基准。",
    },
    {
        "id": "raw_crs_2in",
        "column": "GPE_raw_CRS_2input",
        "label": "原始 SBM · 两投入 CRS",
        "short": "RAW2-C",
        "family": "raw",
        "familyLabel": "原始 SBM",
        "color": "#94AFC4",
        "note": "两投入、未经 Stage 2 环境调整的 CRS 稳健性口径。",
    },
    {
        "id": "raw_vrs_2in",
        "column": "GPE_raw_VRS_2input",
        "label": "原始 SBM · 两投入 VRS",
        "short": "RAW2-V",
        "family": "raw",
        "familyLabel": "原始 SBM",
        "color": "#B8C9D6",
        "note": "两投入、未经 Stage 2 环境调整的 VRS 稳健性口径。",
    },
    {
        "id": "stage_base_crs",
        "column": "GPE_3stage4_CRS_base",
        "label": "三阶段 SBM · 四投入基准 CRS",
        "short": "3S4-B-C",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#087E72",
        "note": "四投入、不含疫情暴露项的 SFA 环境调整，CRS。",
    },
    {
        "id": "stage_covid_crs",
        "column": MAIN_ORDINARY,
        "label": "三阶段 SBM · 四投入疫情调整 CRS",
        "short": "3S4-C-C",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#075E59",
        "note": "四投入、含疫情暴露项的三阶段 SBM；当前普通 SBM 主结果。",
        "isMain": True,
    },
    {
        "id": "stage_covid_vrs",
        "column": "GPE_3stage4_VRS_covid",
        "label": "三阶段 SBM · 四投入疫情调整 VRS",
        "short": "3S4-C-V",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#5AB7A8",
        "note": "四投入、含疫情暴露项的三阶段 SBM，VRS。",
    },
    {
        "id": "stage_base_crs_2in",
        "column": "GPE_3stage_CRS_base",
        "label": "三阶段 SBM · 两投入基准 CRS",
        "short": "3S2-B-C",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#36A092",
        "note": "两投入、不含疫情暴露项的 SFA 环境调整，CRS。",
    },
    {
        "id": "stage_covid_crs_2in",
        "column": "GPE_3stage_CRS_covid",
        "label": "三阶段 SBM · 两投入疫情调整 CRS",
        "short": "3S2-C-C",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#4DB8A8",
        "note": "两投入、含疫情暴露项的三阶段 SBM 稳健性口径。",
    },
    {
        "id": "stage_covid_vrs_2in",
        "column": "GPE_3stage_VRS_covid",
        "label": "三阶段 SBM · 两投入疫情调整 VRS",
        "short": "3S2-C-V",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#7CCBBE",
        "note": "两投入、含疫情暴露项的三阶段 SBM，VRS。",
    },
    {
        "id": "stage_base_vrs_2in",
        "column": "GPE_3stage_VRS_base",
        "label": "三阶段 SBM · 两投入基准 VRS",
        "short": "3S2-B-V",
        "family": "stage",
        "familyLabel": "三阶段 SBM",
        "color": "#8FD4C9",
        "note": "两投入、不含疫情暴露项的 SFA 环境调整，VRS。",
    },
    {
        "id": "super_covid_crs",
        "column": MAIN_SUPER,
        "label": "三阶段 Super-SBM · 四投入疫情调整 CRS",
        "short": "SS4-C-C",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#D06645",
        "note": "四投入、在疫情调整 CRS 结果上区分效率前沿观测；当前 Super-SBM 主结果。",
        "isMain": True,
    },
    {
        "id": "super_covid_vrs",
        "column": "GPE_3stage4_SuperSBM_VRS_covid",
        "label": "三阶段 Super-SBM · 四投入疫情调整 VRS",
        "short": "SS4-C-V",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#E08B68",
        "note": "四投入、在疫情调整 VRS 结果上区分效率前沿观测。",
    },
    {
        "id": "super_base_crs",
        "column": "GPE_3stage4_SuperSBM_CRS_base",
        "label": "三阶段 Super-SBM · 四投入基准 CRS",
        "short": "SS4-B-C",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#B64D32",
        "note": "四投入、不含疫情项的三阶段 Super-SBM，CRS。",
    },
    {
        "id": "super_raw_crs",
        "column": "GPE_raw_SuperSBM_CRS_4input",
        "label": "原始 Super-SBM · 四投入 CRS",
        "short": "SS4-RAW",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#F0A17F",
        "note": "四投入、未经 Stage 2 调整的 Super-SBM，CRS。",
    },
    {
        "id": "super_covid_crs_2in",
        "column": "GPE_3stage_SuperSBM_CRS_covid",
        "label": "三阶段 Super-SBM · 两投入疫情调整 CRS",
        "short": "SS2-C-C",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#E6A088",
        "note": "两投入、在疫情调整 CRS 结果上区分效率前沿观测的稳健性口径。",
    },
    {
        "id": "super_covid_vrs_2in",
        "column": "GPE_3stage_SuperSBM_VRS_covid",
        "label": "三阶段 Super-SBM · 两投入疫情调整 VRS",
        "short": "SS2-C-V",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#EFB8A3",
        "note": "两投入、在疫情调整 VRS 结果上区分效率前沿观测。",
    },
    {
        "id": "super_base_crs_2in",
        "column": "GPE_3stage_SuperSBM_CRS_base",
        "label": "三阶段 Super-SBM · 两投入基准 CRS",
        "short": "SS2-B-C",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#C9785E",
        "note": "两投入、不含疫情项的三阶段 Super-SBM，CRS。",
    },
    {
        "id": "super_raw_crs_2in",
        "column": "GPE_raw_SuperSBM_CRS_2input",
        "label": "原始 Super-SBM · 两投入 CRS",
        "short": "SS2-RAW",
        "family": "super",
        "familyLabel": "Super-SBM",
        "color": "#F5C4AE",
        "note": "两投入、未经 Stage 2 调整的 Super-SBM，CRS。",
    },
    {
        "id": "legacy_selected_crs",
        "column": "GPE_CRS_selected",
        "label": "历史 Selected 口径 · CRS",
        "short": "OLD-S-C",
        "family": "legacy",
        "familyLabel": "历史来源口径",
        "color": "#786B5F",
        "note": "原表保留的旧 Selected 结果；已标记 deprecated，不作为当前主结果。",
    },
    {
        "id": "legacy_selected_vrs",
        "column": "GPE_VRS_selected",
        "label": "历史 Selected 口径 · VRS",
        "short": "OLD-S-V",
        "family": "legacy",
        "familyLabel": "历史来源口径",
        "color": "#9A8B7C",
        "note": "原表保留的旧 Selected VRS 结果。",
    },
    {
        "id": "legacy_trend_crs",
        "column": "GPE_CRS_trend_selected",
        "label": "历史 Trend 口径 · CRS",
        "short": "OLD-T-C",
        "family": "legacy",
        "familyLabel": "历史来源口径",
        "color": "#665B51",
        "note": "原表保留的 Trend 来源/估算口径，CRS。",
    },
    {
        "id": "legacy_trend_vrs",
        "column": "GPE_VRS_trend_selected",
        "label": "历史 Trend 口径 · VRS",
        "short": "OLD-T-V",
        "family": "legacy",
        "familyLabel": "历史来源口径",
        "color": "#A99A89",
        "note": "原表保留的 Trend 来源/估算口径，VRS。",
    },
    {
        "id": "legacy_thc_crs",
        "column": "GPE_CRS_thc_selected",
        "label": "历史 THC 口径 · CRS",
        "short": "OLD-H-C",
        "family": "legacy",
        "familyLabel": "历史来源口径",
        "color": "#8B745F",
        "note": "原表保留的 THC 分摊来源口径，CRS。",
    },
    {
        "id": "legacy_thc_vrs",
        "column": "GPE_VRS_thc_selected",
        "label": "历史 THC 口径 · VRS",
        "short": "OLD-H-V",
        "family": "legacy",
        "familyLabel": "历史来源口径",
        "color": "#B39A81",
        "note": "原表保留的 THC 分摊来源口径，VRS。",
    },
]


def finite_or_none(value):
    if pd.isna(value):
        return None
    number = float(value)
    return number if np.isfinite(number) else None


def load_ports(df: pd.DataFrame) -> list[dict]:
    ref = pd.read_csv(REF_TABLE).set_index("主要港口")
    ports: list[dict] = []
    for port in sorted(df["主要港口"].unique()):
        row = df.loc[df["主要港口"] == port].iloc[0]
        lat = lon = np.nan
        if port in ref.index:
            lat = pd.to_numeric(ref.at[port, "lat"], errors="coerce")
            lon = pd.to_numeric(ref.at[port, "lon"], errors="coerce")
        if (pd.isna(lat) or pd.isna(lon)) and port in PORT_COORD_FALLBACKS:
            lat, lon = PORT_COORD_FALLBACKS[port]
        if pd.isna(lat) or pd.isna(lon):
            raise ValueError(f"Missing coordinates for port: {port}")
        ports.append(
            {
                "port": str(port),
                "city": str(row["所属地级市"]),
                "province": str(row["省份"]),
                "group": str(row["港口群归属"]),
                "portType": str(row["城市-港口关系"]),
                "lat": float(lat),
                "lon": float(lon),
            }
        )
    return ports


def main() -> None:
    df = pd.read_excel(WORKBOOK, sheet_name=SHEET)
    required = {
        "主要港口",
        "年份",
        "港口群归属",
        "省份",
        "所属地级市",
        "城市-港口关系",
        *(method["column"] for method in METHODS),
        "gpe_main_y",
        "gpe_main_y_source",
        "gpe_main_y_supersbm",
        "gpe_main_y_supersbm_source",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for method in METHODS:
        series = pd.to_numeric(df[method["column"]], errors="coerce")
        if series.isna().any():
            raise ValueError(f"{method['column']} contains missing or non-numeric values")

    ordinary_alias_equal = np.allclose(
        pd.to_numeric(df["gpe_main_y"]),
        pd.to_numeric(df[MAIN_ORDINARY]),
        equal_nan=True,
    )
    super_alias_equal = np.allclose(
        pd.to_numeric(df["gpe_main_y_supersbm"]),
        pd.to_numeric(df[MAIN_SUPER]),
        equal_nan=True,
    )
    if not ordinary_alias_equal or not super_alias_equal:
        raise ValueError("Main GPE aliases are not exact copies of their source columns")

    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "port": str(row["主要港口"]),
                "year": int(row["年份"]),
                "group": str(row["港口群归属"]),
                "province": str(row["省份"]),
                "city": str(row["所属地级市"]),
                "v": [finite_or_none(row[method["column"]]) for method in METHODS],
            }
        )

    ordinary = pd.to_numeric(df[MAIN_ORDINARY])
    super_sbm = pd.to_numeric(df[MAIN_SUPER])
    legacy = pd.to_numeric(df["GPE_CRS_selected"])
    base = pd.to_numeric(df["GPE_3stage4_CRS_base"])

    ports = load_ports(df)

    data = {
        "meta": {
            "sourceFile": WORKBOOK.name,
            "sourceSheet": SHEET,
            "rows": int(len(df)),
            "ports": int(df["主要港口"].nunique()),
            "yearMin": int(df["年份"].min()),
            "yearMax": int(df["年份"].max()),
            "groups": sorted(df["港口群归属"].dropna().astype(str).unique().tolist()),
            "methodCount": len(METHODS),
            "aliases": [
                {
                    "alias": "gpe_main_y",
                    "source": MAIN_ORDINARY,
                    "sourceLabel": str(df["gpe_main_y_source"].dropna().iloc[0]),
                    "equal": bool(ordinary_alias_equal),
                },
                {
                    "alias": "gpe_main_y_supersbm",
                    "source": MAIN_SUPER,
                    "sourceLabel": str(
                        df["gpe_main_y_supersbm_source"].dropna().iloc[0]
                    ),
                    "equal": bool(super_alias_equal),
                },
            ],
        },
        "methods": METHODS,
        "ports": ports,
        "portGroups": build_port_groups(ports),
        "mapLayers": load_map_layers(),
        "policyLayers": load_policy_layers(ports),
        "mapLabels": {
            "cities": port_city_labels(ports),
        },
        "records": records,
        "findings": {
            "ordinaryMean": float(ordinary.mean()),
            "superMean": float(super_sbm.mean()),
            "superAboveOne": int((super_sbm > 1 + 1e-10).sum()),
            "ordinarySuperPearson": float(ordinary.corr(super_sbm)),
            "ordinarySuperSpearman": float(ordinary.corr(super_sbm, method="spearman")),
            "ordinarySuperMae": float((ordinary - super_sbm).abs().mean()),
            "legacyMean": float(legacy.mean()),
            "legacyPremiumPct": float((legacy.mean() / ordinary.mean() - 1) * 100),
            "baseCovidMeanDifference": float(base.mean() - ordinary.mean()),
        },
    }

    template = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "__GPE_DATA__" not in template:
        raise ValueError("Template data placeholder is missing")
    html = template.replace("__GPE_DATA__", payload)
    OUTPUT.write_text(html, encoding="utf-8")
    PAGES_OUTPUT.write_text(html, encoding="utf-8")
    print(OUTPUT)
    print(PAGES_OUTPUT)


if __name__ == "__main__":
    main()
