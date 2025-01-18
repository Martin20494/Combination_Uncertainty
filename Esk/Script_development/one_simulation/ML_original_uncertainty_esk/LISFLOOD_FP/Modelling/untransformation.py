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
        fr"{transformed_FPoutput_path}\\transformed_{number_simulation}\\{extract_name}"
    )

    # Add crs
    new_water = water_asc.rio.write_crs(2193)

    # Write out new flowdepth file
    if extract_name == 'out.max':
        new_water.rio.to_raster(fr"{extracted_wd}\\untransformed_{extract_name}_{number_simulation}.nc")
    else:
        new_water.rio.to_raster(fr"{extracted_wse}\\untransformed_{extract_name}_{number_simulation}.nc")


def polygon_untransformation(
    angle_func, x_translation_func, y_translation_func,
    number_simulation,
    extract_name
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
    @Returns:
                None.
    """
    # Choose the outputs
    if extract_name == 'out.max':
        extracted_water = extracted_wd
        untransformed_water = untransformed_wd
    elif extract_name == 'out.mxe':
        extracted_water = extracted_wse
        untransformed_water = untransformed_wse
    else:
        extracted_water = transformed_dem_nc_path
        untransformed_water = untransformed_elev


    # Get new values for translation
    x_raster = x_translation_func / 10 * (-1)
    y_raster = y_translation_func / 10

    # Extract array from flowdepth raster
    if extract_name == 'elev':
        raster_poly = rxr.open_rasterio(fr"{extracted_water}\\generated_dem_transformed_{number_simulation}.nc")
        raster_array = raster_poly.z.values
        raster_transform = raster_poly.z.rio.transform()
        raster_crs = raster_poly.z.rio.crs

    else:
        # Call out the file filterred the sea to work on
        raster_poly = rasterio.open(fr"{extracted_water}\\untransformed_{extract_name}_{number_simulation}.nc")
        raster_array = raster_poly.read(1)
        raster_transform = raster_poly.transform
        raster_crs = raster_poly.crs

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
        fr"{untransformed_water}\\untransformed_{extract_name}_{number_simulation}.csv", index=False
    )


def untransformation_simulation(
    extract_name,
    ran_trans_i,
):
    """
    @Definition:
                A function to extract, convert raster into polygons, and un-transform them
    @References:
                None.
    @Arguments:
                extract_name (string):
                                        Name of a specific output among all flood model outputs
                ran_trans_i (array):
                                        A 3D array contains values of angle, x, and y coordinates of points in tiles
                                        (iterating variable generated from multiprocessing)
    @Returns:
                None.
    """
    # Get values
    angle_val = ran_trans_i[0]
    x_val = ran_trans_i[1]
    y_val = ran_trans_i[2]
    number_simulation = f"angle_{angle_val}_x_{x_val}_y_{y_val}"

    if extract_name == 'elev':
        # Convert to and untransform polygons
        polygon_untransformation(
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

        # Convert to and untransform polygons
        polygon_untransformation(
            angle_val, x_val, y_val,
            number_simulation,
            extract_name
        )

def untransformation_parallelism(
    extract_name,
    ran_trans,
    num_processes
):
    """
    @Definition:
                A function to extract, convert raster into polygons, and un-transform them by applying nested multiprocessing
    @References:
                None.
    @Arguments:
                extract_name (string):
                                        Name of a specific output among all flood model outputs
                ran_trans (array):
                                        A big array of small 3D arrays of transformation values (angle, x, y)
                num_processes (int):
                                        A number of process for the parallelism
    @Returns:
                None.
    """
    # List parameters
    extract_name = extract_name

    # Design a func to be used in multiprocessing
    func = partial(
        untransformation_simulation,
        extract_name
    )

    # Design the pool and execute the multiprocessing
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(func, [ran for ran in ran_trans])
    pool.close()
    pool.join()


