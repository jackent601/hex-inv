from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

from h3 import h3
import h3pandas
import folium

import geopandas as gpd
import geodatasets

DATA_DIR = os.path.join(settings.BASE_DIR, "hexvis", "datasets")
NS_CENTRE=[56.42, 2.74]
NS_ZOOM=5

# def visualize_hexagons(hexagons, color="red", folium_map=None):
#     """
#     hexagons is a list of hexcluster. Each hexcluster is a list of hexagons. 
#     eg. [[hex1, hex2], [hex3, hex4]]
#     """
#     polylines = []
#     lat = []
#     lng = []
#     for hex in hexagons:
#         polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
#         # flatten polygons into loops.
#         outlines = [loop for polygon in polygons for loop in polygon]
#         polyline = [outline + [outline[0]] for outline in outlines][0]
#         lat.extend(map(lambda v:v[0],polyline))
#         lng.extend(map(lambda v:v[1],polyline))
#         polylines.append(polyline)
    
#     if folium_map is None:
#         m = folium.Map(
#             location=[sum(lat)/len(lat), sum(lng)/len(lng)], 
#             zoom_start=13,
#             tiles='cartodbpositron')
#     else:
#         m = folium_map
#     for polyline in polylines:
#         my_PolyLine=folium.PolyLine(locations=polyline,weight=8,color=color)
#         m.add_child(my_PolyLine)
#     # Add lat/lon pop-up
#     m.add_child(folium.LatLngPopup()) 
#     return m
    

# def visualize_polygon(polyline, color):
#     polyline.append(polyline[0])
#     lat = [p[0] for p in polyline]
#     lng = [p[1] for p in polyline]
#     m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
#     my_PolyLine=folium.PolyLine(locations=polyline,weight=8,color=color)
#     m.add_child(my_PolyLine)
#     return m

def getFoliumPolygonMapFromGeoPd(df, 
                        location=[40.70, -73.94], 
                        zoom_start=10, 
                        tiles="CartoDB positron",
                        fillColor="orange",
                        popup="BoroName"):
    """
    Plots shape file in geopandas onto folium
    https://geopandas.org/en/stable/gallery/polygon_plotting_with_folium.html
        using geopandas db plots example polygon on folium map
        GeopandasDB(Polygon) -> Folium Map object
        df should be a WGS 84 (epsg:4326) geopandas dataframe
        default values are for example
    
    Can also hex-ify shape file to plot hexes
    https://stackoverflow.com/questions/63516948/how-to-convert-shapefile-geojson-to-hexagons-using-uber-h3-in-python
        converts polygon to hex, then plots the hex polygons
        df must be a geopandas dataframe
    """
    m = folium.Map(location=location, zoom_start=zoom_start, tiles=tiles)
    for _, r in df.iterrows():
        # Without simplifying the representation of each borough,
        # the map might not be displayed
        sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": fillColor})
        if popup is not None:
            folium.Popup(r[popup]).add_to(geo_j)
        geo_j.add_to(m)
    return m

def getHexifiedGeoPdFromShapeGeoPd(df, resolution = 7):
    """
    https://stackoverflow.com/questions/63516948/how-to-convert-shapefile-geojson-to-hexagons-using-uber-h3-in-python
    converts polygon to hex geopandas representation
    df must be a geopandas dataframe
    """
    # Resample to H3 cells
    return df.h3.polyfill_resample(resolution)

def getFoliumHexifiedMapFromGeoPd(df, resolution = 7):
    """
    https://stackoverflow.com/questions/63516948/how-to-convert-shapefile-geojson-to-hexagons-using-uber-h3-in-python
    converts polygon to hex, then plots the hex polygons
    df must be a geopandas dataframe
    """
    # Resample to H3 cells
    gdf_h3 = getHexifiedGeoPdFromShapeGeoPd(df, resolution=resolution)
    # Plot H3 as polygons
    return getFoliumPolygonMapFromGeoPd(gdf_h3)


def getFoliumMapFromDataPath(datapath=None,
                                 hexify=False,
                                 resolution = 7,
                                 location=[40.70, -73.94], 
                                 zoom_start=10, 
                                 tiles="CartoDB positron",
                                 fillColor="orange",
                                 popup="BoroName"):
    """
    example -> https://geopandas.org/en/stable/gallery/polygon_plotting_with_folium.html
    """
    if datapath is None:
        datapath = geodatasets.get_path("nybb")
    df = gpd.read_file(datapath)
    # Use WGS 84 (epsg:4326) as the geographic coordinate system
    df = df.to_crs(epsg=4326)
    if hexify:
        df = df.h3.polyfill_resample(resolution)
    return getFoliumPolygonMapFromGeoPd(df, location=location, zoom_start=zoom_start, tiles=tiles, fillColor=fillColor, popup=popup)

def renderDisplayMapFromPath(request,
                             datapath=None,
                             template="hexdemo.html",
                             hexify=False,
                             resolution = 7,
                             location=[40.70, -73.94],
                             zoom_start=10,
                             tiles="CartoDB positron",
                             fillColor="orange",
                             popup="BoroName"):
    
    m = getFoliumMapFromDataPath(datapath=datapath,
                                 hexify=hexify,
                                 resolution = resolution,
                                 location=location, 
                                 zoom_start=zoom_start, 
                                 tiles=tiles,
                                 fillColor=fillColor,
                                 popup=popup)
    
    displayContext={}
    displayContext["map"]=m._repr_html_()
    displayContext["form"]="test"
    return render(request, template, displayContext)
    
def index(request):
    m = folium.Map(location=NS_CENTRE, zoom_start=NS_ZOOM, tiles="CartoDB positron")
    return render(request, "hexdemo.html", {"map":m._repr_html_()})

def geopd(request):
    return renderDisplayMapFromPath(request)
    
def hexpd(request):
    return renderDisplayMapFromPath(request, hexify=True)

def geons(request):
    return renderDisplayMapFromPath(request, datapath=os.path.join(DATA_DIR,"iho.zip"),
                                     location=NS_CENTRE, 
                                     zoom_start=NS_ZOOM,
                                     popup=None)

def hexns(request):
    return renderDisplayMapFromPath(request, datapath=os.path.join(DATA_DIR,"iho.zip"),
                                     location=NS_CENTRE, 
                                     zoom_start=NS_ZOOM,
                                     hexify=True,
                                     resolution=4,
                                     popup=None)



