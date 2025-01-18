# Prepare packages -----------------------------------------------------------------------------------------------------
from folder import *                                        # For paths of sub-folders

# Package for paths manipulation
import os                                                   # For manipulating paths and to execute commands
import pathlib                                              # For manipulating the directory path
import glob                                                 # For checking all files in a path
import shutil                                               # For copying file/folder

# Packages for transformation
from transformation import wrapping_point_rotation, \
                           wrapping_point_translation       # For transforming polygon boundaries
from geojsonTransformation import geom_geojson              # For transforming geometries

# Packages for manipulating tabular data
import pandas as pd                                         # For manipulating tabular data (e.g. dataframe)
import numpy as np                                          # For manipulating arrays/matrices

# Packages for manipulating spatial data (e.g. raster)
import xarray                                               # For creating and manipulating an array of raster
import rioxarray as rxr                                     # For manipulating spatial data under xarray array format
import rasterio                                             # For reading and manipulating spatial data
import rasterio.features                                    # For vectorising features in array
import json                                                 # For creating json text data format
from geofabrics import processor                            # For executing the conversion of LiDAR into a DEM raster

# Packages for manipulating geometries
import shapely.geometry                                     # For creating a polygon object
from shapely.geometry import Polygon                        # For creating polygons to change raster values
import geopandas as gpd                                     # For manipulating shape files

# Packages for changing values of raster
from valueChange import value_padding_change, value_sea_change, convert_to_asc
# ----------------------------------------------------------------------------------------------------------------------


# LIDAR-DERIVED DEMS ###################################################################################################
def transform_land_bathy(layer_number, path_out, ran_trans_i):
    """
    @Definition:
                A function to write out geojson file of transformed land and bahymetry contours
    @References:
                https://github.com/rosepearson/GeoFabrics
                https://stackoverflow.com/questions/20638040/glob-exclude-pattern


    @Arguments:
                layer_number (int):
                                    ID number of layer polygons from LINZ. Ex:
                                    https://data.linz.govt.nz/layer/50554-depth-contour-polyline-hydro-122k-190k/ (bathymetry contours - 50554)
                                    https://data.linz.govt.nz/layer/51559-nz-coastlines-and-islands-polygons-topo-1250k/ (costlines and islands polygons - 51559)
                path_out (string):
                                    Directory to write out file
                ran_trans_i (array):
                                    A 3D array contains values of angle, x, and y coordinates of points in tiles
                                    (iterating variable generated from multiprocessing)
    @Returns:
                None.
    """
    # Land/Bathymetry contour file is stored under zip file
    path_in = fr"{original_lidar_path}\\downloads\\vector\\padding\\{layer_number}.geojson"

    # # Path in
    # path_in = glob.glob(zip_path)[0]

    # Transform geometries
    geom_geojson(path_in, path_out, ran_trans_i)


def necessary_files(ran_trans_i):
    """
    @Definition:
                A function to generate necessary files
    @References:
                https://github.com/rosepearson/GeoFabrics
                https://stackoverflow.com/questions/20638040/glob-exclude-pattern
    @Arguments:
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

    # Create folder for writing out necessary files
    # DEM ------------
    folder_out_dem = fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}\\element_dem"
    pathlib.Path(fr"{folder_out_dem}").mkdir(parents=True, exist_ok=True)
    # ROUGHNESS ------
    folder_out_roughness = fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}\\element_roughness"
    pathlib.Path(fr"{folder_out_roughness}").mkdir(parents=True, exist_ok=True)

    # Get directory path of reference folder (folder stores original files)
    ref_path = pathlib.Path(fr"{original_lidar_path}\\padding")

    # Create path for all files but exclude catchment_boundary path
    filtered_ref_path = [x for x in ref_path.glob("**\*.geojson") if not x.name.startswith("catchment_boundary")]

    # Create transformed geometries and write out geojson files
    # from original files stored in 'element' folder of reference file
    for num in range(len(filtered_ref_path)):
        path_in = filtered_ref_path[num]
        path_out = fr"{folder_out_dem}\{pathlib.Path(path_in).stem}.geojson"
        geom_geojson(path_in, path_out, ran_trans_i)


    # Read river parameters file
    with open(fr"{other_data}/general_parameters.json", 'r') as general_parameters_file:
        general_parameters = json.load(general_parameters_file)

    # Create transformed geometries for land (layer number 51559) and bathymetry contours (layer number 50554)
    # from original files stored in '0_lidar_data'. These files are stored under zip shapefile
    # DEM ------------------------------------------------------------
    # Land file
    land_path_out = fr"{folder_out_dem}\\land.geojson"
    transform_land_bathy(general_parameters['land'], land_path_out, ran_trans_i)
    # Bathymetry file
    bathy_path_out = fr"{folder_out_dem}\\bathymetry_contours.geojson"
    transform_land_bathy(general_parameters['ocean_contours'], bathy_path_out, ran_trans_i)
    # rivernetwork.geojson
    rivernetwork_path_in = fr"{original_lidar_path}\\{general_parameters['network_file']}"
    rivernetwork_path_out = fr"{folder_out_dem}\\{pathlib.Path(rivernetwork_path_in).stem}.geojson"
    geom_geojson(rivernetwork_path_in, rivernetwork_path_out, ran_trans_i)
    # # flow_and_friction.csv.gz
    # flow_and_friction_gz_in = fr"{original_lidar_path}\\flow_and_friction.csv.gz"
    # flow_and_friction_gz_out = fr"{folder_out_dem}\\flow_and_friction.csv.gz"
    # shutil.copy2(flow_and_friction_gz_in, flow_and_friction_gz_out)

    # ROUGHNESS -------------------------------------------------------
    # Land file
    land_path_out = fr"{folder_out_roughness}\\land.geojson"
    transform_land_bathy(general_parameters['land'], land_path_out, ran_trans_i)
    # Bathymetry file
    bathy_path_out = fr"{folder_out_roughness}\\bathymetry_contours.geojson"
    transform_land_bathy(general_parameters['ocean_contours'], bathy_path_out, ran_trans_i)

def dem_raster(resolution_func, chunk_size_func, processor_func,
               number_simulation, padding_func, lidar_dataset_name):
    """
    @Definition:
                A function to create a raster file from a las/laz file
    @References:
                https://github.com/rosepearson/GeoFabrics
    @Arguments:
                resolution_func (int or float):
                                            Resolution value in meter
                chunk_size_func (int):
                                            Size value of chunk
                processor_func (int):
                                            Number of processor
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                padding_func (list):
                                            A list of x min, x max, y min, and y max
                lidar_dataset_name (string):
                                            LiDAR name
    @Returns:
                None.
    """

    # Name of output
    output_name = fr"generated_dem_transformed_{number_simulation}.nc"

    basepath = pathlib.Path(fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}")
    result_folder = 'element_dem'

    # Set crs
    h_crs = 2193
    v_crs = 7839

    # Bounding box
    x0 = padding_func[0]
    y0 = padding_func[1]
    x1 = padding_func[2]
    y1 = padding_func[3]
    catchment = shapely.geometry.Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    catchment = gpd.GeoSeries([catchment])
    catchment = catchment.set_crs(h_crs)
    catchment.to_file(basepath / result_folder / "catchment_boundary.geojson", crs=fr"EPSG:{h_crs}", driver="GeoJSON")

    # Design JSON instructions --------------------------------------------
    # Design JSON instructions
    instruction_json = {}

    # DEM
    instruction_json['dem'] = {
        # outputs
        "output": {
            "crs": {
                "horizontal": h_crs,
                "vertical": v_crs
            },
            "grid_params": {
                "resolution": resolution_func
            }
        },

        # processing
        "processing": {
            "chunk_size": chunk_size_func,
            "number_of_cores": processor_func
        },

        # apis
        "datasets": {
            "vector": {
                "linz": {}
            },
            "lidar": {
                "local": {
                    f"{lidar_dataset_name}": {
                        "crs": {
                            "horizontal": 2193,
                            "vertical": 7839
                        },
                        "folder_path": str(basepath / f"{lidar_dataset_name}")
                    }
                }
            }
        },

        # data paths
        "data_paths": {
            "local_cache": str(basepath),
            "lidar_buffer": 5,
            "subfolder": fr"{result_folder}",
            "extents": "catchment_boundary.geojson",

            'land': 'land.geojson',
            'ocean_contours': 'bathymetry_contours.geojson',
            
            'rivers': [{
                'extents': 'river_polygon.geojson',
                'elevations': 'river_bathymetry.geojson'
            }],
            'raw_dem': 'raw_dem.nc',

            # Result
            "result_dem": fr"{transformed_dem_nc_path}\\{output_name}"
        },

        # general
        "general": {
            # For lidar
            "set_dem_shoreline": True,
            "drop_offshore_lidar": False,
            "lidar_classification_to_keep": [2, 9],
            "interpolation": {
                'no_data': 'nearest',
                'lidar': "idw"
            },
            'z_labels': {
                'ocean': 'valdco',
                'rivers': 'bed_elevation_Rupp_and_Smart'
            }
        }
    }

    # Save the instructions
    with open(basepath / result_folder / "instructions.json", "w") as instruction:
        json.dump(instruction_json, instruction)

    runner = processor.RawLidarDemGenerator(instruction_json['dem'])
    runner.run()
    runner = processor.HydrologicDemGenerator(instruction_json['dem'])
    runner.run()
# END LIDAR-DERIVED DEMS ###############################################################################################


# ROUGHNESS ############################################################################################################
def roughness_raster(resolution_func, chunk_size_func, processor_func,
                     number_simulation, padding_func, lidar_dataset_name):
    """
    @Definition:
                A function to create a raster file from a las/laz file
    @References:
                https://github.com/rosepearson/GeoFabrics
    @Arguments:
                resolution_func (int or float):
                                            Resolution value in meter
                chunk_size_func (int):
                                            Size value of chunk
                processor_func (int):
                                            Number of processor
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                padding_func (list):
                                            A list of x min, x max, y min, and y max
                lidar_dataset_name (string):
                                            LiDAR name
    @Returns:
                None.
    """

    # Name of output
    output_roughness = fr"generated_roughness_transformed_{number_simulation}.nc"
    output_dem = fr"generated_dem_transformed_{number_simulation}.nc"

    basepath = pathlib.Path(fr"{transformed_lidar_path}\\transformed_lidar_{number_simulation}")
    result_folder = 'element_roughness'

    # Set crs
    h_crs = 2193
    v_crs = 7839

    # Bounding box
    x0 = padding_func[0]
    y0 = padding_func[1]
    x1 = padding_func[2]
    y1 = padding_func[3]
    catchment = shapely.geometry.Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    catchment = gpd.GeoSeries([catchment])
    catchment = catchment.set_crs(h_crs)
    catchment.to_file(basepath / result_folder / "catchment_boundary.geojson", crs=fr"EPSG:{h_crs}", driver="GeoJSON")

    # Roughness
    instruction_roughness = {
        # roughness - output
        "output": {
            "crs": {
                "horizontal": h_crs,
                "vertical": v_crs
            },
            "grid_params": {
                "resolution": resolution_func
            }
        },

        # processing
        "processing": {
            "chunk_size": chunk_size_func,
            "number_of_cores": processor_func
        },

        # roughness - apis
        "datasets": {
            "vector": {
                "linz": {}
            },
            "lidar": {
                "local": {
                    f"{lidar_dataset_name}": {
                        "crs": {
                            "horizontal": 2193,
                            "vertical": 7839
                        },
                        "folder_path": str(basepath / f"{lidar_dataset_name}")
                    }
                }
            }
        },

        # roughness - data_paths
        "data_paths": {
            "local_cache": str(basepath),
            "subfolder": result_folder,
            "extents": "catchment_boundary.geojson",
            "land": "land.geojson",
            "ocean_contours": "bathymetry_contours.geojson",
            "result_dem": fr"{transformed_dem_nc_path}\\{output_dem}",
            "result_geofabric": fr"{transformed_roughness_nc_path}\\{output_roughness}"
        },

        # roughness - general
        "general": {
            "set_dem_shoreline": True,
            "drop_offshore_lidar": False,
            "lidar_classifications_to_keep": [1, 2, 4, 9],
            "interpolation": {
                "no_data": "nearest",
                "lidar": "idw"
            }
        }
    }

    # Save the instructions
    with open(basepath / result_folder / "instructions.json", "w") as instruction:
        json.dump(instruction_roughness, instruction)

    # Create ROUGHNESS raster
    runner = processor.RoughnessLengthGenerator(instruction_roughness)
    runner.run()

def zo_to_n(number_simulation, H):
    """
    @Definition:
                A function to create a raster file of Manning's n from roughness length
    @References:
                https://doi.org/10.1080/15715124.2017.1411923
    @Arguments:
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                H (int):
                                            Value of depth
    @Returns:
                A raster of Manning's n
    """
    # Extract roughness length
    full_roughness_nc = rxr.open_rasterio(
        fr"{transformed_roughness_nc_path}\\generated_roughness_transformed_{number_simulation}.nc"
    )
    zo = full_roughness_nc.zo

    # Convert roughness length (zo) to Manning's n
    manning_n = (0.41 * (H ** (1 / 6)) * ((H / zo) - 1)) / (np.sqrt(9.80665) * (1 + (H / zo) * (np.log(H / zo) - 1)))

    # Calibrate manning's n
    new_manning_n = manning_n

    # Fill nan
    new_manning_n_interpolation = new_manning_n.interpolate_na(dim="x", method="linear")

    # Write out Manning's n
    new_manning_n_interpolation.rio.to_raster(
        fr"{transformed_n_nc_path}\\generated_n_transformed_{number_simulation}.nc"
    )

# END ROUGHNESS ######################################################################################################


# STARTDEPTH ###########################################################################################################
def startdepth_generation(
    dem_onlychangepadding_path,
    number_simulation
):
    """
    @Definition:
                A function to generate startdepth file
    @References:
                None.
    @Arguments:
                dem_onlychangepadding_path (string):
                                Directory of dem that has no padding
                number_simulation (string):
                                A string to identify the order of simulation (should be angle, x, y)
    @Return:
                None.
    """
    # Get tide flow data
    tide_flow_df = pd.read_csv(fr"{other_data}\\tide_flow_data.csv", sep=',')
    tide_flow_df['DateTime'] = pd.to_datetime(tide_flow_df['DateTime'], format="%Y-%m-%d %H:%M:%S", utc=False)

    # Read dem
    dem_ori = rxr.open_rasterio(fr"{dem_onlychangepadding_path}")
    dem = dem_ori.z.copy(deep=True)

    # Select values for startdepth
    startdepth = dem.where(dem.values <= tide_flow_df.Level.iloc[0], other=np.nan)
    startdepth = startdepth * -1

    # Fill values np.nan as 0
    startdepth.fillna(9999)
    startdepth = startdepth.where(startdepth.values >= 0, other=0)
    startdepth = startdepth.where(startdepth.values != 9999, other=np.nan)

    # Create startdepth raster (GeoTiff)
    startdepth.rio.to_raster(fr"{transformed_startdepth_tiff_path}\\startdepth_{number_simulation}.tif", cache=False)

    # For checking original if in case
    startdepth.rio.to_raster(fr"{transformed_startdepth_nc_path}\\startdepth_{number_simulation}.nc")

# END STARTDEPTH #######################################################################################################



# SIMULATE RASTER GENERATION FUNCTION ##################################################################################
def raster_generation(
        resolution_func,
        chunk_size_func,
        processor_func,
        padding_func,
        lidar_dataset_name,
        center_x_func, center_y_func,
        ran_trans_i
):
    """
    @Definition:
                A function to create a raster file from a las/laz file
    @References:
                https://github.com/rosepearson/GeoFabrics
    @Arguments:
                resolution_func (int or float):
                                            Resolution value in meter
                chunk_size_func (int):
                                            Size value of chunk
                processor_func (int):
                                            Number of processor
                number_simulation (string):
                                            A string to identify the order of simulation (should be angle, x, y)
                padding_func (list):
                                            A list of x min, x max, y min, and y max
                lidar_dataset_name (string):
                                            LiDAR name
                center_x_func (float):
                                            X coordinate of original/reference DEM
                center_y_func (float):
                                            Y coordinate of original/reference DEM
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
    number_simulation = f"angle_{angle_val}_x_{x_val}_y_{y_val}"

    # Write out necessary files
    necessary_files(ran_trans_i)

    # Create DEM
    dem_raster(
        resolution_func,
        chunk_size_func,
        processor_func,
        number_simulation,
        padding_func,
        lidar_dataset_name
    )

    # Create MANNING'S N
    # Roughness
    roughness_raster(
        resolution_func,
        chunk_size_func,
        processor_func,
        number_simulation,
        padding_func,
        lidar_dataset_name
    )
    # Manning's n
    zo_to_n(
        number_simulation,
        1
    )

    # Create STARTDEPTH
    startdepth_generation(
        fr"{transformed_dem_nc_path}\\generated_dem_transformed_{number_simulation}.nc",
        number_simulation
    )

    # Change value of padding
    value_padding_change(
        number_simulation,
        angle_val, x_val, y_val,
        center_x_func, center_y_func
    )

    # Change value of sea
    value_sea_change(
        number_simulation,
        angle_val, x_val, y_val,
        center_x_func, center_y_func,
        polygon=True # need to adjust manually
    )

    # Convert GeoTiff into ASCII
    convert_to_asc(number_simulation)

# END SIMULATE RASTER GENERATION FUNCTION ##############################################################################


