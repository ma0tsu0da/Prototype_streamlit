import json
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_folium import st_folium


f = open("./geojson/N03-19_40_190101.geojson", 'r', encoding="utf-8")
fukuoka = json.load(f)
f.close()

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

    st.header("閾値設定")
    division = st.number_input(
        label='分割数',
        value=9,
        min_value=4,
        max_value=100,
        key="division"
    )

with map_col:
    if st.session_state["division"]:
        threshold = np.linspace(0, 1, st.session_state["division"]).tolist()
    # 鉄道路線データ
    rosen_list = ["九州旅客鉄道", "北九州高速鉄道", "平成筑豊鉄道", "甘木鉄道",
                  "皿倉登山鉄道", "福岡市交通局", "筑豊電気鉄道", "西日本鉄道"]
    df_rosen = pd.DataFrame()
    for rosen in rosen_list:
        gdf = gpd.read_file(f"./geojson/{rosen}.geojson", encoding="utf-8")
        gdf["company"] = rosen
        df_rosen = pd.concat([df_rosen, gdf])

    df_rosen.reset_index(inplace=True, drop=True)

    # 駅データ
    stations = gpd.read_file("./geojson/NumberOfPassengers.geojson",
                             encoging="utf-8")
    stations.loc[stations["S12_002"] == "福岡市", "S12_002"] = "福岡市交通局"
    stations_fukuoka = stations[stations["S12_002"].isin(rosen_list)][[
        "S12_001", "S12_002", "S12_003",
        "S12_046", "S12_047", "S12_049", "geometry"]]
    stations_fukuoka['first_coordinate'
                     ] = stations_fukuoka['geometry'].apply(
                         lambda line: (line.coords[0][1], line.coords[0][0]))
    stations_fukuoka.loc[stations_fukuoka["S12_047"] == 1, "S12_047"] = "有"
    stations_fukuoka.loc[stations_fukuoka["S12_047"] == 2, "S12_047"] = "無"
    stations_fukuoka.loc[stations_fukuoka["S12_047"] == 3, "S12_047"] = "非公開"

    filtered_features = [feature for feature in fukuoka['features']
                         if feature['properties'].get('N03_007') is not None]
    # for feature in filtered_features:
    #     properties = feature.get('properties', {})
    #     n03_003_value = properties.get("N03_003", None)
    #     n03_007_value = properties.get('N03_007', None)
    #     if n03_003_value == "北九州市":
    #         properties['N03_007'] = "40100"
    #     elif n03_003_value == "福岡市":
    #         properties["N03_007"] = "40130"

    fukuoka = {
        'type': 'FeatureCollection',
        'crs': fukuoka['crs'],
        'features': filtered_features
    }

    # 人口・所得データ
    fukuoka_df = pd.read_excel("./人口増減.xlsx")
    fukuoka_df["市区町村コード"] = fukuoka_df["市区町村コード"].astype(str)
    fukuoka_df.loc[fukuoka_df["市区町村コード"].str[:4] == "4010",
                   "課税対象所得(百万円)(2021)"] = 1323568
    fukuoka_df.loc[fukuoka_df["市区町村コード"].str[:4] == "4013",
                   "課税対象所得(百万円)(2021)"] = 2689842
    fukuoka_df.loc[fukuoka_df["市区町村コード"].str[:4] == "4010",
                   "納税義務者数(2021)"] = 410915
    fukuoka_df.loc[fukuoka_df["市区町村コード"].str[:4] == "4013",
                   "納税義務者数(2021)"] = 742167
    fukuoka_df["一人当たり課税対象所得(百万円)"
               ] = fukuoka_df['課税対象所得(百万円)(2021)'] / fukuoka_df['納税義務者数(2021)']
    fukuoka_df["10~14歳の人口増加率(1年間)"] = 100 * (fukuoka_df["10~14歳の人口(2023)"] - fukuoka_df["10~14歳の人口(2022)"]) / fukuoka_df["10~14歳の人口(2022)"]
    fukuoka_df["10~14歳の人口増加率(3年間)"] = 100 * (fukuoka_df["10~14歳の人口(2023)"] - fukuoka_df["10~14歳の人口(2020)"]) / fukuoka_df["10~14歳の人口(2020)"]

    fukuoka_df = fukuoka_df[
        (fukuoka_df["市区町村"] != "福岡市") & (fukuoka_df["市区町村"] != "北九州市")]

    map_center = [33.590204, 130.420850]  # 福岡
    my_map = folium.Map(location=map_center,
                        tiles='cartodbpositron', zoom_start=9)

    population = folium.Choropleth(                   # コロプレス図を表示する
        geo_data=fukuoka,                             # 市区町村の形が入ったデータ
        data=fukuoka_df,                              # 色分けの基準が入ったデータ
        columns=["市区町村コード", "2023年の人口"],
        key_on="feature.properties.N03_007",          # geo_dataの、dataと対応するカラム
        fill_color='BuGn',                            # 色を指定
        nan_fill_color='darkgray',                    # データがない区域の色を指定
        fill_opacity=0.8,
        nan_fill_opacity=0.8,
        line_opacity=0.2,
        legend_name='2023年の人口',
        name="人口(2023年)",
        bins=list(fukuoka_df["2023年の人口"
                             ].quantile(threshold)),
    ).add_to(my_map)

    income = folium.Choropleth(
        geo_data=fukuoka,
        data=fukuoka_df,
        columns=["市区町村コード", "一人当たり課税対象所得(百万円)"],
        key_on="feature.properties.N03_007",
        fill_color='RdPu',
        nan_fill_color='darkgray',
        fill_opacity=0.8,
        nan_fill_opacity=0.8,
        line_opacity=0.2,
        legend_name='一人当たり課税対象所得(百万円)',
        name="一人当たり課税対象所得(百万円)",
        bins=list(
            fukuoka_df["一人当たり課税対象所得(百万円)"].quantile(threshold)),
        show=False,
    )

    population_density = folium.Choropleth(
        geo_data=fukuoka,
        data=fukuoka_df,
        columns=["市区町村コード", "2023年の人口密度"],
        key_on="feature.properties.N03_007",
        fill_color='OrRd',
        nan_fill_color='darkgray',
        fill_opacity=0.8,
        nan_fill_opacity=0.8,
        line_opacity=0.2,
        legend_name='2023年の人口密度(人/km^2)',
        name="2023年の人口密度(人/km^2)",
        bins=list(
            fukuoka_df["2023年の人口密度"].quantile(threshold)),
        show=False,
    )

    choropleth_list = [population, income, population_density]
    for cp in choropleth_list:
        for key in cp._children:
            if key.startswith('color_map'):
                del (cp._children[key])
        cp.add_to(my_map)
        data_indexed = fukuoka_df.set_index("市区町村コード")
        # for s in cp.geojson.data["features"]:
        #     s["properties"]["population"] = data_indexed.loc[s["id"],
        # "2023年の人口"]
        folium.GeoJsonTooltip(["N03_004"], ["地域"]).add_to(cp.geojson)

    stations_cluster = MarkerCluster(
        maxClusterRadius=40, disableClusteringAtZoom=13,
        name="駅").add_to(my_map)
    for i, row in stations_fukuoka.iterrows():
        popup_text = row["S12_003"] + "<br/>" + row["S12_001"] + "駅<br/>" + "乗降者数：" + str(row["S12_049"]) + "人<br/>" + "データ状況：" + str(row["S12_047"])
        popup_html = folium.Html(popup_text, script=True)
        folium.Marker(
            location=row["first_coordinate"],
            popup=folium.Popup(popup_html, max_width=100),
            icon=folium.plugins.BeautifyIcon(icon="train"),
        ).add_to(stations_cluster)

    folium.GeoJson(
        df_rosen, name="路線図",
        style_function=lambda x: {"color": "gray"}).add_to(my_map)

    folium.LayerControl().add_to(my_map)

    st_folium(my_map, use_container_width=True,
              height=720, returned_objects=[])
