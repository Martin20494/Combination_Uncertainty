# Prepare packages -----------------------------------------------------------------------------------------------------
from folder import *                                # For paths of sub-folders

# Packages for transformation
from numba import guvectorize, float64              # For speeding up the time of the code running

# Packages for general data manipulation
import numpy as np                                  # For all calculation and data array/matrices manipulation
import pandas as pd                                 # For dealing with csv file within pandas dataframe

# For handling raster
import rioxarray as rxr                             # For manipulating pixel values, spatial attributes, and raster files
import xarray as xr                                 # For reading raster file

# Packages for geometry manipulation
import geopandas as gpd                             # For creating polygon
from shapely.geometry import Point                  # For creating point from coordinates of pixel middle

# Packages for searching depth values of point sample's coordinates
from shapely.strtree import STRtree                 # For building up a tree for searching points within this tree
from shapely import wkt                             # For reading geometry in csv files

# Packages for multiprocessing
from functools import partial                       # For containing many variables
import multiprocessing                              # For parallelising

# Packages for directory manipulation
import glob                                         # For collect a list of all files stored in a folder
from pathlib import Path                            # For manipulating paths' names
# ----------------------------------------------------------------------------------------------------------------------


# Remove all warnings  -------------------------------------------------------------------------------------------------
# Reference: https://numba.pydata.org/numba-doc/dev/reference/deprecation.html#suppressing-deprecation-warnings
from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning, NumbaWarning
import warnings

warnings.simplefilter('ignore', category=NumbaDeprecationWarning)
warnings.simplefilter('ignore', category=NumbaPendingDeprecationWarning)
warnings.simplefilter('ignore', category=NumbaWarning)
# ----------------------------------------------------------------------------------------------------------------------


# CONVERT RECTANGLE ARRAY INTO 3D XYZ ARRAY ############################################################################
def array_creation(data_array, value, switch=False):
    """
    @Definition:
                A function to create an array of coordinate
    @References:
                None
    @Arguments:
                data_array (array):
                                        Original array with full data
                value (string):
                                        Name of value - 'x' or 'y'
                switch (boolean):
                                        Switch the shape of array (shape x,y or shape y,x)
    @Returns:
                new_array (array):
                                        An array of coordinate
    """
    # Read x, y values into arrays
    arr_x = data_array.x.values
    arr_y = data_array.y.values

    if switch:
        # Create zero array
        new_array = np.zeros((arr_y.shape[0], arr_x.shape[0]))
    else:
        # Create zero array
        new_array = np.zeros((arr_x.shape[0], arr_y.shape[0]))

    # Get full number of x or y values
    if value == "x":
        for i in range(arr_x.shape[0]):
            for j in range(arr_y.shape[0]):
                new_array[j, i] = arr_x[i]
        return new_array

    else:
        for i in range(arr_x.shape[0]):
            for j in range(arr_y.shape[0]):
                new_array[j, i] = arr_y[j]
        return new_array

def xyz_array(
    dataset_z_rxr,
    switch=False
):
    """
    @Definition:
                A function to create an array of coordinate
    @References:
                None
    @Arguments:
                dataset_z_rxr (array):
                                    Rioxarray array that contains elevation or flowdepth values including padding
    @Returns:
                new_array (array):
                                        An array of coordinate
    """

    # Create full number of values of x, y, z coordinates
    array_x = array_creation(dataset_z_rxr, 'x', switch)
    array_y = array_creation(dataset_z_rxr, 'y', switch)
    array_z = dataset_z_rxr.isel(band=0).values

    # Flatten x, y, z arrays
    flatten_x = array_x.flatten()
    flatten_y = array_y.flatten()
    flatten_z = array_z.flatten()

    # Put all x, y, z into one array
    full_dataset = np.vstack((flatten_x, flatten_y, flatten_z)).transpose()

    return full_dataset

# END CONVERT RECTANGLE ARRAY INTO 3D XYZ ARRAY ########################################################################


# TRANSFORMATION #######################################################################################################
# CENTER CALCULATION ---------------------------------------------------------------------------------------------------
def center_calculation(lidar=True):
    """
    @Definition:
                A function to calculate the center of reference DEM raster which will be used in the whole process
    @References:
                https://gis.stackexchange.com/questions/104362/how-to-get-extent-out-of-geotiff
                https://rasterio.readthedocs.io/en/latest/quickstart.html
    @Arguments:
                lidar (boolean):
                                            True means doing rotation on LiDAR data
                                            False means doing unrotation on model outputs
    @Returns:
                center_func (tuple):
                                            A tuple of x, y coordinates of center raster
    """
    # Read file
    raster_reference_func = xr.open_dataset(fr"{original_lidar_path}\\padding\\padding.nc")

    if lidar:
        # Get z band
        raster_reference_z = raster_reference_func.z
        # Get the center bounding coordinates for LiDAR
        bounds = raster_reference_z.rio.bounds()
        center_x_func = (bounds[0] + bounds[2]) / 2
        center_y_func = (bounds[1] + bounds[3]) / 2
        center_func = np.array([center_x_func, center_y_func])

    else:
        # Get the center coordinates for DEMs
        center_func = (raster_reference_func.rio.shape[0] / 2, raster_reference_func.rio.shape[1] / 2)
    return center_func

# END CENTER CALCULATION -----------------------------------------------------------------------------------------------


# ROTATION -------------------------------------------------------------------------------------------------------------
# Create a command for guvectorize() decorator
# In that, float64[:,:] stands for the format of the array and float64 stands for the format of other parameters
# (m,n) signature stands for the matrix of the array and () signature stands for other parameters
gu_rotation = guvectorize([(float64[:, :], float64, float64, float64, float64, float64[:, :])],
                          '(m,n),(),(),(),()->(m,n)')

def point_rotation(coordinates_func, angle, center_x_func, center_y_func, clockwise, new_coordinates_func):
    """
    @Definition:
                A function to calculate the rotated coordinates of lidar data
    @References:
                https://www.youtube.com/watch?v=RqZH-7hlI48
                https://stackoverflow.com/questions/14607640/rotating-a-vector-in-3d-space
                https://stackoverflow.com/questions/5954603/transposing-a-1d-numpy-array
                https://en.wikipedia.org/wiki/Rotation_matrix
                https://math.stackexchange.com/questions/270194/how-to-find-the-vertices-angle-after-rotation

                https://github.com/numba/numba/issues/3312
                https://numba.pydata.org/numba-doc/latest/user/vectorize.html
                https://numba.pydata.org/numba-doc/latest/cuda/ufunc.html
                http://numba.pydata.org/numba-doc/0.20.0/reference/compilation.html
                http://numba.pydata.org/numba-doc/0.12/tutorial_numpy_and_numba.html
                https://numba.pydata.org/numba-doc/dev/reference/types.html
    @Arguments:
                coordinates_func (array):
                                        An array of the coordinates of the point will be rotated
                angle (int or float):
                                        The value of angle to rotate
                center_x_func (float):
                                        Coordinate value of x center.
                                        The x center here was used from the center of reference DEM without padding
                center_y_func (float):
                                        Coordinate value of x center.
                                        The x center here was used from the center of reference DEM without padding
                clockwise (string):
                                        Rotating the points in clockwise (1) or anti_clockwise (0) directions
                new_coordinates_func (array):
                                        A new array of rotated x, y, z coordinates values of a point
    @Returns:
                (array):
                                        The function will return itself without the need of 'return' command
    """
    # Convert degree to radian and calculate cosine and sine
    radian = np.deg2rad(angle)
    cosine = np.cos(radian)
    sine = np.sin(radian)

    # Create a for loop to manipulate each row of the array
    for i in range(coordinates_func.shape[0]):
        # Do subtraction with center coordinates
        diff_x = coordinates_func[i, 0] - center_x_func
        diff_y = coordinates_func[i, 1] - center_y_func

        # Calculate the rotated point coordinates
        if clockwise == 0:  # Rotating in anti-clockwise direction
            new_coordinates_func[i, 0] = diff_x * cosine - diff_y * sine + center_x_func
            new_coordinates_func[i, 1] = diff_x * sine + diff_y * cosine + center_y_func
            new_coordinates_func[i, 2] = coordinates_func[i, 2]
        else:  # Rotating in clockwise direction
            new_coordinates_func[i, 0] = diff_x * cosine + diff_y * sine + center_x_func
            new_coordinates_func[i, 1] = diff_x * (-sine) + diff_y * cosine + center_y_func
            new_coordinates_func[i, 2] = coordinates_func[i, 2]

# Wrapping function to map later
wrapping_point_rotation = gu_rotation(point_rotation)


# TRANSLATION ----------------------------------------------------------------------------------------------------------
# Create a command for guvectorize() decorator
# In that, float64[:,:] stands for the format of the array and float64 stands for the format of other parameters
# (m,n) signature stands for the matrix of the array and () signature stands for other parameters
gu_translation = guvectorize([(float64[:, :], float64, float64, float64[:, :])], '(m,n),(),()->(m,n)')

# Create a point translation function
def point_translation(coordinates_func, x_translation_func, y_translation_func, new_coordinates_func):
    """
    @Definition:
                A function to calculate the translated coordinates of lidar data
    @References:
                https://www.youtube.com/watch?v=RqZH-7hlI48
                https://stackoverflow.com/questions/14607640/rotating-a-vector-in-3d-space
                https://stackoverflow.com/questions/5954603/transposing-a-1d-numpy-array
                https://en.wikipedia.org/wiki/Rotation_matrix
                https://math.stackexchange.com/questions/270194/how-to-find-the-vertices-angle-after-rotation

                https://github.com/numba/numba/issues/3312
                https://numba.pydata.org/numba-doc/latest/user/vectorize.html
                https://numba.pydata.org/numba-doc/latest/cuda/ufunc.html
                http://numba.pydata.org/numba-doc/0.20.0/reference/compilation.html
                http://numba.pydata.org/numba-doc/0.12/tutorial_numpy_and_numba.html
                https://numba.pydata.org/numba-doc/dev/reference/types.html
    @Arguments:
                coordinates_func:
                (array)
                                        An array of the coordinates of the point will be rotated
                x_translation_func:
                (int or float)
                                        Distances to translate x coordinates values
                y_translation_func:
                (int or float)
                                        Distances to translate y coordinates values
                new_coordinates_func:
                (array)
                                        A new array of translated x, y, z coordinates values of a point
    @Returns:
               (array)
                                        The function will return itself without the need of 'return' command
    """
    for i in range(coordinates_func.shape[0]):
        new_coordinates_func[i, 0] = coordinates_func[i, 0] + x_translation_func
        new_coordinates_func[i, 1] = coordinates_func[i, 1] + y_translation_func
        new_coordinates_func[i, 2] = coordinates_func[i, 2]

# Wrapping function to map later
wrapping_point_translation = gu_translation(point_translation)
# END TRANSLATION ----------------------------------------------------------------------------------------------------
# END TRANSFORMATION ###################################################################################################


# POINT SAMPLE #########################################################################################################
def clip_padding_xyzdataset(
    dataset
):
    """
    @Definition:
                A function to clip 3D xyz array
    @References:
                None.
    @Arguments:
                dataset (array):
                                    An array with x, y, z values or xyz dataset
    @Returns:
                adjusted_dataset_clip2 (3D array):
                                    A dataset without padding.
                                    The coordinates are adjusted 0.000001 degree and meter for value extraction
    """
    # Get boundary coordinates
    raster_origin = rxr.open_rasterio(fr"{original_lidar_path}\\no_padding\\no_padding.nc")
    xmin, ymin, xmax, ymax = raster_origin.z.rio.bounds()

    # Calculate coordinates of center point
    center_point = center_calculation(True)
    center_x = center_point[0]  # Extract x coordinate of center point
    center_y = center_point[1]  # Extract y coordinate of center point

    # if clipping using rectangle shape
    dataset_clip = dataset[(xmin <= dataset[:, 0])
                           & (xmax >= dataset[:, 0])
                           & (ymin <= dataset[:, 1])
                           & (ymax >= dataset[:, 1])]

    # Adjust x and y to get flowdepth values later (to avoid the case one point with two flowdepth values)
    # Rotate -0.000001 degree
    adjusted_dataset_clip1 = wrapping_point_rotation(dataset_clip, -0.000001, center_x, center_y, 0)
    # Translate -0.000001 meter
    adjusted_dataset_clip2 = adjusted_dataset_clip1.copy()
    adjusted_dataset_clip2[:, 0] = adjusted_dataset_clip1[:, 0] - 0.000001
    adjusted_dataset_clip2[:, 1] = adjusted_dataset_clip1[:, 1] - 0.000001
    adjusted_dataset_clip2[:, 2] = adjusted_dataset_clip1[:, 2]

    return adjusted_dataset_clip2

def point_sample_generation(
    switch=False
):
    """
    @Definition:
                A function to create a point sample file. The coordinates will be extracted from this file
                to collect the elevation data with the same coordinates in all simulations
    @References:
                https://geopandas.org/docs/reference/api/geopandas.GeoDataFrame.to_crs.html
                https://shapely.readthedocs.io/en/stable/manual.html
                https://geopandas.org/docs/user_guide/io.html
                https://sgillies.net/2014/01/18/getting-shapes-of-raster-features-with-rasterio.html
    @Arguments:
                extract_name (string):
                                        Name of a specific output among all flood model outputs
                number_simulation (string):
                                        A string to identify the order of simulation (should be angle, x, y)
                switch (boolean):
                                        Switch the shape of array (shape x,y or shape y,x)
    @Returns:
                point_df (geopandas DataFrame):
                                        A geospatial dataframe containing coordinates (geometry) of point sample
    """
    # Get dataset x rioxarray
    dataset_full_rxr = rxr.open_rasterio(
        fr"{original_lidar_path}\\padding\\padding.nc"
    )
    dataset_z_rxr = dataset_full_rxr.z

    # Get xyz dataset and clip the padding
    raster_xyz = xyz_array(dataset_z_rxr, switch=switch)
    clipped_padding_xyz = clip_padding_xyzdataset(raster_xyz)

    # Convert x, y coordinates array into shapely geometry
    # General idea here is to convert pixel middle point (containing x, y coordinates and elevation data)
    # to shapely geometry Point (only contains x, y coordinates)
    point_geo_values = [
        Point(clipped_padding_xyz[i, 0], clipped_padding_xyz[i, 1]) for i in range(clipped_padding_xyz.shape[0])
    ]

    # Develop geopandas dataframe
    data_coords = {
        "x_coord": clipped_padding_xyz[:, 0],
        "y_coord": clipped_padding_xyz[:, 1]
    }
    point_df = gpd.GeoDataFrame(
        data=data_coords,
        geometry=point_geo_values,
        crs=2193
    )

    return point_df

# END POINT SAMPLE #####################################################################################################



# DEPTH VALUES #########################################################################################################
def get_water_values(point_sample_csv, water_file):
    """
    @Definition:
                A function to extract flood model outputs (water depth or water surface elevation) at given coordinates
                from any geometry files
    @References:
                https://gis.stackexchange.com/questions/102933/more-efficient-spatial-join-in-python-without-qgis-arcgis-postgis-etc/103066#103066
                https://gis.stackexchange.com/questions/121469/get-shapefile-polygon-attribute-value-at-a-specific-point-using-python-e-g-via
                https://stackoverflow.com/questions/59030022/checking-whether-point-is-within-polygon-returns-wrong-results-in-shapely
                https://gis.stackexchange.com/questions/119919/maximizing-code-performance-for-shapely
                https://gis.stackexchange.com/questions/42931/rtree-python-polygon-index
                https://gis.stackexchange.com/questions/227474/rtree-spatial-index-does-not-result-in-faster-intersection-computation
                https://rtree.readthedocs.io/en/latest/tutorial.html
                https://sgillies.net/2014/01/18/getting-shapes-of-raster-features-with-rasterio.html
                https://stackoverflow.com/questions/20474549/extract-points-coordinates-from-a-polygon-in-shapely

                As rtree cannot be used with multiprocessing, STRtree should be used instead

                https://gis.stackexchange.com/questions/353619/shapely-with-rtree-versus-strtree
                https://shapely.readthedocs.io/en/stable/manual.html
                https://gis.stackexchange.com/questions/396615/shapely-geometry-how-to-preserve-refrence-to-original-feature
    @Arguments:
                point_sample_csv (geopandas DataFrame):
                                        A geospatial dataframe contains point sample's coordinates
                water_file (string):
                                        A directory of a simulation csv file of flood model outputs (water depth or
                                        water surface elevation)
    @Returns:
                new_array (array):
                                        An array of coordinate
    """
    # Get the files
    infile_csv = pd.read_csv(water_file, engine='pyarrow')
    infile_csv['geometry'] = infile_csv['geometry'].apply(wkt.loads)
    infile_csv = gpd.GeoDataFrame(infile_csv, crs='epsg:2193')

    # Convert dataframe into lists
    list_file_polygon = infile_csv['geometry'].tolist()
    list_file_point = point_sample_csv['geometry'].tolist()

    # Build up the tree
    tree = STRtree(list_file_polygon)

    # Get index (id) of polygon list
    index_by_id = dict((id(pt), i) for i, pt in enumerate(list_file_polygon))

    # Empty list
    water_list = []

    # Get intersected tuple
    for num_point in range(len(list_file_point)):
        intersect_tuple = [(index_by_id[id(pts)], pts.wkt) for pts in tree.query(list_file_point[num_point]) if
                           list_file_point[num_point].within(pts)]
        water_list.append(infile_csv.iloc[intersect_tuple[0][0]]['depth'])

    return water_list


def get_water_parallelism(
    num_processes,
    extract_name
):
    """
    @Definition:
                A function to extract flowdepth at given coordinates from any geometry files by multiprocessing
    @References:
                https://stackoverflow.com/questions/43175382/python-create-a-pandas-data-frame-from-a-list
    @Arguments:
                num_processes (int):
                                        A number of process for the parallelism
                extract_name (string):
                                        Name of a specific output among all flood model outputs
    @Returns:
                new_array (array):
                                        An array of coordinate
    """
    # Get necessary parameters -----------------------
    # Choose output
    if extract_name == 'out.max':
        untransformed_water = untransformed_wd
        csv_untransformation = wd_csv_untransformation
    elif extract_name == 'out.mxe':
        untransformed_water = untransformed_wse
        csv_untransformation = wse_csv_untransformation
    else:
        untransformed_water = untransformed_elev
        csv_untransformation = elev_csv_untransformation

    # Get point sample dataframe
    point_sample_df = point_sample_generation(False)

    # Get all csv folders
    all_csv_folders = glob.glob(fr"{untransformed_water}\\untransformed_*")

    # Get all column names
    column_names = [Path(all_csv_folders[i]).stem for i in range(len(all_csv_folders))]

    # Get flowdepth list -----------------------------

    # List all parameters
    point_sample_csv = point_sample_df

    # Design func parameters
    func = partial(
        get_water_values,
        point_sample_csv,
    )

    # Design the pool and execute the multiprocessing
    with multiprocessing.Pool(processes=num_processes) as pool:
        water_df = pd.DataFrame(
            pool.map(func, all_csv_folders),
            index=column_names
        ).T
    pool.close()
    pool.join()

    # Add x coordinate column
    water_df.insert(0, 'y_coord', value=point_sample_csv['y_coord'])
    water_df.insert(0, 'x_coord', value=point_sample_csv['x_coord'])

    # Write out file
    water_df.to_csv(fr"{csv_untransformation}\\all_simulations.csv", index=False)

    return water_df

# END DEPTH VALUES #####################################################################################################