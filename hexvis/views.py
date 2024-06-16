from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os
import colorsys

from h3 import h3
import h3pandas
import folium

import geopandas as gpd
import geodatasets

DATA_DIR = os.path.join(settings.BASE_DIR, "hexvis", "datasets")
NS_CENTRE=[56.42, 2.74]
NS_ZOOM=5

def getFoliumPolygonMapFromGeoPd(df, 
                        location=[40.70, -73.94], 
                        zoom_start=10, 
                        tiles="CartoDB positron",
                        fillColor="orange",
                        popup="BoroName",
                        m=None):
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
    if m is None:
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

def getHexFromPoints(df, pointColumn, res):
    """adds href from geometry point"""
    df["h3ref"] = df.apply(lambda x: h3.geo_to_h3(x[pointColumn].xy[1][0], x[pointColumn].xy[0][0], res), axis=1)
    return df

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

def filterGeoPandasByShapeAndCount(geoPandasShapeBoundary, geoPandasAreas, res, count=False):
    """
    Takes first row of geoPandasShapeBoundary to get shape
    Filters all points in geoPandasAreas for points in area
    """
    entryInBoundary = geoPandasAreas.within(geoPandasShapeBoundary.loc[0, 'geometry'])
    #creating a new geoDataFrame that will have only the intersecting records
    filteredAreas = geoPandasAreas.loc[entryInBoundary]#.copy()
    # Get Points
    filteredAreas["rep_points"] = filteredAreas.geometry.representative_point()
    # Hexify Points
    filteredAreas = getHexFromPoints(filteredAreas, "rep_points", res)
    if count:
        filteredAreas = countHRefPandas(filteredAreas)
    # Add shape for hex
    filteredAreas = filteredAreas.set_index("h3ref").h3.h3_to_geo_boundary()
    return filteredAreas

def countHRefPandas(geoPD, h3ref="h3ref", normalise=True):
    # aggregate over similar hexes
    hsrefSummary = geoPD.groupby([h3ref]).size()
    # make dataframe
    summaryDF = hsrefSummary.to_frame(name="count")
    # Get polgons of only aggregates
    # First normalise the range to [0-1]
    minVal=summaryDF["count"].min()
    maxVal=summaryDF["count"].max()
    summaryDF['normalised'] = (summaryDF["count"] - minVal) / (maxVal - minVal) 
    return summaryDF.h3.h3_to_geo_boundary().reset_index()
    
def index(request):
    m = folium.Map(location=NS_CENTRE, zoom_start=NS_ZOOM, tiles="CartoDB positron")
    return render(request, "hexdemo.html", {"map":m._repr_html_()})

def geopd(request):
    return renderDisplayMapFromPath(request)
    
def hexpd(request):
    return renderDisplayMapFromPath(request, hexify=True)

DATAPATH_DICT={"north_sea":"iho.zip","wrecks":"wrecks/Areas.shp"}

def geons(request):
    # Get Data Set
    flavour = request.GET.get('flavour', 'north_sea')
    if flavour not in DATAPATH_DICT.keys():
        flavour = "north_sea"
    dataPath = DATAPATH_DICT["north_sea"]
    # Check if hexify
    hexify=False
    hexifyQ = request.GET.get('hexify', '')
    if hexifyQ != '':
        hexify=True
    # Get Resolution
    res = int(request.GET.get('res', 4))
    
    return renderDisplayMapFromPath(request, datapath=os.path.join(DATA_DIR,dataPath),
                                     location=NS_CENTRE, 
                                     zoom_start=NS_ZOOM,
                                     hexify=hexify,
                                     resolution=res,
                                     popup=None)

# converting colours
def rgb2hex(r,g,b):
    return '#%02x%02x%02x' % (r, g, b)

def getScaledRedToYellow(normalisedValue, zeroColor=None):
    if normalisedValue == 0:
        return zeroColor
    return rgb2hex(round(255*1),round(255*(1-normalisedValue)),round(0*1))

def geowreck(request):
    # Get Resolution
    res = int(request.GET.get('res', 3))
    
    # - - - - - - Exported to geopandas - - - - - -
    # Load Wreck Data
    # wrecks = gpd.read_file(os.path.join(DATA_DIR,"wrecks/Areas.shp"))
    # # Use WGS 84 (epsg:4326) as the geographic coordinate system
    # wrecks = wrecks.to_crs(epsg=4326)
    # # Load North Sea Data
    ns = gpd.read_file(os.path.join(DATA_DIR,"iho.zip"))
    # # Filter wrecks to north sea, and get hex for each cell
    # wrecksParsed = filterGeoPandasByShapeAndCount(ns, wrecks, res, count=True)
    # - - - - - - - - - - - - - - - - - - - - - - - - 
    
    # - - - - - - From pre-wrangled data (faster) - - - - - -
    # load
    nsWreckPoints=gpd.read_file(os.path.join(DATA_DIR,"northsea_wreck_points/nsWreckPoints.shp"))
    # Get hex
    nsWreckPoints["h3ref"] = nsWreckPoints.apply(lambda x: h3.geo_to_h3(x['geometry'].xy[1][0], x['geometry'].xy[0][0], res), axis=1)
    # Agg
    # aggregate over similar hexes
    wreckSummary = nsWreckPoints.groupby(["h3ref"]).size()
    wreckSummary = wreckSummary.to_frame(name="count")
    # Normalise
    minVal=wreckSummary["count"].min()
    maxVal=wreckSummary["count"].max()
    wreckSummary['normalised'] = (wreckSummary["count"] - minVal) / (maxVal - minVal) 

    
    # Hexify North Sea Data
    ns = ns.to_crs(epsg=4326)
    ns = ns.h3.polyfill_resample(res).reset_index()
    ns['h3ref']=ns['h3_polyfill'] # prep for merge
    
    # Merge wrecks to NS
    merged = wreckSummary.merge(ns, how='outer', on='h3ref')
    mergedRefAndCount = merged[["h3ref","count", "normalised"]]
    mergedRefAndCount = mergedRefAndCount.fillna(0)

    mergedRefAndCount=mergedRefAndCount.set_index("h3ref")
    mergedRefAndCount=mergedRefAndCount.h3.h3_to_geo_boundary()
    
    # Add colour param
    # wrecksParsed['countColorCode']=wrecksParsed.apply(lambda x: getScaledRedToYellow(x['normalised'], zeroColor="#99CCFF"), axis=1)

    # Get Map
    m = folium.Map(location=NS_CENTRE, zoom_start=NS_ZOOM, tiles="CartoDB positron")
    for _, r in mergedRefAndCount.iterrows():
        normalCount = r['normalised']
        fillColour=getScaledRedToYellow(normalCount,"#66B2FF")
        sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x,fillColour=fillColour: {"fillColor": fillColour})
        # if popup is not None:
        folium.Popup(str(r['count'])).add_to(geo_j)
        geo_j.add_to(m)
    m
    # for _, r in wrecksParsed.iterrows():
    #     fillColour = r['countColorCode']
    #     sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
    #     geo_j = sim_geo.to_json()
    #     geo_j = folium.GeoJson(data=geo_j, style_function=lambda x,fillColour=fillColour: {"fillColor": fillColour})
    #     # if popup is not None:
    #     folium.Popup(str(r['count'])).add_to(geo_j)
    #     geo_j.add_to(m)
        
    # Render    
    displayContext={}
    displayContext["map"]=m._repr_html_()
    displayContext["form"]="test"
    return render(request, "hexdemo.html", displayContext)

# def hexns(request):
#     return renderDisplayMapFromPath(request, datapath=os.path.join(DATA_DIR,"iho.zip"),
#                                      location=NS_CENTRE, 
#                                      zoom_start=NS_ZOOM,
#                                      hexify=True,
#                                      resolution=4,
#                                      popup=None)

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