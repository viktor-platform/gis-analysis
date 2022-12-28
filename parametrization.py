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

from munch import Munch
from viktor.parametrization import And
from viktor.parametrization import AutocompleteField
from viktor.parametrization import BooleanField
from viktor.parametrization import DownloadButton
from viktor.parametrization import FileField
from viktor.parametrization import HiddenField
from viktor.parametrization import IsEqual
from viktor.parametrization import IsNotNone
from viktor.parametrization import IsTrue
from viktor.parametrization import LineBreak
from viktor.parametrization import Lookup
from viktor.parametrization import MapSelectInteraction
from viktor.parametrization import NumberField
from viktor.parametrization import OptionField
from viktor.parametrization import OptionListElement
from viktor.parametrization import Section
from viktor.parametrization import SetParamsButton
from viktor.parametrization import Text
from viktor.parametrization import ViktorParametrization

from gis_functions import get_gdf


def _get_field_name_options(params: Munch, **kwargs) -> list:
    """Returns all attribute field names"""
    try:
        gdf = get_gdf(params.shape_input.shapefile_upload, params.shape_input.data_source)
        field_name_options = gdf.columns.drop(["geometry", "fill", "description"])
        field_name_options = field_name_options.dropna().tolist()
    except KeyError:  # Create an empty placeholder
        field_name_options = [" "]
    return field_name_options


def _get_value_options(params: Munch, **kwargs) -> list:
    """Return all unique values for a selected attribute field name"""
    try:
        gdf = get_gdf(params.shape_input.shapefile_upload, params.shape_input.data_source)
        value_options = gdf[params.attributes.field_name]
        attribute_value_options = value_options.dropna().unique().tolist()
    except KeyError:  # Create an empty placeholder
        attribute_value_options = [" "]
    return attribute_value_options


class Parametrization(ViktorParametrization):
    shape_input = Section("Input")
    shape_input.introduction_text = Text(
        "Welcome to the VIKTOR sample-GIS app. In this application is shown how to do basic GIS-analysis in VIKTOR."
    )
    shape_input.data_source = OptionField(
        "Data source", options=["Sample data", "Custom data"], variant="radio-inline", default="Sample data"
    )
    shape_input.sample_data_text = Text(
        "Some sample data is loaded to play around with. Additionally, it is possible to upload your "
        "own GIS-data (shapefile, geojson, geopackage and dxf are supported). When uploading a shapefile, make sure it is zipped to a "
        "single file.",
    )
    shape_input.line_break = LineBreak()
    shape_input.shapefile_upload = FileField(
        "Upload file", description="Upload GIS-data", visible=IsEqual("Custom data", Lookup("shape_input.data_source"))
    )
    shape_input.attribute_results = HiddenField("attribute_results", "attribute_results")
    attributes = Section("Filter")
    attributes.attribute_field_filter_text = Text(
        "Filter shapes by its attribute value, obtained from the attribute table. "
        "When the filter is activated, only the shapes are shown for which its attribute values are within the filter."
    )
    attributes.set_filter = BooleanField("Activate filter")
    attributes.line_break3 = LineBreak()
    attributes.field_name = OptionField(
        "Field names",
        options=_get_field_name_options,
        description="Field names are imported automatically from the attribute table.",
        visible=IsTrue(Lookup("attributes.set_filter")),
        default="Currency",
    )
    attributes.line_break = LineBreak()
    attributes.filter_type = OptionField(
        "Filter type",
        options=["Unique value", "Range"],
        variant="radio-inline",
        default="Unique value",
        visible=IsTrue(Lookup("attributes.set_filter")),
        description="**Unique values:** all unique values from the selected field name are imported  \n  "
                    "**Range:** Set a minimum and maximum value to filter numerical values"
    )
    attributes.line_break2 = LineBreak()
    attributes.attribute_value = AutocompleteField(
        "Value",
        options=_get_value_options,
        visible=And(IsEqual("Unique value", Lookup("attributes.filter_type")), IsTrue(Lookup("attributes.set_filter"))),
        description="Unique values are imported automatically from the attribute table, based on the selected field "
        "name",
        default="Euro",
    )
    attributes.attribute_field_filter_text3 = Text(
        "Set value options for selected field name and filter by selected range.",
        visible=And(IsEqual("Range", Lookup("attributes.filter_type")), IsTrue(Lookup("attributes.set_filter"))),
    )
    attributes.minimum_value = NumberField("Minimum value", visible=IsEqual("Range", Lookup("attributes.filter_type")))
    attributes.maximum_value = NumberField("Maximum value", visible=IsEqual("Range", Lookup("attributes.filter_type")))
    compare = Section("Compare by ranking")
    compare.text = Text(
        "Compare different shapes with eachother by ranking. First select the attribute field with "
        "the names of the shapes. Then, select the value for which the shapes should be ranked. Finally, select "
        "shapes on the map to compare."
    )
    compare.compare_features = SetParamsButton(
        "Select shapes to compare",
        "compare_attributes",
        interaction=MapSelectInteraction("get_geojson_view", min_select=1, max_select=10),
    )
    compare.linebreak = LineBreak()
    compare.field_name = OptionField(
        "Field names",
        options=_get_field_name_options,
        default="Country",
        visible=IsNotNone(Lookup("attribute_results")),
    )
    compare.selected_value = OptionField(
        "Compare for values",
        options=_get_field_name_options,
        default="Population",
        visible=IsNotNone(Lookup("attribute_results")),
    )
    download = Section("Download")
    download.text = Text(
        "Download the GIS-data to any of the output formats as shown below. When the filter is activated,"
        " only the filtered data is downloaded."
    )
    download.output_format_options = OptionField(
        "Output format",
        options=[
            OptionListElement("shapefile", "Shapefile (.shp)"),
            OptionListElement("geopackage", "Geopackage (.gpkg)"),
            OptionListElement("autocad", "AutoCAD (.DXF)"),
            OptionListElement("geojson", "GeoJSON"),
        ],
        default="shapefile",
    )
    download.output_crs = OptionField(
        "CRS output",
        options=[OptionListElement("4326", "WGS84 (4326)"), OptionListElement("28992", "RD NEW (28992)"), "Other"],
        default=4326,
    )
    download.output_crs_other = NumberField(
        "CRS output (other)",
        description="Enter any EPSG coordinate system here.",
        visible=IsEqual("Other", Lookup("download.output_crs")),
    )
    download.linebreak = LineBreak()
    download.download_shapefile = DownloadButton("Download", "download_geopackage")
