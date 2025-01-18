# Prepare packages --------------------------------------------------------------------------------
import pathlib                              # For creating and manipulating the directory path
import os                                   # For manipulating the directory and to execute commands
from versionModule import version          # For changing version
# -------------------------------------------------------------------------------------------


# Set up PATH -------------------------------------------------------------------------------
# Assign the path to the variable
MAIN_DIR = fr"S:\Combine_Uncertainty_Folders\uncertainty_combination\buller\{version}"

# Create header path
pathlib.Path(f"{MAIN_DIR}").mkdir(parents=True, exist_ok=True)

# Change the directory
os.chdir(f"{MAIN_DIR}")
# -------------------------------------------------------------------------------------------


# Create paths #############################################################################
# ------------------------------- This is for TRANSFORMATION PART --------------------------

## General data: Folder stores all files that need to download
other_data = fr"{MAIN_DIR}\other_data"

## 0_lidar_data: Folder stores downloaded lidar point cloud data from Open Topography website
# Reference: https://portal.opentopography.org/datasets
original_lidar_path = fr"{MAIN_DIR}\0_lidar_data"

## 1_transformation: Folder stores transformed lidar point cloud data
bathy_before_transformed_lidar_path = fr"{MAIN_DIR}\1_bathy_transformation\bathy_before_transformation"
bathy_after_transformed_lidar_path = fr"{MAIN_DIR}\1_bathy_transformation\bathy_after_transformation"

## 2_raster: Folder stores DEM rasters
# DEM -------------
# Netcdf
bathy_transformed_dem_nc_path = fr"{MAIN_DIR}\2_raster\dem\netcdf"
# GeoTiff
bathy_transformed_dem_tiff_path = fr"{MAIN_DIR}\2_raster\dem\tiff"
# Ascii
bathy_transformed_dem_asc_path = fr"{MAIN_DIR}\2_raster\dem\ascii"

# MANNING'S N -------
# Roughness
bathy_transformed_roughness_nc_path = fr"{MAIN_DIR}\2_raster\n\roughness"
# Netcdf
bathy_transformed_n_nc_path = fr"{MAIN_DIR}\2_raster\n\netcdf"
# GeoTiff
bathy_transformed_n_tiff_path = fr"{MAIN_DIR}\2_raster\n\tiff"
# Ascii
bathy_transformed_n_asc_path = fr"{MAIN_DIR}\2_raster\n\ascii"

# STARTDEPTH ------
# Netcdf
bathy_transformed_startdepth_nc_path = fr"{MAIN_DIR}\2_raster\startdepth\netcdf"
# GeoTiff
bathy_transformed_startdepth_tiff_path = fr"{MAIN_DIR}\2_raster\startdepth\tiff"
# Ascii
bathy_transformed_startdepth_asc_path = fr"{MAIN_DIR}\2_raster\startdepth\ascii"

# SHAPEFILE of PADDING
bathy_transformed_shapefile = fr"{MAIN_DIR}\2_raster\shapefile"


## 3_LISFLOOD: Folder stores DEM rasters
# Parameters
bathy_transformed_FPpara_path = fr"{MAIN_DIR}\3_LISFLOOD_FP\bathy_transformed_para"

# Outputs
bathy_transformed_FPoutput_path = fr"{MAIN_DIR}\3_LISFLOOD_FP\bathy_transformed_output"


## 4_bathy_untransformation_extraction
# Water depth (wd)
extracted_wd = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\wd"
bathy_untransformed_wd= fr"{MAIN_DIR}\4_bathy_untransformation_extraction\bathy_untransformed_wd"
# ----------
filter_extracted_wd_tiff = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_wd\tiff"
filter_extracted_wd_shp = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_wd\shp"
filter_extracted_wd_nc = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_wd\nc"
filter_bathy_untransformed_wd = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_bathy_untransformed_wd"

# Water surface elevation (wse)
extracted_wse = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\wse"
bathy_untransformed_wse= fr"{MAIN_DIR}\4_bathy_untransformation_extraction\bathy_untransformed_wse"
# ----------
filter_extracted_wse_tiff = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_wse\tiff"
filter_extracted_wse_shp = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_wse\shp"
filter_extracted_wse_nc = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_wse\nc"
filter_bathy_untransformed_wse = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_bathy_untransformed_wse"

# Elevation
bathy_untransformed_elev = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\bathy_untransformed_elev"
# ----------
filter_extracted_elev_tiff = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_elev\tiff"
filter_extracted_elev_shp = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_elev\shp"
filter_extracted_elev_nc = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_elev\nc"
filter_bathy_untransformed_elev = fr"{MAIN_DIR}\4_bathy_untransformation_extraction\filter_bathy_untransformed_elev"

# ----------------------------------------- This is for ANALYSIS PART -----------------------
## 5_results
# Variation
# Water depth
wd_csv_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wd\bathy_untransformed_csv"
wd_raster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wd\bathy_untransformed_raster"
wd_plot_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wd\bathy_untransformed_plot"
wd_onepolygon_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wd\bathy_untransformed_impact\onepolygon_nobackground"
wd_oneraster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wd\bathy_untransformed_impact\oneraster_nobackground"
# ---------
wd_filter_csv_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wd\bathy_untransformed_csv"
wd_filter_raster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wd\bathy_untransformed_raster"
wd_filter_plot_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wd\bathy_untransformed_plot"
wd_filter_onepolygon_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wd\bathy_untransformed_impact\onepolygon_nobackground"
wd_filter_oneraster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wd\bathy_untransformed_impact\oneraster_nobackground"

# Water surface elevation
wse_csv_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wse\bathy_untransformed_csv"
wse_raster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wse\bathy_untransformed_raster"
wse_plot_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wse\bathy_untransformed_plot"
wse_onepolygon_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wse\bathy_untransformed_impact\onepolygon_nobackground"
wse_oneraster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\wse\bathy_untransformed_impact\oneraster_nobackground"
# ----------------
wse_filter_csv_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wse\bathy_untransformed_csv"
wse_filter_raster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wse\bathy_untransformed_raster"
wse_filter_plot_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wse\bathy_untransformed_plot"
wse_filter_onepolygon_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wse\bathy_untransformed_impact\onepolygon_nobackground"
wse_filter_oneraster_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\wse\bathy_untransformed_impact\oneraster_nobackground"

# Elevation
elev_csv_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\nonfilter\elev\bathy_untransformed_csv"
# -------
elev_filter_csv_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\filter\elev\bathy_untransformed_csv"

# RMSE
rmse_bathy_untransformation = fr"{MAIN_DIR}\5_analysis\rmse"


# -------------------------------------------------------------------------------------------

# Ending path creation ######################################################################


# Create a list of all sub-folders' paths --------------------------------------------------
necessary_files = [
    # Data needs downloading
    other_data,

    # 0_lidar_data
    original_lidar_path,

    # 1_transformation
    bathy_before_transformed_lidar_path,
    bathy_after_transformed_lidar_path,

    # 2_dem_raster
    # DEM
    bathy_transformed_dem_nc_path,
    bathy_transformed_dem_tiff_path,
    bathy_transformed_dem_asc_path,
    # MANNING'S N
    bathy_transformed_roughness_nc_path,
    bathy_transformed_n_nc_path,
    bathy_transformed_n_tiff_path,
    bathy_transformed_n_asc_path,
    # STARTDEPTH
    bathy_transformed_startdepth_nc_path,
    bathy_transformed_startdepth_tiff_path,
    bathy_transformed_startdepth_asc_path,
    # SHAPEFILE
    bathy_transformed_shapefile,

    # 3_LISFLOOD
    bathy_transformed_FPpara_path,
    bathy_transformed_FPoutput_path,

    # 4_bathy_untransformation_extraction
    # Water depth
    extracted_wd,
    extracted_wse,
    # -----------
    filter_extracted_wd_tiff,
    filter_extracted_wd_shp,
    filter_extracted_wd_nc,
    filter_bathy_untransformed_wd,
    # Water surface elevation
    bathy_untransformed_wd,
    bathy_untransformed_wse,
    # -----------
    filter_extracted_wse_tiff,
    filter_extracted_wse_shp,
    filter_extracted_wse_nc,
    filter_bathy_untransformed_wse,
    # Elevation
    bathy_untransformed_elev,
    # -----------
    filter_extracted_elev_tiff,
    filter_extracted_elev_shp,
    filter_extracted_elev_nc,
    filter_bathy_untransformed_elev,

    # 5_results
    # NON FILTER ---
    # Variation
    # Water depth
    wd_csv_bathy_untransformation,
    wd_raster_bathy_untransformation,
    wd_plot_bathy_untransformation,
    # Water surface elevation
    wse_csv_bathy_untransformation,
    wse_raster_bathy_untransformation,
    wse_plot_bathy_untransformation,
    # Elevation
    elev_csv_bathy_untransformation,

    # Impact
    # Water depth
    wd_onepolygon_bathy_untransformation,
    wd_oneraster_bathy_untransformation,
    # Water surface elevation
    wse_onepolygon_bathy_untransformation,
    wse_oneraster_bathy_untransformation,

    # FILTER ---
    # Variation
    # Water depth
    wd_filter_csv_bathy_untransformation,
    wd_filter_raster_bathy_untransformation,
    wd_filter_plot_bathy_untransformation,
    # Water surface elevation
    wse_filter_csv_bathy_untransformation,
    wse_filter_raster_bathy_untransformation,
    wse_filter_plot_bathy_untransformation,
    # Elevation
    elev_filter_csv_bathy_untransformation,

    # Impact
    # Water depth
    wd_filter_onepolygon_bathy_untransformation,
    wd_filter_oneraster_bathy_untransformation,
    # Water surface elevation
    wse_filter_onepolygon_bathy_untransformation,
    wse_filter_oneraster_bathy_untransformation,

    # RMSE ---
    rmse_bathy_untransformation
]
# -------------------------------------------------------------------------------------------


# Execute all sub-folders -------------------------------------------------------------------
for each_folder in necessary_files:
    pathlib.Path(f"{each_folder}").mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------