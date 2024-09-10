import folium
from folium.features import GeoJsonTooltip
import pandas as pd
import numpy as np
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium


def add_choropleth(my_map, df_map: pd.DataFrame, col_name: str, fill_color: str, bins: list[float]):
    folium.Choropleth(
        geo_data=df_map,
        data=df_map,  # GeoPandasデータフレームをそのまま使用
        columns=["NAME", col_name],
        key_on="feature.properties.NAME",  # GeoJSON内のプロパティ名
        fill_color=fill_color,                            # 色を指定
        nan_fill_color='darkgray',                    # データがない区域の色を指定
        fill_opacity=0.8,
        nan_fill_opacity=0.8,
        line_opacity=0.2,
        # legend_name='高校生数',
        name=col_name,
        bins=bins,  # 色分けの閾値を指定
        show=False
    ).add_to(my_map)


def arrange() -> pd.DataFrame:
    PREF_DICT = {11: ["saitama", "埼玉県"], 12: ["chiba", "千葉県"], 13: ["tokyo", "東京都"], 14: ["kanagawa", "神奈川県"]}
    # シェープファイル読み込み
    df_shape = []
    for key, value in PREF_DICT.items():
        df = gpd.read_file(f"./shape/{key}_{value[0]}/r2ka{key}.shx")
        df_shape.append(df)

    df_shape = pd.concat(df_shape)
    # シェア率データ読み込み
    df_share = []
    for key, value in PREF_DICT.items():
        df = pd.read_excel("./シェア率.xlsx", sheet_name=value[1], dtype={0: str, 1: str, 2: str, 3: str})
        df_share.append(df)

    df_share = pd.concat(df_share)
    df_shape["MY_CODE"] = df_shape["PREF"] + df_shape["CITY"] + df_shape["S_AREA"]
    df_shape["S_NAME"] = df_shape["S_NAME"].fillna("")
    df_shape["NAME"] = df_shape["PREF_NAME"] + df_shape["CITY_NAME"] + df_shape["S_NAME"]

    df_share["大字・町名"] = df_share["大字・町名"].fillna("")
    df_share["字・丁目名"] = df_share["字・丁目名"].fillna("")
    df_share["NAME"] = df_share['都道府県名'] + df_share['市区町村名'] + df_share['大字・町名'] + df_share['字・丁目名']

    # df_map = pd.merge(df_shape, df_share, on="MY_CODE", how="left")
    df_map = pd.merge(df_shape, df_share, on="NAME", how="left")
    df_map["S_NAME"] = df_map["S_NAME"].fillna("")
    # df_map["NAME"] = df_map["PREF_NAME"] + df_map["CITY_NAME"] + df_map["S_NAME"]

    parent_list = df_map.loc[~(df_map["S_NAME"].isnull()), "CITY_NAME"].unique()
    df_map.loc[(df_map["CITY_NAME"].isin(parent_list)) & (df_map["S_NAME"] == ""), "高校生数"] = np.nan
    df_map.loc[(df_map["CITY_NAME"].isin(parent_list)) & (df_map["S_NAME"] == ""), "HS生徒数"] = 0
    df_map.loc[(df_map["CITY_NAME"].isin(parent_list)) & (df_map["S_NAME"] == ""), "HSシェア率"] = np.nan

    df_map = df_map[~df_map["NAME"].isnull()]
    df_map = df_map[(df_map["PREF"] == "13") & (df_map["CITY_NAME"].str.contains("区"))]
    return df_map


df_map = arrange()
map_center = [35.686086, 139.760256]  # 千代田区
my_map = folium.Map(location=map_center, tiles='openstreetmap', zoom_start=13)


num_student = "高校生数"
ave_age = "平均年齢"

placeholder = st.empty()
map_col, menu_col = placeholder.columns([5, 2])

with menu_col:
    # カスタムCSSを追加してラベルの折り返しを防ぐ
    st.markdown("""
    <style>
    .stMarkdown h2 {
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("分割設定")
    division = st.number_input(
        label='分割数',
        value=9,
        min_value=4,
        max_value=100,
        key="division"
    )
    st.header("閾値設定")
    thresholds = []
    for i in range(st.session_state["division"]):
        if i == 0:
            threshold = df_map[num_student].min()
        elif i == st.session_state["division"] - 1:
            threshold = df_map[num_student].max()
        else:
            threshold = st.number_input(
                f"閾値_{i}", min_value=0, max_value=1000, value=i)
        thresholds.append(threshold)

    # Thresholdリストを表示
    st.write("最小値:", df_map[num_student].min())
    st.write("最大値:", df_map[num_student].max())

with map_col:
    if st.button("マップ生成"):
        map_center = [35.686086, 139.760256]  # 千代田区
        my_map = folium.Map(location=map_center, tiles='openstreetmap', zoom_start=13)
        df_map_tmp = df_map[(df_map["PREF"] == "13") & (df_map["CITY_NAME"].str.contains("区"))]  # 東京23区

        add_choropleth(my_map, df_map, num_student, "BuGn", thresholds)
        add_choropleth(my_map, df_map, ave_age, "RdPu", [0, 30, 35, 40, 45, 50, 55, 70])
        folium.GeoJson(
            df_map,
            style_function=lambda x: {'fillColor': '#ffffff00', 'color': '#ffffff00'},
            tooltip=GeoJsonTooltip(
                fields=["NAME", "高校生数", "平均年齢"],  # ツールチップに表示するフィールド名
                aliases=["地域名: ", "高校生数: ", "平均年齢: ",],  # フィールド名の別名
                localize=True,  # データをローカライズするか（数値フォーマットなど）
                sticky=False,  # マウスが動いてもツールチップを表示し続けるか
                labels=True,  # ラベルを表示するか
                style=("background-color: white; color: black; font-weight: bold; padding: 5px; z-index: 1000")
            ),
            name="tooltip",
            show=True
        ).add_to(my_map)

        folium.LayerControl().add_to(my_map)

        st_folium(my_map, use_container_width=True, height=720, returned_objects=[])
