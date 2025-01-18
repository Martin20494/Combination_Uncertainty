# Prepare packages -----------------------------------------------------------------------------------------------------
# Package for paths manipulation
from folder import *                                # For paths of sub-folders
import glob                                         # For getting all files' names in a certain path
import os                                           # For manipulating paths and to execute commands
import pathlib                                      # For manipulating the directory path
import shutil                                       # For copying file/folder
import sys

# Package for reading las/laz file and handling lidar point cloud
import numpy as np                                  # For all calculation and data array/matrices manipulation
import pdal                                         # For handling LiDAR point cloud data
import json                                         # For creating json text data format

# Packages for transformation
from numba import guvectorize, float64              # For speeding up the time of the code running

# Packages for raster
import xarray as xr                                 # For reading raster file
import rioxarray as rxr                             # For reading raster file and get size

# Packages for unrotating and untranslating
from osgeo import gdal                              # For manipulating rasters (calculating centers)
from shapely.geometry import Polygon                # For creating polygons to change raster values
import geopandas as gpd                             # For manipulating shape files

# Packages for multiprocessing
from functools import partial                       # For containing many variables
import multiprocessing                              # For parallelising

# ----------------------------------------------------------------------------------------------------------------------


# Remove all warnings --------------------------------------------------------------------------------------------------
# Reference: https://numba.pydata.org/numba-doc/dev/reference/deprecation.html#suppressing-deprecation-warnings
from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning, NumbaWarning
import warnings

warnings.simplefilter('ignore', category=NumbaDeprecationWarning)
warnings.simplefilter('ignore', category=NumbaPendingDeprecationWarning)
warnings.simplefilter('ignore', category=NumbaWarning)
# ----------------------------------------------------------------------------------------------------------------------



# NESTED PARALLELISM --------------------------------------------------------------------------------------------------
"""
@Definition:
            A class to perform nested parallelism
@References:
            https://stackoverflow.com/questions/50937362/multiprocessing-on-python-3-jupyter
            https://stackoverflow.com/questions/66420735/simple-multiprocessing-pool-hangs-in-jupyter-notebook
            https://stackoverflow.com/questions/23641475/multiprocessing-working-in-python-but-not-in-ipython/23641560#23641560
            https://stackoverflow.com/questions/5442910/how-to-use-multiprocessing-pool-map-with-multiple-arguments
            https://stackoverflow.com/questions/20886565/using-multiprocessing-process-with-a-maximum-number-of-simultaneous-processes
            
            https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
            https://www.geeksforgeeks.org/partial-functions-python/
"""

class NoDaemonProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class NoDaemonContext(type(multiprocessing.get_context())):
    Process = NoDaemonProcess

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class MyPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(MyPool, self).__init__(*args, **kwargs)

# END NESTED PARALLELISM ----------------------------------------------------------------------------------------------


# READING LAS/LAZ FILES OF TILES --------------------------------------------------------------------------------------
def read_las_file(filename_tile):
    """
    @Definition:
                A function to read the las/laz file into arrays
    @References:
                https://pythonhosted.org/laspy/file.html
                https://pythonhosted.org/laspy/tut_part_1.html
    @Arguments:
                filename_tile (string):
                                                Name of las/laz files of tiles
    @Returns:
                points_classification_func (array):
                                                An array includes classification information (int format)
                coordinates_func (array):
                                                An array includes x, y, z coordinates values of points as rows
    """
    # Set up horizontal and vertical crs
    h_crs = 2193
    v_crs = 7839

    # Write las/las file into arrays
    pdal_pipeline_instructions = [{"type": "readers.las", "filename": fr"{filename_tile}"},
                                  {"type": "filters.reprojection", "in_srs": f"EPSG:{h_crs}+{v_crs}",
                                   "out_srs": f"EPSG:{h_crs}+{v_crs}"}]

    pdal_pipeline = pdal.Pipeline(json.dumps(pdal_pipeline_instructions))
    pdal_pipeline.execute()

    # Call out arrays
    points_full_func = pdal_pipeline.arrays  # note is shape [1,nx,ny]

    # Assign x, y , z (values in meters)
    x_func = points_full_func[0]["X"]
    y_func = points_full_func[0]["Y"]
    z_func = points_full_func[0]["Z"]

    # Get classification
    point_classification_func = points_full_func[0]['Classification']

    # Write x, y, z into arrays with each row as (x, y, z) (meters as unit)
    coordinates_func = np.vstack((x_func, y_func, z_func)).transpose().astype('float64')

    return point_classification_func, coordinates_func


# CENTER CALCULATION ###################################################################################################
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

# END CENTER CALCULATION ###############################################################################################


# ROTATION #############################################################################################################
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


# TRANSLATION ##########################################################################################################
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



# WRITING TRANSFORMED LAS/LAZ FILES ####################################################################################
def writing_las_file(point_classification_func, number_simulation, transformed_array,
                     filename_code, lidar_dataset_name):
    """
    @Definition:
                A function to create a new lidar las/laz file the same as the old lidar las/laz file with different coordinates
    @References:
                https://pdal.io/tutorial/las.html
    @Arguments:
                point_classification_func (array):
                                            An array contains points' information from original tiles
                number_simulation (int):
                                            Ordinal number of simulation
                transformed_array (array):
                                            A transformed array
                filename_code (string):
                                            Code of file name (the same as original lidar tiles' names)
                lidar_dataset_name (string):
                                            LiDAR dataset name
    @Returns:
                None.
    """
    # Set up horizontal and vertical crs
    h_crs = 2193
    v_crs = 7839

    # Output file
    pathlib.Path(fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}\\{lidar_dataset_name}").mkdir(parents=True, exist_ok=True)
    outfile = fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}\\{lidar_dataset_name}\\{filename_code}.laz"

    print(outfile)

    # Get the shape of transformed LiDAR array
    lidar_arr_shape = len(point_classification_func)

    # Create empty transformed LiDAR array
    lidar_arr = np.empty([lidar_arr_shape], dtype=[('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('Classification', 'u1')])

    # Overwrite the X, Y, and Z values in the points array with the transformed values
    lidar_arr['X'] = (transformed_array[:, 0]).flatten()
    lidar_arr['Y'] = (transformed_array[:, 1]).flatten()
    lidar_arr['Z'] = (transformed_array[:, 2]).flatten()
    lidar_arr['Classification'] = point_classification_func

    # Read river parameters file
    with open(fr"{other_data}/general_parameters.json", 'r') as general_parameters_file:
        general_parameters = json.load(general_parameters_file)

    # Save the file
    pdal_pipeline_instructions = [
        {
            "type": "writers.las",
            "scale_x": 0.0001,
            "scale_y": 0.0001,
            "offset_x": general_parameters['offset_x'],    # for Waikanae - 1700000, Buller - 1400000, Esk - 1900000
            "offset_y": general_parameters['offset_y'],    # for Waikanae - 5400000, Buller - 5300000, Esk - 5600000
            "a_srs": f"EPSG:{h_crs}+{v_crs}",
            "filename": str(outfile),
            "compression": "laszip"
        }
    ]

    # Run
    pdal_pipeline = pdal.Pipeline(json.dumps(pdal_pipeline_instructions), [lidar_arr])
    pdal_pipeline.execute()
    return outfile

# OTHER NECESSARY FUNCTIONS ############################################################################################
def tile_index_polygon(tile_array_coordinate):
    """
    @Definition:
                A function to create transformed tile index polygon for each original tile
    @References:
                None.
    @Arguments:
                tile_array_coordinate (array):
                                        An array of each tile's coordinate (x, y, z)
    @Returns:
                tile_boundary_polygon (polygon):
                                        A polygon represents the boundary of the LiDAR tiles
    """
    # Get xmin, xmax, ymin, ymax for the index
    x_min_tile = np.min(tile_array_coordinate[:, 0])
    x_max_tile = np.max(tile_array_coordinate[:, 0])
    y_min_tile = np.min(tile_array_coordinate[:, 1])
    y_max_tile = np.max(tile_array_coordinate[:, 1])

    # Design boundary coordinates
    tile_boundary = np.array([
        [x_min_tile, y_max_tile],
        [x_max_tile, y_max_tile],
        [x_max_tile, y_min_tile],
        [x_min_tile, y_min_tile],
        [x_min_tile, y_max_tile]
    ]).astype('float64')

    # Convert to polygon
    tile_boundary_polygon = Polygon(tile_boundary)

    return tile_boundary_polygon

def get_url(lidar_dataset_name):
    """
    @Definition:
                A function to extract the URL of each tile from original tile index file
    @References:
                None.
    @Arguments:
                lidar_dataset_name (string):
                                        LiDAR name
    @Returns:
                url_file (list):
                                URL of the specific tile
    """
    # Read the shape file to have geopandas dataframe
    full_file = gpd.read_file(
        fr"{original_lidar_path}\\{lidar_dataset_name}\\{lidar_dataset_name}_TileIndex.zip")

    # Get list of tiles names
    list_tile_paths = glob.glob(fr"{original_lidar_path}\\{lidar_dataset_name}\*.laz")
    length_list = len(list_tile_paths)
    list_tile_names = [pathlib.Path(list_tile_paths[name]).stem for name in range(length_list)]

    url_file = []

    # Collect point classification and coordinate array
    for each_tile in range(length_list):
        # Get the row with the file name the same as given 'filename_tile'
        file_info = full_file[full_file[full_file.columns[0]] == f"{list_tile_names[each_tile]}.laz"]

        # Get the index of that row
        url_index = file_info.index[0]

        # Use the extracted index to get the correct URL
        url_file.append(full_file['URL'][url_index])

    return url_file

def get_tile_files(lidar_dataset_name):
    """
    @Definition:
                A function to get tiles' information including path, length, and name
    @References:
                None.
    @Arguments:
                lidar_dataset_name (string):
                                            LiDAR name
    @Returns:
                (list):
                                            A list includes a list of path, number presenting its length, and a list
                                            of tile's name
    """
    # Get list of tiles names
    list_tile_paths_func = glob.glob(fr"{original_lidar_path}\\{lidar_dataset_name}\*.laz")
    length_list_func = len(list_tile_paths_func)
    list_tile_names_func = [pathlib.Path(list_tile_paths_func[name]).stem for name in range(length_list_func)]

    return [list_tile_paths_func, length_list_func, list_tile_names_func]

# END OTHER NECESSARY FUNCTION ---------------------------------------------------------------------------------------

# TRANSFORMATION ------------------------------------------------------------------------------------------------------
def transformed_tiles_generation(
        angle_func, x_translation_func, y_translation_func,
        center_x_func, center_y_func,
        number_simulation,
        lidar_dataset_name,
        list_tile_files,
        each_tile):
    """
    @Definition:
                A function to transform each tile and write out las file
    @References:
                None.
    @Arguments:
                angle_func, x_translation_func, y_translation_func (float):
                            Values to rotate and translate
                center_x_func (float):
                            X coordinate of original/reference DEM
                center_y_func (float):
                            Y coordinate of original/reference DEM
                number_simulation (string):
                            A string to identify the order of simulation (should be angle, x, y)
                lidar_dataset_name (string):
                            Name of the LiDAR dataset from OpenTopography
                list_tile_files (list):
                            A list of two elements. First is tiles' paths. Second is tiles' names
                each_tile (int):
                            An ordinal number of each tile (iterating variable generated from multiprocessing)
    @Returns:
                None.
    """

    # Get list of tiles names
    list_tile_paths = list_tile_files[0]
    list_tile_names = list_tile_files[1]

    # Main tasks
    # Read each tile
    points_tiles, coordinates_tiles = read_las_file(list_tile_paths[each_tile])

    # Transform tile
    rotated_array_func = wrapping_point_rotation(coordinates_tiles,
                                                 angle_func, center_x_func, center_y_func, 0)
    transformed_array_func = wrapping_point_translation(rotated_array_func, x_translation_func, y_translation_func)

    # Write LiDAR tiles into las/laz file
    writing_las_file(points_tiles, number_simulation,
                     transformed_array_func, list_tile_names[each_tile],
                     lidar_dataset_name)

    # Write tile index polygon
    tile_polygon = tile_index_polygon(transformed_array_func)

    return tile_polygon

# END TRANSFORMATION --------------------------------------------------------------------------------------------------


# NESTED PARALLELISM --------------------------------------------------------------------------------------------------
def transformation_performance(
        center_x_func,
        center_y_func,
        lidar_dataset_name,
        tile_files,
        num_processes,
        url_list_file,
        ran_trans_i):
    """
    @Definition:
                A function to execute a choice of transformation by applying transformation on all tiles with
                multiprocessing
    @References:
                https://stackoverflow.com/questions/23641475/multiprocessing-working-in-python-but-not-in-ipython/23641560#23641560
                https://stackoverflow.com/questions/66420735/simple-multiprocessing-pool-hangs-in-jupyter-notebook
                https://stackoverflow.com/questions/50937362/multiprocessing-on-python-3-jupyter
                https://stackoverflow.com/questions/25553919/passing-multiple-parameters-to-pool-map-function-in-python/25553970#25553970
                https://stackoverflow.com/questions/25553919/passing-multiple-parameters-to-pool-map-function-in-python/25553970#25553970
                https://www.youtube.com/watch?v=PcJZeCEEhws
    @Arguments:
                center_x_func (float):
                                        X coordinate of original/reference DEM
                center_y_func (float):
                                        Y coordinate of original/reference DEM
                lidar_dataset_name (string):
                                        Name of the LiDAR dataset from OpenTopography
                tile_files (list):
                                        A list of 3 elements generated from function <get_tile_files>. First is
                                        tiles' paths. Second is a quantity of tiles. Third is tiles' names
                num_processes (int):
                                        A number of processes for paralellism
                url_list_file (list):
                                        A list of strings of URLs where the tiles are stored and can be downloaded
                ran_trans_i (array):
                                        A 3D array contains values of angle, x, and y coordinates of points in tiles
                                        (iterating variable generated from multiprocessing)
    @Returns:
                None
    """

    # Get values
    angle_val = ran_trans_i[0]
    x_val = ran_trans_i[1]
    y_val = ran_trans_i[2]

    # List all parameters
    angle_func = angle_val
    x_translation_func = x_val
    y_translation_func = y_val
    center_x_func = center_x_func
    center_y_func = center_y_func
    number_simulation = f"angle_{angle_val}_x_{x_val}_y_{y_val}"
    lidar_dataset_name = lidar_dataset_name
    list_tile_files = [tile_files[0], tile_files[2]]

    # Design func parameters
    func = partial(
        transformed_tiles_generation,
        angle_func, x_translation_func, y_translation_func,
        center_x_func, center_y_func,
        number_simulation,
        lidar_dataset_name,
        list_tile_files
    )

    # List to iterate
    iterating_list = list(range(tile_files[1]))

    # Multiprocessing
    with multiprocessing.Pool(processes=num_processes) as pool:
        tile_index_list = pool.map(func, iterating_list)
    pool.close()
    pool.join()

    # Tile indices generation
    # - Read file
    full_file = gpd.read_file(glob.glob(fr"{original_lidar_path}\\{lidar_dataset_name}\\*.zip")[0])
    # - Tile dictionary
    tile_dict = {
        f"{full_file.columns[0]}": [os.path.basename(tile_files[0][name]) for name in range(tile_files[1])],
        "URL": url_list_file
    }
    # - Create dataframe
    tile_data_index = gpd.GeoDataFrame(
        data=tile_dict,
        geometry=tile_index_list,
        crs=2193
    )
    # - Create compressed shapefile
    tile_index_path = pathlib.Path(fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}\\{lidar_dataset_name}\\{lidar_dataset_name}_TileIndex")
    tile_data_index.to_file(tile_index_path)
    shutil.make_archive(base_name=tile_index_path, format='zip', root_dir=tile_index_path)
    shutil.rmtree(tile_index_path)


def transformation_parallelism(
        center_x_func,
        center_y_func,
        lidar_dataset_name,
        tile_files,
        num_processes_1,
        url_list_file,
        ran_trans,
        num_processes_2=1
):
    """
    @Definition:
                A function to execute multiple choices of transformation by applying nested multiprocessing. Default
                is 1
    @References:
                https://stackoverflow.com/questions/23641475/multiprocessing-working-in-python-but-not-in-ipython/23641560#23641560
                https://stackoverflow.com/questions/66420735/simple-multiprocessing-pool-hangs-in-jupyter-notebook
                https://stackoverflow.com/questions/50937362/multiprocessing-on-python-3-jupyter
                https://stackoverflow.com/questions/25553919/passing-multiple-parameters-to-pool-map-function-in-python/25553970#25553970
                https://stackoverflow.com/questions/25553919/passing-multiple-parameters-to-pool-map-function-in-python/25553970#25553970
                https://www.youtube.com/watch?v=PcJZeCEEhws
    @Arguments:
                center_x_func (float):
                                        X coordinate of original/reference DEM
                center_y_func (float):
                                        Y coordinate of original/reference DEM
                lidar_dataset_name (string):
                                        Name of the LiDAR dataset from OpenTopography
                tile_files (list):
                                        A list of 3 elements generated from function <get_tile_files>. First is
                                        tiles' paths. Second is a quantity of tiles. Third is tiles' names
                num_processes_1 (int):
                                        A number of processes for the first parallelism
                url_list_file (list):
                                        A list of strings of URLs where the tiles are stored and can be downloaded
                ran_trans (array):
                                        A big array of small 3D arrays of transformation values (angle, x, y)
                num_processes_2 (int):
                                        A number of process for the second parallelism. Default is 1
    @Returns:
                None
    """

    # List parameters. Assign the values to the same arguments' names of <transformation_performance> function
    center_x_func = center_x_func
    center_y_func = center_y_func
    lidar_dataset_name = lidar_dataset_name
    tile_files = tile_files
    num_processes = num_processes_1
    url_list_file = url_list_file

    # Design a func to be used in multiprocessing (multiprocessing will used this on behalf of
    # <transformation_performance>
    func = partial(
        transformation_performance,
        center_x_func, center_y_func,
        lidar_dataset_name,
        tile_files,
        num_processes,
        url_list_file
    )

    # Design the pool and execute the multiprocessing
    pool = MyPool(num_processes_2)
    pool.map(func, [ran for ran in ran_trans])
    pool.close()
    pool.join()
    multiprocessing.freeze_support()

# END NESTED PARALLELISM ----------------------------------------------------------------------------------------------