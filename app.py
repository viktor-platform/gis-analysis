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

import json
from pathlib import Path
from typing import Optional

from munch import Munch
from viktor import UserException
from viktor import ViktorController
from viktor.result import DownloadResult
from viktor.result import SetParamsResult
from viktor.views import DataGroup
from viktor.views import DataItem
from viktor.views import GeoJSONAndDataResult
from viktor.views import GeoJSONAndDataView
from viktor.views import InteractionEvent
from viktor.views import MapLabel
from viktor.views import WebResult
from viktor.views import WebView

from gis_functions import get_download
from gis_functions import get_gdf
from gis_functions import set_filter_attributes
from parametrization import Parametrization


class Controller(ViktorController):
    label = "GIS-app"
    parametrization = Parametrization(width=30)
    viktor_enforce_field_constraints = True

    @GeoJSONAndDataView("Map view", duration_guess=1)
    def get_geojson_view(self, params: Munch, **kwargs) -> GeoJSONAndDataResult:
        """Show all the map elements and data results"""
        gdf = get_gdf(params.shape_input.shapefile_upload, params.shape_input.data_source)
        geojson = json.loads(gdf.to_json())

        # Add labels to the map
        if params.shape_input.data_source == "Sample data":
            gdf_labels = gdf.dropna().copy()
            gdf_labels["label_geometry"] = gdf_labels.representative_point()
            labels = [
                MapLabel(point.y, point.x, str(gdf_labels.labels.iloc[index]), 3)
                for index, point in enumerate(gdf_labels.label_geometry)
            ]
        else:  # Create an empty placeholder for the labels
            gdf_labels = gdf.copy()
            gdf_labels["label_geometry"] = gdf_labels.representative_point()
            labels = [MapLabel(gdf_labels.label_geometry[0].x, gdf_labels.label_geometry[0].x, " ", 20)]

        # Set filter
        if params.attributes.set_filter:
            gdf_filtered = set_filter_attributes(gdf, params.attributes)
            geojson = json.loads(gdf_filtered.to_json())

        # Get and compare results for selected features
        if params.attribute_results:
            selected_features_indeces = params.attribute_results
            try:
                gdf_selected = gdf.loc[selected_features_indeces]
            except KeyError:
                raise UserException(
                    "Selection from sample data is still in memory. Please restart the app to clear " "the database."
                )
            if params.compare.field_name == params.compare.selected_value:
                raise UserException("Field names and compare for values cannot be the same. Please change this value.")
            gdf_combined = gdf_selected[[params.compare.field_name, params.compare.selected_value]].reset_index()
            gdf_combined = gdf_combined.sort_values(by=[params.compare.selected_value], ascending=False)
            attribute_results = DataGroup(
                DataItem(f"**{params.compare.field_name}**", f"**{params.compare.selected_value}**"),
                *[
                    DataItem(str(field_name), str(value))
                    for field_name, value in zip(
                        gdf_combined[params.compare.field_name].tolist(),
                        gdf_combined[params.compare.selected_value].tolist(),
                    )
                ],
            )
        else:  # Create an empty placeholder for results
            attribute_results = DataGroup(DataItem("Compare by ranking: Please select shapes to compare", ""))

        return GeoJSONAndDataResult(geojson, attribute_results, labels)

    def compare_attributes(self, event: Optional[InteractionEvent], **kwargs) -> SetParamsResult:
        """Returns the index of the selected features"""
        if event:
            selected_features_indeces = [int(value) for value in event.value]
            return SetParamsResult({"attribute_results": selected_features_indeces})

    def download_geopackage(self, params: Munch, **kwargs) -> DownloadResult:
        """Download selected results to a geopackage"""
        gdf = get_gdf(params.shape_input.shapefile_upload, params.shape_input.data_source)
        if params.attributes.set_filter:
            gdf = set_filter_attributes(gdf, params.attributes)

        gdf.drop(columns=["description", "fill"], inplace=True)
        if gdf.crs.to_epsg() != params.download.output_crs:  # Check if output CRS is different than input CRS
            if params.download.output_crs == "Other":  # Use any EPSG coordinate system
                gdf = gdf.to_crs(params.download.output_crs_other)
            else:  # Use one of the predefined coordinate systems
                gdf = gdf.to_crs(params.download.output_crs)
        download_file, file_name = get_download(params.download.output_format_options, gdf)

        return DownloadResult(download_file, file_name)

    @WebView("What's next?", duration_guess=1)
    def final_step(self, params, **kwargs):
        """Initiates the process of rendering the last step."""
        html_path = Path(__file__).parent / "final_step.html"
        with html_path.open() as f:
            html_string = f.read()
        return WebResult(html=html_string)
