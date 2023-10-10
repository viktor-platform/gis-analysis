"""Copyright (c) 2022 VIKTOR B.V.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.
VIKTOR B.V. PROVIDES THIS SOFTWARE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Tuple

import geopandas as gpd
from geopandas import GeoDataFrame
from munch import Munch
from viktor import File
from viktor import UserError
from viktor.api_v1 import FileResource


def get_gdf(upload_file: FileResource, data_source: str, styling: Munch) -> GeoDataFrame:
    """Creates a geodataframe. Also adds attribute table as click-event and sets the color."""
    if data_source == "Custom data" and upload_file:  # Custom data
        shapefile_file = upload_file.file
        data_IO = BytesIO(shapefile_file.getvalue_binary())
        gdf = gpd.read_file(data_IO)
        gdf = gdf.to_crs("EPSG:4326")
        field_names = gdf.columns.drop(["geometry"])
    else:  # Sample data
        gdf = gpd.read_file(Path(__file__).parent / "language_per_country_europe.zip", crs=4326)
        gdf["title"] = gdf["Country"]
        field_names = gdf.columns.drop(["geometry", "title"])
    gdf["fill"] = styling.color.hex  # Set color
    gdf["fill-opacity"] = styling.opacity
    gdf["stroke-width"] = styling.line_width

    # Add attribute table to the geodataframe as a string, so it can be added to the map as a click-event
    gdf_description = ""
    for field_name in field_names:
        gdf_description = gdf_description + field_name + ": " + gdf[field_name].astype(str) + "  \n  "
    gdf["description"] = gdf_description
    gdf.fillna("")  # Get rid of NaN-values, which can cause problems with some calculations
    return gdf


def get_download(file_type: str, gdf: GeoDataFrame) -> Tuple[File, str]:
    """Convert a GeoDataFrame to a Vikor-File, which can be downloaded. Available output formats are: .shp, .gpkg,
    .dxf, .json
    """
    if file_type == "shapefile":
        with tempfile.TemporaryDirectory() as temp_dir:
            shape_name = "shapefile"
            file_name = shape_name + ".zip"
            gdf.to_file(filename=os.path.join(temp_dir, shape_name + ".shp"), driver="ESRI Shapefile")
            shutil.make_archive(shape_name, "zip", temp_dir)
            with open(file_name, "rb") as fh:
                buffer = BytesIO(fh.read())
                download_file = File.from_data(buffer.getvalue())
            shutil.rmtree(temp_dir)
        os.remove(file_name)
    if file_type == "geopackage":
        bytes_buffer = BytesIO()
        gdf.to_file(bytes_buffer, driver="GPKG", layer="geopackage")
        download_file = File.from_data(bytes_buffer.getvalue())
        file_name = "geopackage.gpkg"
    if file_type == "autocad":
        bytes_buffer = BytesIO()
        gdf.geometry.to_file(bytes_buffer, driver="DXF")
        download_file = File.from_data(bytes_buffer.getvalue())
        file_name = "autocad.dxf"
    if file_type == "geojson":
        bytes_buffer = BytesIO()
        gdf.to_file(bytes_buffer, driver="GeoJSON")
        download_file = File.from_data(bytes_buffer.getvalue())
        file_name = "geojson.json"
    return download_file, file_name


def set_filter_attributes(gdf: GeoDataFrame, attributes: Munch) -> GeoDataFrame:
    """Add filter on attributes in GeoDataFrame."""
    if attributes.filter_type == "Unique value":
        gdf = gdf[gdf[attributes.field_name] == attributes.attribute_value]
    elif attributes.filter_type == "Range":
        try:
            gdf = gdf[gdf[attributes.field_name] >= attributes.minimum_value]
            gdf = gdf[gdf[attributes.field_name] <= attributes.maximum_value]
        except TypeError:  # range only works for numerical values
            raise UserError(
                "Filter by range is only possible for numerical values. Please select 'Unique value' " "instead."
            )
    return gdf
