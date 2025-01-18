# Prepare packages -----------------------------------------------------------------------------------------------------
# Packages for paths manipulation
from folder import *                              # For paths of sub-folders
import os                                         # For manipulating the directory path and to execute commands
import pathlib                                    # For manipulating the directory path

# Packages for untransformation
import numpy as np                                # For all calculation and data array/matrices manipulation
from transformation import center_calculation     # For center calculation
from valueChange import value_sea_change          # For filtering the sea area


# Packages for unrotating and untranslating
import rioxarray as rxr                           # For reading flowdepth files
import rasterio                                   # For reading and manipulating spatial data
import rasterio.features                          # For vectorising features in array
from shapely.geometry import shape                # For manipulating spatial information (geometry) under GeoJSON format
import geopandas as gpd                           # For manipulating shape files


# Packages for multiprocessing
from functools import partial                       # For containing many variables
import multiprocessing                              # For parallelising

from valueChange import value_change


# ----------------------------------------------------------------------------------------------------------------------


def water_extraction(
    number_simulation,
    extract_name
):
    """
    @Definition:
                A function to extract and add crs into a specific flowdepth file
    @References:
                None.
    @Arguments:
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                extract_name (string):
                                            Name of a specific output among all flood model outputs
    @Returns:
                None.
    """
    # Extract required water file
    water_asc = rxr.open_rasterio(
        fr"{bathy_transformed_FPoutput_path}/bathy_transformed_{number_simulation}/{extract_name}"
    )

    # Add crs
    new_water = water_asc.rio.write_crs(2193)

    # Write out new flowdepth file
    if extract_name == 'out.max':
        new_water.rio.to_raster(fr"{extracted_wd}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
    else:
        new_water.rio.to_raster(fr"{extracted_wse}/bathy_untransformed_{extract_name}_{number_simulation}.nc")

def river_filter(
    number_simulation,
    extract_name
):
    """
    @Definition:
                A function to filter river by polygon in flood model output
    @References:
                None.
    @Arguments:
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                extract_name (string):
                                            Name of a specific output among all flood model outputs
    @Returns:
                None.
    """
    if extract_name == "out.max":
        water_origin = rxr.open_rasterio(fr"{extracted_wd}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
        filter_tiff = filter_extracted_wd_tiff
        filter_shp = filter_extracted_wd_shp
        filter_nc = filter_extracted_wd_nc
        filter_value = 0
    elif extract_name == 'out.mxe':
        water_origin = rxr.open_rasterio(fr"{extracted_wse}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
        filter_tiff = filter_extracted_wse_tiff
        filter_shp = filter_extracted_wse_shp
        filter_nc = filter_extracted_wse_nc
        filter_value = -9999
    else:
        dem_elev = rxr.open_rasterio(fr"{bathy_transformed_dem_nc_path}/dem_bathy_transformed_{number_simulation}.nc")
        water_origin = dem_elev.z
        filter_tiff = filter_extracted_elev_tiff
        filter_shp = filter_extracted_elev_shp
        filter_nc = filter_extracted_elev_nc
        filter_value = -9999

    # Convert netCDF file to Tiff
    water_origin.rio.to_raster(fr"{filter_tiff}/bathy_untransformed_{extract_name}_{number_simulation}.tif")

    # Convert geojson into shapefile
    river_geo = gpd.read_file(fr"{bathy_after_transformed_lidar_path}/bathy_transformed_lidar_{number_simulation}/element_dem/river_polygon.geojson")
    river_geo.to_file(fr"{filter_shp}/river_polygon_{number_simulation}.shp", crs=2193)

    # Remove river
    watertiff_path = fr"{filter_tiff}/bathy_untransformed_{extract_name}_{number_simulation}.tif"
    rivershp_path = fr"{filter_shp}/river_polygon_{number_simulation}.shp"
    value_change(rivershp_path, watertiff_path, filter_value, True)

    # Convert back to netcdf
    watertiff_filter = rxr.open_rasterio(fr"{filter_tiff}/bathy_untransformed_{extract_name}_{number_simulation}.tif")
    if extract_name == 'elev':
        watertiff_filter = watertiff_filter.rio.write_nodata(-9999)
        watertiff_filter.rio.to_raster(fr"{filter_nc}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
    else:
        watertiff_filter.rio.to_raster(fr"{filter_nc}/bathy_untransformed_{extract_name}_{number_simulation}.nc")


def polygon_bathy_untransformation(
    angle_func, x_translation_func, y_translation_func,
    number_simulation,
    extract_name, filter=False
):
    """
    @Definition:
                A function to convert raster into polygons and un-transform them
    @References:
                https://docs.dea.ga.gov.au/notebooks/Frequently_used_code/Polygonise_pixel_edges.html
                https://gis.stackexchange.com/questions/187877/how-to-polygonize-raster-to-shapely-polygons/

                https://github.com/sgillies/affine/blob/master/affine/__init__.py#L178
                https://gis.stackexchange.com/questions/408386/rotating-raster-using-python
                https://pythonhosted.org/PyAgg/affine.m.html

                https://gis.stackexchange.com/questions/408386/rotating-raster-using-python
                https://gis.stackexchange.com/questions/350526/gdal-setgeotransform-issue
                https://corteva.github.io/rioxarray/stable/examples/convert_to_raster.html
                https://gdal.org/tutorials/geotransforms_tut.html#geotransforms-tut
                https://gdal.org/tutorials/raster_api_tut.html
    @Arguments:
                angle_func, x_translation_func, y_translation_func (float):
                                            Values to rotate and translate
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                extract_name (string):
                                            Name of a specific output among all flood model outputs
                filter (boolean):
                                            True - filter river
                                            False - NOT filter river
    @Returns:
                None.
    """
    # Choose the outputs
    if filter:
        # If filter river
        if extract_name == 'out.max':
            untransformed_water = filter_bathy_untransformed_wd
            raster_poly = rasterio.open(fr"{filter_extracted_wd_nc}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
        elif extract_name == 'out.mxe':
            untransformed_water = filter_bathy_untransformed_wse
            raster_poly = rasterio.open(fr"{filter_extracted_wse_nc}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
        else:
            untransformed_water = filter_bathy_untransformed_elev
            raster_poly = rasterio.open(fr"{filter_extracted_elev_nc}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
        raster_array = raster_poly.read(1)
        raster_transform = raster_poly.transform
        raster_crs = raster_poly.crs
    else:
        # If NOT filter river
        if extract_name == 'out.max':
            extracted_water = extracted_wd
            untransformed_water = bathy_untransformed_wd
        elif extract_name == 'out.mxe':
            extracted_water = extracted_wse
            untransformed_water = bathy_untransformed_wse
        else:
            extracted_water = bathy_transformed_dem_nc_path
            untransformed_water = bathy_untransformed_elev

        # Extract array from flowdepth raster
        if extract_name == 'elev':
            raster_poly = rxr.open_rasterio(fr"{extracted_water}/dem_bathy_transformed_{number_simulation}.nc")
            raster_array = raster_poly.z.values
            raster_transform = raster_poly.z.rio.transform()
            raster_crs = raster_poly.z.rio.crs

        else:
            raster_poly = rasterio.open(fr"{extracted_water}/bathy_untransformed_{extract_name}_{number_simulation}.nc")
            raster_array = raster_poly.read(1)
            raster_transform = raster_poly.transform
            raster_crs = raster_poly.crs

    # Get new values for translation
    x_raster = x_translation_func / 10 * (-1)
    y_raster = y_translation_func / 10

    # Extract parameters: id and depth
    id_pixels = np.arange(raster_array.size).reshape(raster_array.shape)
    depth_list = list(raster_array.flatten())

    # Find out raster centers
    raster_center = center_calculation(False)

    # UNTRANSLATE affine transformation
    untransformed_1 = raster_transform * raster_transform.translation(x_raster, y_raster)

    # UNROTATE affine transformation
    untransformed_2 = untransformed_1 * untransformed_1.rotation(angle_func, raster_center)

    # Vectorise features
    untransformed_vectors = rasterio.features.shapes(source=id_pixels.astype(np.int16),
                                                     transform=untransformed_2)

    # List the UNTRANSFORMED polygons to extract necessary parameters
    untransformed_vectors_list = list(untransformed_vectors)

    # Get geometry
    polygons_geometry_values = [
        shape(polygon_geometry) for polygon_geometry, value_geometry in untransformed_vectors_list
    ]

    # Get id
    id_untransformed_pixels_values = [
        id_value for id_polygon, id_value in untransformed_vectors_list
    ]

    # Create UNTRANSFORMED database under geopandas dataframe (gdf) format
    untransformed_data = {
        "id": id_untransformed_pixels_values,
        "depth": depth_list
    }
    untransformed_raster_poly_gdf = gpd.GeoDataFrame(
        data=untransformed_data,
        geometry=polygons_geometry_values,
        crs=raster_crs
    )

    # Write out csv files
    untransformed_raster_poly_gdf.to_csv(
        fr"{untransformed_water}/bathy_untransformed_{extract_name}_{number_simulation}.csv", index=False
    )


def bathy_untransformation_simulation(
    extract_name,
    kind, para_name,
    filter,
    ran_bathy_trans_i

):
    """
    @Definition:
                A function to extract, convert raster into polygons, and un-transform them
    @References:
                None.
    @Arguments:
                extract_name (string):
                                        Name of a specific output among all flood model outputs
                kind (string):
                                        neal or rupp
                para_name (string):
                                        width, slope, flow, or combination
                filter (boolean):
                                        True - filter river
                                        False - NOT filter river
                ran_bathy_trans_i (array):
                                        A 3D array contains values of angle, x, and y coordinates of points in tiles
                                        (iterating variable generated from multiprocessing)
    @Returns:
                None.
    """
    # Get values
    bathy_val = int(ran_bathy_trans_i[0])
    angle_val = ran_bathy_trans_i[1]
    x_val = ran_bathy_trans_i[2]
    y_val = ran_bathy_trans_i[3]
    number_simulation = f"{kind}_{para_name}_{bathy_val}_a_{angle_val}_x_{x_val}_y_{y_val}"

    if extract_name == 'elev':

        if filter:
            # Remove river
            river_filter(
                number_simulation,
                extract_name
            )

            # Convert to and untransform polygons - filter river
            polygon_bathy_untransformation(
                angle_val, x_val, y_val,
                number_simulation,
                extract_name, True
            )

        else:
            # Convert to and untransform polygons
            polygon_bathy_untransformation(
                angle_val, x_val, y_val,
                number_simulation,
                extract_name
            )

    else:
        # Get specific flowdepth
        water_extraction(
            number_simulation,
            extract_name
        )

        if filter:
            # Remove river
            river_filter(
                number_simulation,
                extract_name
            )

            # Convert to and untransform polygons - filter river
            polygon_bathy_untransformation(
                angle_val, x_val, y_val,
                number_simulation,
                extract_name, True
            )

        else:
            # Convert to and untransform polygons
            polygon_bathy_untransformation(
                angle_val, x_val, y_val,
                number_simulation,
                extract_name
            )


def bathy_untransformation_parallelism(
    extract_name,
    ran_bathy_trans,
    kind, para_name,
    num_processes,
    filter=False
):
    """
    @Definition:
                A function to extract, convert raster into polygons, and un-transform them by applying nested multiprocessing
    @References:
                None.
    @Arguments:
                extract_name (string):
                                        Name of a specific output among all flood model outputs
                ran_bathy_trans (array):
                                        A big array of small 3D arrays of bathy ordinal values and transformation values (angle, x, y)
                kind (string):
                                        neal or rupp
                para_name (string):
                                        width, slope, flow, or combination
                num_processes (int):
                                        A number of process for the parallelism
                filter (boolean):
                                        True - filter river
                                        False - NOT filter river
    @Returns:
                None.
    """
    # Design a func to be used in multiprocessing
    func = partial(
        bathy_untransformation_simulation,
        extract_name,
        kind,
        para_name,
        filter
    )

    # Design the pool and execute the multiprocessing
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(func, [ran for ran in ran_bathy_trans])
    pool.close()
    pool.join()


