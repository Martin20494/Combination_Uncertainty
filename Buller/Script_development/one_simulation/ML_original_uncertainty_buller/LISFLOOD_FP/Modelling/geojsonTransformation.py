# Prepare packages -----------------------------------------------------------------------------------------------------

import numpy as np                                              # For data array manipulation
from shapely.geometry import Polygon, MultiPolygon, \
                             LineString, Point                  # For geometries manipulation
from transformation import center_calculation, \
                           wrapping_point_rotation, \
                           wrapping_point_translation           # For transformation
import geopandas as gpd                                         # For spatial dataframe manipulation
# ----------------------------------------------------------------------------------------------------------------------

# CONVERT SHAPELY GEOMETRIES TO 3D ARRAY -------------------------------------------------------------------------------
def geom_to_xyzarray(geom_coord, center_x_func, center_y_func, angle_func, x_translation_func, y_translation_func):
    """
    @Definition:
                A function to transform a polygon
    @References:
                https://stackoverflow.com/questions/20474549/extract-points-coordinates-from-a-polygon-in-shapely
    @Arguments:
                geom_coord (array):
                                An array of array package contains coordinates
                center_x_func, center_y_func (float):
                                Center coordinates of reference DEM
                angle_func, x_translation_func, y_translation_func (float):
                                Values of angle, x, and y to transform
    @Returns:
                (2D array):
                                An array of transformed x and y coordinates
    """
    # Create a zero-value column (third column) in 3D array
    zero_arr = np.zeros(len(geom_coord[0]))

    # Create 3D array containing values of x and y coordinates, and zero values
    arr = np.vstack((geom_coord[0], geom_coord[1], zero_arr)).T

    # Copy array to get only values (without any calculation)
    copy_arr = arr.copy()

    # Rotate polygon coordinates
    rotation = wrapping_point_rotation(copy_arr, angle_func, center_x_func, center_y_func, 0)

    # Translate polygon coordinates
    translation = wrapping_point_translation(rotation, x_translation_func, y_translation_func)

    return translation[:, :2]

# END CONVERTING SHAPELY GEOMETRIES TO 3D ARRAY ------------------------------------------------------------------------

# GEOMETRIES TRANSFORMATION --------------------------------------------------------------------------------------------
def geom_transform(file, ran_trans_i):
    """
    @Definition:
                A function to transform many polygons
    @References:
                https://stackoverflow.com/questions/39142876/check-if-a-polygon-is-a-multipolygon-in-shapely
    @Arguments:
                file (geo dataframe):
                                    A geo dataframe contains geometry column
                ran_trans_i (array):
                                    An element in a big 3D array. Format is [angle, x, y]
    @Returns:
                new_geom_list (list):
                                    A list of transformed geometries
    """
    # Get center to transform
    center_x, center_y = center_calculation(True)

    # Get values of angle, x, y to transform
    angle_func = ran_trans_i[0]
    x_translation_func = ran_trans_i[1]
    y_translation_func = ran_trans_i[2]

    # Transform process
    # Each line of geometry column will be checked if it is polygon, multipolygon, linestring, or point
    # Then the transformation process will be executed
    new_geom_list = []
    for i in range(file.shape[0]):
        geom = file.geometry.iloc[i]

        # Check if the geometry is None
        if geom is None:
            new_geom_list.append(None)

        # For polygon
        elif geom.geom_type == 'Polygon':
            poly_coord = geom.exterior.coords.xy
            poly_arr = geom_to_xyzarray(poly_coord,
                                        center_x, center_y, angle_func, x_translation_func, y_translation_func)
            new_poly = Polygon(poly_arr)
            new_geom_list.append(new_poly)

        # For multipolygon
        # Each polygon will be transformed within this multipolygon
        elif geom.geom_type == 'MultiPolygon':
            multipoly_list = []
            for n in range(len(geom.geoms)):
                multi_poly = geom.geoms[n]
                multi_coord = multi_poly.exterior.coords.xy
                new_multi_arr = geom_to_xyzarray(multi_coord,
                                                 center_x, center_y, angle_func, x_translation_func, y_translation_func)
                new_multi_poly = Polygon(new_multi_arr)
                multipoly_list.append(new_multi_poly)
            new_multipolygon = MultiPolygon(multipoly_list)
            new_geom_list.append(new_multipolygon)

        # For LineString
        elif geom.geom_type == 'LineString':
            str_coord = geom.coords.xy
            str_arr = geom_to_xyzarray(str_coord, center_x, center_y, angle_func, x_translation_func,
                                       y_translation_func)
            new_str = LineString(str_arr)
            new_geom_list.append(new_str)

        # For Point
        else:
            p_coord = geom.coords.xy
            p_arr = geom_to_xyzarray(p_coord, center_x, center_y, angle_func, x_translation_func, y_translation_func)
            new_p = Point(p_arr[0])
            new_geom_list.append(new_p)

    return new_geom_list

# END GEOMETRIES TRANSFORMATION ----------------------------------------------------------------------------------------


# WRITE OUT GEOJSON ----------------------------------------------------------------------------------------------------
def geom_geojson(path_in, path_out, ran_trans_i):
    """
    @Definition:
                A function to transform geometries and write out geojson
    @References:
                None.
    @Arguments:
                path_in (string):
                                Path to the file needs transforming
                path_out (string):
                                Path to the file needs writing out
                ran_trans_i (array):
                                An element in a big 3D array. Format is [angle, x, y]
    @Returns:
                None.
    """

    # Read file
    file = gpd.read_file(path_in)
    # Convert crs
    geom_crs = file.to_crs(2193)

    # Make a copy of file
    copy_geom = geom_crs.copy(deep=True)

    # Transform the geometry
    geom_list = geom_transform(copy_geom, ran_trans_i)

    # Change into the new geometry
    copy_geom['geometry'] = geom_list

    # Write out to geojson file
    copy_geom.to_file(path_out, driver="GeoJSON")
# END WRITING OUT GEOJSON ----------------------------------------------------------------------------------------------