![](https://img.shields.io/badge/SDK-v13.7.0-blue) <Please check version is the same as specified in requirements.txt>

# GIS in Viktor
This sample app demonstrates how to do a GIS-analysis in Viktor.

The goal of this app is to demonstrate some common GIS analyses using Viktor. This app was developed using an 
open-source library (`geopandas`), which provides a powerful toolkit for GIS-analysis. Using Viktor, complex analysis 
becomes easy to perform, accessible through the browser.

In this application the following functionalities are demonstrated:
- Uploading and visualizing custom GIS-data (shapefile, geopackage, geojson)
- Add filters to attribute table
- MapView interaction, analysis on selected features
- Download data as any GIS-datatype (shapefile, geopackage, geojson, autocad)

This app consists of a single editor.

A published version of this app is available on [demo.viktor.ai](https://demo.viktor.ai/workspaces/63/app/).

Here is an animation going through the steps: 
- Step 1: Uploading a .gef file
- Step 2: Choosing a classification method
- Step 3: Classifying the soil layout
- Step 4: Interpreting the results

![](resources/steps.gif)


## App structure
This is an editor-only app type.
