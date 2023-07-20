#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import geopandas as gpd
import kml2geojson as k2g
import json
from dash import dash, Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.wkt import loads
import dash_bootstrap_components as dbc
import cmocean
import gunicorn


# In[45]:


df = pd.read_csv('geo_ddcoord.csv')


# In[46]:


dashdf = df.drop(['Category','Date collected','Lat','Long', 'Geometry','Polygon Points'], axis=1)


# In[47]:


bar_P21 = dashdf[(dashdf['Year'] == 2021.0) & (dashdf['Sample timing'] == 'Pre-treatment')]

bar_F21 = dashdf[(dashdf['Year'] == 2021.0) & (dashdf['Sample timing'] == 'Fall')]

bar_P22 = dashdf[(dashdf['Year'] == 2022.0) & (dashdf['Sample timing'] == 'Pre-treatment')]

bar_F22 = dashdf[(dashdf['Year'] == 2022.0) & (dashdf['Sample timing'] == 'Fall')]


# In[48]:


geojson_file = "Arizona+Tree+Nuts_Cochise.geojson"

with open(geojson_file, "r") as file:
    data = json.load(file)

gdf = gpd.GeoDataFrame.from_features(data["features"], crs=2223)


# In[49]:


gdf.to_file('AZTreeNut_Cochise.shp')


# In[50]:


gdf = gdf.drop(['VARIETY','CTNUM','AF36','AF36PLANTDATE','GPS_NON','SOILSAMPLE','COTTON_TYPE','FSA'], axis=1)


# In[51]:


shapefile = "crop_poly.shp"

shapefile_gdf = gpd.read_file(shapefile)


# In[52]:


joined_gdf = gpd.sjoin(gdf, shapefile_gdf, how="left", predicate="intersects")


# In[53]:


def row_to_polygon(row):
    if isinstance(row, float) and np.isnan(row):
        return None
    row = row.strip("()")

    point_strings = row.split("), (")

    polygon_points = [(float(point.split(", ")[1]), float(point.split(", ")[0])) for point in point_strings]
    polygons = []
    polygon = Polygon(polygon_points)
    polygons.append(polygon)
    multipolygon = MultiPolygon(polygons)

    return polygon

joined_gdf['Polygon'] = joined_gdf['Polygon Po'].apply(row_to_polygon)
joined_gdf = gpd.GeoDataFrame(joined_gdf, geometry='Polygon', crs=2223)


# In[54]:


joined_gdf['index'] = joined_gdf.index


# In[55]:


csv_df = pd.read_csv('AZTreeNuts_CochiseEDITED.csv')


# In[56]:


csv_df.dropna(subset=['geometry'], inplace=True)


# In[57]:


csv_df['geometry'] = csv_df['geometry'].apply(lambda x: loads(x))

csvgdf = gpd.GeoDataFrame(csv_df, geometry='geometry', crs = 2223)


# In[58]:


map_P21 = csvgdf[(csvgdf['Year'] == 2021.0) & (csvgdf['Sample tim'] == 'Pre-treatment')]

map_F21 = csvgdf[(csvgdf['Year'] == 2021.0) & (csvgdf['Sample tim'] == 'Fall')]

map_P22 = csvgdf[(csvgdf['Year'] == 2022.0) & (csvgdf['Sample tim'] == 'Pre-treatment')]

map_F22 = csvgdf[(csvgdf['Year'] == 2022.0) & (csvgdf['Sample tim'] == 'Fall')]


# In[87]:


#completely interactive Dash map shared with interactive bar graph
fig0, fig1, fig2, fig3 = go.Figure(), go.Figure(), go.Figure(), go.Figure()

strain_options = [{'label': 'cfu/g', 'value': 'cfu/g'},
                  {'label': 'CFU L-tox', 'value': 'CFU L-tox'},
                  {'label': 'CFU AF36', 'value': 'CFU AF36'},
                  {'label': 'CFU S', 'value': 'CFU S'},
                  {'label': 'CFU tamarii', 'value': 'CFU tamarii'}]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.Header(
        dbc.Row([
            dbc.Col(html.H1(children=["Geospatial Analysis : Dispersal of ", html.Em("Aspergillus Flavus"),"\nStrains in Tree Nut Cropping Systems"], className="p-5"),width=12, style={'color': 'dark grey', 'textAlign':'center'})
        ]),
        style={'background-color': 'beige', 'padding': '20px'}
    ),
    dbc.Row([
        dbc.Col([html.H2(children='Select a Strain:', style={'textAlign':'left'}),
            dcc.RadioItems(
                id='strain',
                options=strain_options,
                value='CFU AF36',
                inline = False,
                style={'font-size':'20px'}
            ),    html.H4(children='Pre-treatment 2021', style={'textAlign':'center'}),
            dcc.Graph(id='graph0', figure=fig0),
            html.H4(children='Fall 2021', style={'textAlign':'center'}),
            dcc.Graph(id='graph1', figure=fig1),
            html.H4(children='Pre-treatment 2022', style={'textAlign':'center'}),
            dcc.Graph(id='graph2', figure=fig2),
            html.H4(children='Fall 2022', style={'textAlign':'center'}),
            dcc.Graph(id='graph3', figure=fig3)], width=8, style={'background-color': 'beige', 'border-radius': '5px', 'padding': '10px'}),
        dbc.Col([
            dcc.Dropdown(
                id='dataframe-dropdown',
                options=[
                    {'label': 'Pre-treatment 2021', 'value': 'bar_P21'},
                    {'label': 'Fall 2021', 'value': 'bar_F21'},
                    {'label': 'Pre-treatment 2022', 'value': 'bar_P22'},
                    {'label': 'Fall 2022', 'value': 'bar_F22'}
                ],
                value=None,
                placeholder='Select a Time Period'
            ),
        html.Br(),
        dcc.Dropdown(
                id='column-dropdown',
                options = strain_options,
                value=None,
                placeholder='Select a Strain'
            ),
            html.Br(),
            html.Div(id='output-div'),
            dbc.Col([
                dbc.Row([
                    dash_table.DataTable(data=[{}], page_size=12, style_table={'overflowX':'auto'}, id='datatable')
                ]),
                dbc.Row([
                    dcc.Graph(figure={}, id='graph-placeholder')
                ]),
            ], align='right')], width=4, style={'background-color': 'beige', 'border-radius': '5px', 'padding': '10px'}),
    ])
], fluid=True)

@app.callback(Output('graph0','figure'),[Input('strain','value')])
def update_graph0(selected_strain):
    fig0 = px.choropleth_mapbox(map_P21, geojson=map_P21.geometry, locations=map_P21.index, hover_name=map_P21['Distance'], color=selected_strain,
                           color_continuous_scale="tempo", mapbox_style="stamen-terrain",
                           center={'lat':32.32,'lon':-109.55}, zoom=9, range_color=(0,100))
    fig0.update_geos(fitbounds="locations", visible=False)
    fig0.update_layout(autosize = True,margin={"r": 0, "t": 0, "l": 0, "b": 0}, title='Pre-treatment 2021')
    return fig0
@app.callback(Output('graph1','figure'),[Input('strain','value')])
def update_graph1(selected_strain):
    fig1 = px.choropleth_mapbox(map_F21, geojson=map_F21.geometry, locations=map_F21.index, hover_name=map_F21['Distance'], color=selected_strain,
                           color_continuous_scale="tempo", mapbox_style="stamen-terrain",
                           center={'lat':32.32,'lon':-109.55}, zoom=9, range_color=(0,100))
    fig1.update_geos(fitbounds="locations", visible=False)
    fig1.update_layout(autosize = True,margin={"r": 0, "t": 0, "l": 0, "b": 0}, title='Fall 2021')
    return fig1
@app.callback(Output('graph2','figure'),[Input('strain','value')])
def update_graph2(selected_strain):
    fig2 = px.choropleth_mapbox(map_P22, geojson=map_P22.geometry, locations=map_P22.index, hover_name=map_P22['Distance'], color=selected_strain,
                           color_continuous_scale="tempo", mapbox_style="stamen-terrain",
                           center={'lat':32.32,'lon':-109.55}, zoom=9, range_color=(0,100))
    fig2.update_geos(fitbounds="locations", visible=False)
    fig2.update_layout(autosize = True,margin={"r": 0, "t": 0, "l": 0, "b": 0}, title='Pre-treatment 2022')
    return fig2
@app.callback(Output('graph3','figure'),[Input('strain','value')])
def update_graph3(selected_strain):
    fig3 = px.choropleth_mapbox(map_F22, geojson=map_F22.geometry, locations=map_F22.index, hover_name=map_F22['Distance'],color=selected_strain,
                           color_continuous_scale="tempo", mapbox_style="stamen-terrain",
                           center={'lat':32.32,'lon':-109.55}, zoom=9, range_color=(0,100))
    fig3.update_geos(fitbounds="locations", visible=False)
    fig3.update_layout(autosize = True,margin={"r": 0, "t": 0, "l": 0, "b": 0}, title='Fall 2022')
    return fig3

@app.callback(
    Output('output-div', 'children'),
    Output('datatable', 'data'),
    Output('datatable', 'columns'),
    Output('graph-placeholder', 'figure'),
    Input('dataframe-dropdown', 'value'),
    Input('column-dropdown', 'value')
)
def update_graph(dataframe_value, column_value):
    if dataframe_value is None or column_value is None:
        return 'Please make a selection.', [{}], [], {}
    else:
        if dataframe_value == 'bar_P21':
            df_chosen = bar_P21
        elif dataframe_value == 'bar_F21':
            df_chosen = bar_F21
        elif dataframe_value == 'bar_P22':
            df_chosen = bar_P22
        else:  
            df_chosen = bar_F22

        data = df_chosen.to_dict('records')
        columns = [{'name': col, 'id': col} for col in df_chosen.columns]

        fig = go.Figure(data=[go.Histogram(x=df_chosen['Distance'], y=df_chosen[column_value], histfunc='avg')])

        return ('',data,columns,fig)

if __name__ == '__main__':
    app.run_server(debug=True, port=8026)

