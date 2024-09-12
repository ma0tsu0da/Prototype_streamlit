import folium
from folium.features import GeoJsonTooltip
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="マッピング プロトタイプ",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

map_center = [35.686086, 139.760256]  # 千代田区


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


def create_map(my_map: folium.Map, df_map: pd.DataFrame, col_name: str, fill_color: str, bins: list[float]):
    add_choropleth(my_map, df_map, col_name, fill_color, bins)
    folium.GeoJson(
        df_map,
        style_function=lambda x: {'fillColor': '#ffffff00', 'color': '#ffffff00'},
        tooltip=GeoJsonTooltip(
            fields=["NAME", f"{col_name}"],  # ツールチップに表示するフィールド名
            aliases=["地域名: ", f"{col_name}: "],  # フィールド名の別名
            localize=True,  # データをローカライズするか（数値フォーマットなど）
            sticky=False,  # マウスが動いてもツールチップを表示し続けるか
            labels=True,  # ラベルを表示するか
            style=("background-color: white; color: black; font-weight: bold; padding: 5px; z-index: 1000")
        ),
        name="tooltip",
        show=True
    ).add_to(my_map)
    folium.LayerControl().add_to(my_map)


df_map = pd.read_csv('./public_tokyo23.csv')
df_map['geometry'] = df_map['geometry'].apply(wkt.loads)
df_map = gpd.GeoDataFrame(df_map, geometry='geometry')
df_map = df_map.set_crs(epsg=4612, inplace=True)


# placeholder_1 = st.empty()
# map_col_1, menu_col_1 = placeholder_1.columns([5, 2])
# placeholder_2 = st.empty()
# map_col_2, menu_col_2 = placeholder_2.columns([5, 2])

with st.container():
    map_col_1, menu_col_1 = st.columns([5, 2])

    with menu_col_1:
        # カスタムCSSを追加してラベルの折り返しを防ぐ
        st.markdown("""
        <style>
        .stMarkdown h2 {
            white-space: nowrap;
        }
        </style>
        """, unsafe_allow_html=True)

        st.header("マップ1 分割設定")
        division = st.number_input(
            label='分割数',
            value=9,
            min_value=4,
            max_value=100,
            key="division_1"
        )
        st.header("マップ1 閾値設定")
        thresholds_1 = []
        for i in range(st.session_state["division_1"]):
            if i == 0:
                threshold_1 = int(np.floor(df_map["高校生数"].min()))
            elif i == st.session_state["division_1"] - 1:
                threshold_1 = int(np.ceil(df_map["高校生数"].max()))
            else:
                threshold_1 = st.number_input(
                    f"閾値_{i}", min_value=0, max_value=1000, value=i * 25)
            thresholds_1.append(threshold_1)

        # Thresholdリストを表示
        st.write("最小値:", df_map["高校生数"].min())
        st.write("最大値:", df_map["高校生数"].max())

    with map_col_1:
        # def create_map(my_map: folium.Map):
        #    add_choropleth(my_map, df_map, num_student, "BuGn", thresholds)
        #    add_choropleth(my_map, df_map, ave_age, "RdPu", [0, 30, 35, 40, 45, 50, 55, 70])
        #    folium.GeoJson(
        #        df_map,
        #        style_function=lambda x: {'fillColor': '#ffffff00', 'color': '#ffffff00'},
        #        tooltip=GeoJsonTooltip(
        #            fields=["NAME", "高校生数", "平均年齢"],  # ツールチップに表示するフィールド名
        #            aliases=["地域名: ", "高校生数: ", "平均年齢: ",],  # フィールド名の別名
        #            localize=True,  # データをローカライズするか（数値フォーマットなど）
        #            sticky=False,  # マウスが動いてもツールチップを表示し続けるか
        #            labels=True,  # ラベルを表示するか
        #            style=("background-color: white; color: black; font-weight: bold; padding: 5px; z-index: 1000")
        #        ),
        #        name="tooltip",
        #        show=True
        #    ).add_to(my_map)
        #    folium.LayerControl().add_to(my_map)

        # ボタンの状態を session_state で管理
        if 'show_map1' not in st.session_state:
            st.session_state['show_map1'] = False

        # ボタン1が押された場合
        if st.button("マップ1生成", key="button_1"):
            st.session_state['show_map1'] = not st.session_state['show_map1']

        if st.session_state['show_map1'] & st.session_state["division_1"]:
            st.write("マップ1")
            my_map_1 = folium.Map(location=map_center, tiles='openstreetmap', zoom_start=13)
            create_map(my_map_1, df_map, "高校生数", "BuGn", thresholds_1)
            st_folium(my_map_1, use_container_width=True, width=500, returned_objects=[])


with st.container():
    map_col_2, menu_col_2 = st.columns([5, 2])

    with menu_col_2:
        # カスタムCSSを追加してラベルの折り返しを防ぐ
        st.markdown("""
        <style>
        .stMarkdown h2 {
            white-space: nowrap;
        }
        </style>
        """, unsafe_allow_html=True)

        st.header("マップ2 分割設定")
        division = st.number_input(
            label='分割数',
            value=9,
            min_value=4,
            max_value=100,
            key="division_2"
        )
        st.header("マップ2 閾値設定")
        thresholds_2 = []
        for i in range(st.session_state["division_2"]):
            if i == 0:
                threshold_2 = int(np.floor(df_map["平均年齢"].min()))
            elif i == st.session_state["division_2"] - 1:
                threshold_2 = int(np.ceil(df_map["平均年齢"].max()))
            else:
                threshold_2 = st.number_input(
                    f"閾値_{i}", min_value=0, max_value=100, value=15 + i * 7)
            thresholds_2.append(threshold_2)

        # Thresholdリストを表示
        st.write("最小値:", df_map["平均年齢"].min())
        st.write("最大値:", df_map["平均年齢"].max())

    with map_col_2:
        if 'show_map2' not in st.session_state:
            st.session_state['show_map2'] = False

        # ボタン2が押された場合
        if st.button("マップ2生成", key="button_2"):
            st.session_state['show_map2'] = not st.session_state['show_map2']

        if st.session_state['show_map2'] & st.session_state["division_2"]:
            st.write("マップ2")
            my_map_2 = folium.Map(location=map_center, tiles='openstreetmap', zoom_start=13)
            create_map(my_map_2, df_map, "平均年齢", "RdPu", thresholds_2)
            st_folium(my_map_2, use_container_width=True, width=500, returned_objects=[])


with st.container():
    map_col_3, menu_col_3 = st.columns([5, 2])
    with menu_col_3:
        filter_value = st.selectbox('フィルタリングする要素の選択',
                                    ['すべて'] + list(df_map['CITY_NAME'].unique()), key='filter_1')
    with map_col_3:
        if filter_value == 'すべて':
            target = df_map.copy()
        else:
            target = df_map[df_map['CITY_NAME'] == filter_value]
        target.rename({'S_NAME': '丁名'}, axis=1, inplace=True)
        target = target[['S_NAME', '高校生数'
                         ]].dropna(subset='高校生数'
                                   ).sort_values('高校生数', ascending=False
                                                 ).reset_index(drop=True)
        st.dataframe(target, use_container_width=True)
        st.write(f"{filter_value}の丁別高校生数")


with st.container():
    map_col_4, menu_col_4 = st.columns([5, 2])
    with menu_col_4:
        filter_value = st.selectbox('フィルタリングする要素の選択',
                                    ['すべて'] + list(df_map['CITY_NAME'].unique()), key='filter_2')
    with map_col_4:
        if filter_value == 'すべて':
            target = df_map.copy()
        else:
            target = df_map[df_map['CITY_NAME'] == filter_value]
        target.rename({'S_NAME': '丁名'}, axis=1, inplace=True)
        target = target[['S_NAME', '平均年齢'
                         ]].dropna(subset='平均年齢'
                                   ).sort_values('平均年齢', ascending=True
                                                 ).reset_index(drop=True)
        st.dataframe(target, use_container_width=True)
        st.write(f"{filter_value}の丁別平均年齢")
