# Prepare packages -----------------------------------------------------------------------------------------------------
from folder import *

# Packages for spatial data manipulation
from shapely.geometry import Polygon                        # For creating polygons to change raster values
from shapely.ops import linemerge, unary_union, polygonize  # For spliting polygons using linestring
import geopandas as gpd                                     # For manipulating shape files
import rioxarray as rxr                                     # For manipulating spatial data under xarray array format

# Packages for data manipulation
import numpy as np
import pandas as pd

import json

# Packages for transformation
from transformation import wrapping_point_rotation, \
                           wrapping_point_translation       # For transforming polygon boundaries
# ----------------------------------------------------------------------------------------------------------------------


def value_change(shapefile_func, file_need_changing_func, value_func, inside=True):
    """
    @Definition:
                A function to change pixel values inside or outside polygons
    @References:
                https://corteva.github.io/rioxarray/html/rioxarray.html
                https://corteva.github.io/rioxarray/stable/examples/convert_to_raster.html
                https://gis.stackexchange.com/questions/414194/changing-raster-pixel-values-outside-of-polygon-box-using-rioxarray
                https://automating-gis-processes.github.io/CSC/notebooks/L2/geopandas-basics.html
                https://corteva.github.io/rioxarray/stable/getting_started/nodata_management.html
                https://gdal.org/programs/gdal_translate.html
                https://gis.stackexchange.com/questions/390438/replacing-nodata-values-by-a-constant-using-gdal-cli-tools
    @Arguments:
                shapefile_func (polygon):
                                            Polygon boundaries
                file_need_changing_func (string):
                                            File contains values that need changing
                value_func (int or float):
                                            Values used to replace
                inside (boolean):
                                            If True, change values inside, else, change values outside
    @Returns:
                None.
    """
    # Set up value changing command
    if inside:
        # Change values inside polygons
        inside_command = fr"gdal_rasterize -burn {value_func} {shapefile_func} {file_need_changing_func}"
        os.system(inside_command)
    else:
        # Change values outside polygons
        outside_command = fr"gdal_rasterize -i -burn {value_func} {shapefile_func} {file_need_changing_func}"
        os.system(outside_command)


def polygon_generation(
        number_simulation,
        angle_func,
        x_translation_func,
        y_translation_func,
        center_x_func,
        center_y_func,
        padding=True
):

    """
    @Definition:
                A function to transform the polygon and write out shapefile
    @References:
                None.
    @Arguments:
                number_simulation (string):
                            A string to identify the order of simulation (should be angle, x, y)
                angle_func, x_translation_func, y_translation_func (float):
                            Values to rotate and translate
                center_x_func (float):
                            X coordinate of original/reference DEM
                center_y_func (float):
                            Y coordinate of original/reference DEM
                padding (boolean):
                            For removing padding
                num_padding_sea (boolean):
                            True - the first
                            False - the second
    @Return:
                None.
    """

    # Get extent information of original no-padding raster
    raster_no_padding = rxr.open_rasterio(fr"{original_lidar_path}/no_padding/no_padding.nc")
    no_padding_xmin, no_padding_ymin, no_padding_xmax, no_padding_ymax = raster_no_padding.rio.bounds()

    if padding:
        # Create polygon to remove PADDING values
        # Set up polygon coordinates into a list
        polygon_padding = [(no_padding_xmax, no_padding_ymax),
                           (no_padding_xmax, no_padding_ymin),
                           (no_padding_xmin, no_padding_ymin),
                           (no_padding_xmin, no_padding_ymax),
                           (no_padding_xmax, no_padding_ymax)]

        output_name = "padding"

    else:
        # Read general parameters file
        with open(fr"{other_data}/general_parameters.json", 'r') as general_parameters_file:
            general_parameters = json.load(general_parameters_file)

        # Read files
        sea_linestring = gpd.read_file(fr"{other_data}/sea_linestring.shp")
        catchment_shapefile = gpd.read_file(fr"{original_lidar_path}/no_padding/catchment_boundary.geojson")

        # Convert to list
        sea_linestring_list = [sea_linestring['geometry'][0]]
        catchment_boundary = catchment_shapefile['geometry'][0].boundary

        # Splitting polygon into sub-polygons using linestring
        sea_linestring_list.append(catchment_boundary)
        multi_sea_linestrings = unary_union(sea_linestring_list)
        multi_sea_linestrings = linemerge(multi_sea_linestrings)
        multi_catchments = polygonize(multi_sea_linestrings)
        multi_catchments_list = list(multi_catchments)

        # Get the sea polygon
        sea_catchment = multi_catchments_list[general_parameters['sea_catchment']]

        # Get the list of array of points of sea polygon catchment
        sea_catchment_point_list = np.array([
            np.array(
                (sea_catchment.exterior.coords.xy[0][i],
                 sea_catchment.exterior.coords.xy[1][i])
            ) for i in range(len(sea_catchment.exterior.coords.xy[0]))
        ])

        # Change the name
        polygon_padding = sea_catchment_point_list.copy()
        output_name = 'sea'


    # Convert the list into array to do transformation
    boundary_coordinates = np.array(polygon_padding).astype('float64')

    # Transform
    rotated_boundary = wrapping_point_rotation(boundary_coordinates, angle_func, center_x_func, center_y_func, 0)
    translated_boundary = wrapping_point_translation(rotated_boundary, x_translation_func, y_translation_func)

    # Convert into shapely geometry Polygon
    shapely_polygon = Polygon(translated_boundary)

    # Create geopandas dataframe
    polygon_dataframe = gpd.GeoDataFrame(geometry=[shapely_polygon], crs=2193)

    # Write into shape file
    # Notice that the folder <transformed_{number_simulation}> was created in module demRaster,
    # function <necessary_files>
    pathlib.Path(
        fr"{bathy_transformed_shapefile}/{output_name}/bathy_transformed_{number_simulation}"
    ).mkdir(parents=True, exist_ok=True)
    polygon_dataframe.to_file(
        fr"{bathy_transformed_shapefile}/{output_name}/bathy_transformed_{number_simulation}/polygon_{number_simulation}.shp",
        crs=2193
    )


def value_padding_change(
        number_simulation,
        angle_func, x_translation_func, y_translation_func,
        center_x_func, center_y_func
):
    """
    @Definition:
                A function to change the values of padding
    @References:
                None.
    @Arguments:
                number_simulation (string):
                            A string to identify the order of simulation (should be angle, x, y)
                angle_func, x_translation_func, y_translation_func (float):
                            Values to rotate and translate
                center_x_func (float):
                            X coordinate of original/reference DEM
                center_y_func (float):
                            Y coordinate of original/reference DEM
    @Return:
                None.
    """
    # Create polygon shapefile for PADDING
    polygon_generation(
        number_simulation,
        angle_func, x_translation_func, y_translation_func,
        center_x_func, center_y_func, True
    )

    # Shapefile path
    shapefile_padding_dir = fr"{bathy_transformed_shapefile}/padding/bathy_transformed_{number_simulation}/polygon_{number_simulation}.shp"

    # DEM ----------------------------------------------
    # Convert raster from NetCDF file into GeoTiff file
    raster_nc = rxr.open_rasterio(
        fr"{bathy_transformed_dem_nc_path}/dem_bathy_transformed_{number_simulation}.nc"
    )

    raster_nc.z.rio.to_raster(
        fr"{bathy_transformed_dem_tiff_path}/dem_bathy_transformed_{number_simulation}.tif", cache=False
    )

    # Get directory of shapefile and file that has values need changing
    dem_need_changing_dir = fr"{bathy_transformed_dem_tiff_path}/dem_bathy_transformed_{number_simulation}.tif"

    # Changing padding values into -9999
    value_change(shapefile_padding_dir, dem_need_changing_dir, -9999, False)

    # MANNING'S N ----------------------------------------
    # Convert raster from NetCDF file into GeoTiff file
    raster_nc = rxr.open_rasterio(
        fr"{bathy_transformed_n_nc_path}/n_bathy_transformed_{number_simulation}.nc"
    )

    raster_nc.rio.to_raster(
        fr"{bathy_transformed_n_tiff_path}/n_bathy_transformed_{number_simulation}.tif", cache=False
    )

    # Get directory of shapefile and file that has values need changing
    n_need_changing_dir = fr"{bathy_transformed_n_tiff_path}/n_bathy_transformed_{number_simulation}.tif"

    # Changing padding values into -9999
    value_change(shapefile_padding_dir, n_need_changing_dir, -9999, False)

    # STARTDEPTH ---------------------------------------
    # Get directory of shapefile and file that has values need changing
    startdepth_need_changing_dir = fr"{bathy_transformed_startdepth_tiff_path}/startdepth_{number_simulation}.tif"

    # Changing padding values into -9999
    value_change(shapefile_padding_dir, startdepth_need_changing_dir, -9999, False)


def value_sea_change(
        number_simulation,
        angle_func, x_translation_func, y_translation_func,
        center_x_func, center_y_func,
        polygon=True,
):
    """
    @Definition:
                A function to change the values of sea area
    @References:
                None.
    @Arguments:
                number_simulation (string):
                            A string to identify the order of simulation (should be angle, x, y)
                angle_func, x_translation_func, y_translation_func (float):
                            Values to rotate and translate
                center_x_func (float):
                            X coordinate of original/reference DEM
                center_y_func (float):
                            Y coordinate of original/reference DEM
                polygon (boolean):
                            True means using polygon to change the values of sea area
                            False means using tide level to change the values of sea area

    @Return:
                None.
    """

    if polygon:
        # Create polygon shapefile for sea
        polygon_generation(
            number_simulation,
            angle_func, x_translation_func, y_translation_func,
            center_x_func, center_y_func, False
        )

        # SEA SHAPEFILE -----------------
        shapefile_sea_dir = fr"{bathy_transformed_shapefile}/sea/bathy_transformed_{number_simulation}/polygon_{number_simulation}.shp"

        # DEM ---------------------------
        dem_need_changing_dir = fr"{bathy_transformed_dem_tiff_path}/dem_bathy_transformed_{number_simulation}.tif"
        value_change(shapefile_sea_dir, dem_need_changing_dir, -9999, True)


        # MANNING'S N ---------------------
        n_need_changing_dir = fr"{bathy_transformed_n_tiff_path}/n_bathy_transformed_{number_simulation}.tif"
        value_change(shapefile_sea_dir, n_need_changing_dir, -9999, True)

        # STARTDEPTH --------------------
        startdepth_need_changing_dir = fr"{bathy_transformed_startdepth_tiff_path}/startdepth_{number_simulation}.tif"
        value_change(shapefile_sea_dir, startdepth_need_changing_dir, 0, True)

    else:
        # Get tide flow data
        tide_flow_df = pd.read_csv(fr"{other_data}/tide_flow_data.csv", sep=',')
        tide_flow_df['DateTime'] = pd.to_datetime(tide_flow_df['DateTime'], format="%Y-%m-%d %H:%M:%S", utc=False)

        # Get dem file from GeoTiff file and make a copy of it
        dem = rxr.open_rasterio(fr"{bathy_transformed_dem_tiff_path}/dem_bathy_transformed_{number_simulation}.tif")
        dem_copy = dem.copy(deep=True)

        # Get Manning's n file from GeoTiff file and make a copy of it
        n = rxr.open_rasterio(fr"{bathy_transformed_n_tiff_path}/n_bathy_transformed_{number_simulation}.tif")
        n_copy = n.copy(deep=True)

        # Get startdepth from GeoTiff file and make a copy of it
        startdepth = rxr.open_rasterio(fr"{bathy_transformed_startdepth_tiff_path}/startdepth_{number_simulation}.tif")
        startdepth_copy = startdepth.copy(deep=True)

        # Get sea area
        seaarea = dem_copy * np.nan
        seaarea = seaarea.where(dem_copy >= (np.min(tide_flow_df.Level)+0.2), other=1) # value 0.2 here can be
        # adjusted manually and accordingly

        # Remove sea area
        dem_xr_domain_copy = dem_copy.where(seaarea.values != 1, other=np.nan) # DEM
        startdepth_copy = startdepth_copy.where(seaarea.values != 1, other=np.nan) # STARTDEPTH
        n_copy = n_copy.where(seaarea.values != 1, other=np.nan) # MANNING'S N

        # Write out file
        dem_xr_domain_copy.rio.to_raster(fr"{bathy_transformed_dem_tiff_path}/dem_bathy_transformed_{number_simulation}.tif", cache=False)
        startdepth_copy.rio.to_raster(fr"{bathy_transformed_startdepth_tiff_path}/startdepth_{number_simulation}.tif", cache=False)
        n_copy.rio.to_raster(fr"{bathy_transformed_n_tiff_path}/n_bathy_transformed_{number_simulation}.tif", cache=False)


def convert_to_asc(number_simulation):

    """
    @Definition:
                A function to change the values of padding
    @References:
                None.
    @Arguments:
                number_simulation (string):
                            A string to identify the order of simulation (should be angle, x, y)
    @Return:
                None.
    """

    # DEM ---------------------------------
    # Convert GeoTiff file into ASCII file
    tiff_dem_func = rxr.open_rasterio(
        fr"{bathy_transformed_dem_tiff_path}/dem_bathy_transformed_{number_simulation}.tif"
    )
    nodata_tiff_dem_func = tiff_dem_func.rio.write_nodata(-9999, inplace=True)
    crs_tiff_dem_func = nodata_tiff_dem_func.rio.write_crs(2193)
    crs_tiff_dem_func.rio.to_raster(fr"{bathy_transformed_dem_asc_path}/dem_bathy_transformed_{number_simulation}.asc")

    # MANNING'S N ---------------------------
    # Convert GeoTiff file into ASCII file
    tiff_n_func = rxr.open_rasterio(
        fr"{bathy_transformed_n_tiff_path}/n_bathy_transformed_{number_simulation}.tif"
    )
    tiff_n_func_upperlimit = tiff_n_func.where(tiff_n_func.values < 10000, 0)
    tiff_n_func_lowerlimit = tiff_n_func_upperlimit.where(tiff_n_func.values > -10000, -9999)
    nodata_tiff_n_func = tiff_n_func_lowerlimit.rio.write_nodata(-9999)
    nodata_tiff_n_func.rio.to_raster(fr"{bathy_transformed_n_asc_path}/n_bathy_transformed_{number_simulation}.asc")

    # STARTDEPTH --------------------------
    # Convert GeoTiff file into ASCII file
    tiff_startdepth_func = rxr.open_rasterio(
        fr"{bathy_transformed_startdepth_tiff_path}/startdepth_{number_simulation}.tif"
    )
    nodata_tiff_startdepth_func = tiff_startdepth_func.rio.write_nodata(-9999, inplace=True)
    crs_tiff_startdepth_func = nodata_tiff_startdepth_func.rio.write_crs(2193)
    crs_tiff_startdepth_func.rio.to_raster(fr"{bathy_transformed_startdepth_asc_path}/startdepth_{number_simulation}.asc")