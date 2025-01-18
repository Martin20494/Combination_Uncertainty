# Prepare packages --------------------------------------------------------------------------------
import pathlib                              # For creating and manipulating the directory path
import os                                   # For manipulating the directory and to execute commands
from versionModule import version           # For changing version
# -------------------------------------------------------------------------------------------


# Set up PATH -------------------------------------------------------------------------------
# Assign the path to the variable
MAIN_DIR = f"S:\\new_versions_004\\{version}"

# Create header path
pathlib.Path(f"{MAIN_DIR}").mkdir(parents=True, exist_ok=True)

# Change the directory
os.chdir(f"{MAIN_DIR}")
# -------------------------------------------------------------------------------------------


# Create paths #############################################################################
# ------------------------------- This is for TRANSFORMATION PART --------------------------

## General data: Folder stores all files that need to download
other_data = f"{MAIN_DIR}\\other_data"

## 0_lidar_data: Folder stores downloaded lidar point cloud data from Open Topography website
# Reference: https://portal.opentopography.org/datasets
original_lidar_path = f"{MAIN_DIR}\\0_lidar_data"

## 1_transformation: Folder stores transformed lidar point cloud data
transformed_lidar_path = f"{MAIN_DIR}\\1_transformation"

## 2_raster: Folder stores DEM rasters
# DEM -------------
# Netcdf
transformed_dem_nc_path = f"{MAIN_DIR}\\2_raster\\dem\\netcdf"
# GeoTiff
transformed_dem_tiff_path = f"{MAIN_DIR}\\2_raster\\dem\\tiff"
# Ascii
transformed_dem_asc_path = f"{MAIN_DIR}\\2_raster\\dem\\ascii"

# ROUGHNESS -------
# Netcdf
transformed_roughness_nc_path = f"{MAIN_DIR}\\2_raster\\roughness\\netcdf"
# GeoTiff
transformed_roughness_tiff_path = f"{MAIN_DIR}\\2_raster\\roughness\\tiff"
# Ascii
transformed_roughness_asc_path = f"{MAIN_DIR}\\2_raster\\roughness\\ascii"

# STARTDEPTH ------
# Netcdf
transformed_startdepth_nc_path = f"{MAIN_DIR}\\2_raster\\startdepth\\netcdf"
# GeoTiff
transformed_startdepth_tiff_path = f"{MAIN_DIR}\\2_raster\\startdepth\\tiff"
# Ascii
transformed_startdepth_asc_path = f"{MAIN_DIR}\\2_raster\\startdepth\\ascii"

# SHAPEFILE of PADDING
transformed_shapefile = f"{MAIN_DIR}\\2_raster\\shapefile"


## 3_LISFLOOD: Folder stores DEM rasters
# Parameters
transformed_FPpara_path = f"{MAIN_DIR}\\3_LISFLOOD_FP\\transformed_para"

# Outputs
transformed_FPoutput_path = f"{MAIN_DIR}\\3_LISFLOOD_FP\\transformed_output"


## 4_un_transformation
# Water depth (wd)
extracted_wd = f"{MAIN_DIR}\\4_untransformation\\wd"
untransformed_wd= f"{MAIN_DIR}\\4_untransformation\\untransformed_wd"

# Water surface elevation (wse)
extracted_wse = f"{MAIN_DIR}\\4_untransformation\\wse"
untransformed_wse= f"{MAIN_DIR}\\4_untransformation\\untransformed_wse"

# Elevation
untransformed_elev = f"{MAIN_DIR}\\4_untransformation\\untransformed_elev"


# ----------------------------------------- This is for ANALYSIS PART -----------------------
## 5_results
# Variation
# Water depth
wd_csv_untransformation = f"{MAIN_DIR}\\5_analysis\\wd\\untransformed_csv"
wd_raster_untransformation = f"{MAIN_DIR}\\5_analysis\\wd\\untransformed_raster"
wd_plot_untransformation = f"{MAIN_DIR}\\5_analysis\\wd\\untransformed_plot"
wd_onepolygon_untransformation = f"{MAIN_DIR}\\5_analysis\\wd\\untransformed_impact\\onepolygon_nobackground"
wd_oneraster_untransformation = f"{MAIN_DIR}\\5_analysis\\wd\\untransformed_impact\\oneraster_nobackground"

# Water surface elevation
wse_csv_untransformation = f"{MAIN_DIR}\\5_analysis\\wse\\untransformed_csv"
wse_raster_untransformation = f"{MAIN_DIR}\\5_analysis\\wse\\untransformed_raster"
wse_plot_untransformation = f"{MAIN_DIR}\\5_analysis\\wse\\untransformed_plot"
wse_onepolygon_untransformation = f"{MAIN_DIR}\\5_analysis\\wse\\untransformed_impact\\onepolygon_nobackground"
wse_oneraster_untransformation = f"{MAIN_DIR}\\5_analysis\\wse\\untransformed_impact\\oneraster_nobackground"

# Elevation
elev_csv_untransformation = f"{MAIN_DIR}\\5_analysis\\elev\\untransformed_csv"

# -------------------------------------------------------------------------------------------

# Ending path creation ######################################################################


# Create a list of all sub-folders' paths --------------------------------------------------
necessary_files = [
    # Data needs downloading
    other_data,

    # 0_lidar_data
    original_lidar_path,

    # 1_transformation
    transformed_lidar_path,

    # 2_dem_raster
    # DEM
    transformed_dem_nc_path,
    transformed_dem_tiff_path,
    transformed_dem_asc_path,
    # ROUGHNESS
    transformed_roughness_nc_path,
    transformed_roughness_tiff_path,
    transformed_roughness_asc_path,
    # STARTDEPTH
    transformed_startdepth_nc_path,
    transformed_startdepth_tiff_path,
    transformed_startdepth_asc_path,
    # SHAPEFILE
    transformed_shapefile,

    # 3_LISFLOOD
    transformed_FPpara_path,
    transformed_FPoutput_path,

    # 4_untransformation
    # Water depth
    extracted_wd,
    untransformed_wd,
    # Water surface elevation
    extracted_wse,
    untransformed_wse,
    # Elevation
    untransformed_elev,

    # 5_results
    # Variation
    # Water depth
    wd_csv_untransformation,
    wd_raster_untransformation,
    wd_plot_untransformation,
    # Water surface elevation
    wse_csv_untransformation,
    wse_raster_untransformation,
    wse_plot_untransformation,
    # Elevation
    elev_csv_untransformation,

    # Impact
    # Water depth
    wd_onepolygon_untransformation,
    wd_oneraster_untransformation,
    # Water surface elevation
    wse_onepolygon_untransformation,
    wse_oneraster_untransformation
]
# -------------------------------------------------------------------------------------------


# Execute all sub-folders -------------------------------------------------------------------
for each_folder in necessary_files:
    pathlib.Path(f"{each_folder}").mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------