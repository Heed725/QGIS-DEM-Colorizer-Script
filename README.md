# QGIS DEM Colorizer Script

A simple standalone PyQGIS script that applies an exact discrete elevation color scheme to the currently selected DEM raster in QGIS.

This repository now uses the standalone script:

```text
Tanzania_DEM_Exact_Style_QGIS_3_40.py
```

The previous Processing Toolbox version has been removed.

## What the script does

The script takes the raster currently selected in the QGIS Layers panel and changes its renderer to `singlebandpseudocolor` with fixed discrete elevation breaks.

It does not create a new raster and does not alter DEM cell values. It only changes the raster symbology in QGIS.

It also refreshes the layer legend and map canvas immediately after applying the style.

## Default elevation classes

| Elevation | Color |
|---|---|
| Below 0 m | Transparent |
| 0–100 m | `#A9CD6F` |
| 101–200 m | `#CCDD89` |
| 201–500 m | `#F7E8A3` |
| 501–1000 m | `#F9D58D` |
| 1001–1500 m | `#E7B882` |
| 1501–2000 m | `#E09762` |
| 2001–3000 m | `#C87C52` |
| 3001–4000 m | `#B15E38` |
| Above 4000 m | `#A65235` |

The script was prepared around a Tanzania DEM whose approximate range was:

```text
Minimum: -776 m
Maximum: 5786 m
```

Values below zero are transparent.

## Requirements

- QGIS 3.38, 3.40, 3.44 or another compatible QGIS 3.x release
- A valid single-band DEM raster loaded in QGIS
- QGIS Python Console

No external Python packages are required.

## Repository structure

```text
QGIS-DEM-Colorizer-Script/
├── Tanzania_DEM_Exact_Style_QGIS_3_40.py
└── README.md
```

## How to use

### 1. Download the script

Download:

```text
Tanzania_DEM_Exact_Style_QGIS_3_40.py
```

For example, save it in:

```text
C:\Users\Admin\Downloads\
```

### 2. Load your DEM into QGIS

Open QGIS and add your DEM TIFF or other supported elevation raster.

For example:

```text
tanzania_elevation.tif
```

### 3. Select the DEM in the Layers panel

Click the DEM layer so it becomes the active layer.

This is important because the script uses:

```python
layer = iface.activeLayer()
```

If no layer is selected, the script stops with an error.

### 4. Open the QGIS Python Console

Go to:

**Plugins → Python Console**

### 5. Run the script

If the file is in your Downloads folder, run:

```python
exec(open(r"C:\Users\Admin\Downloads\Tanzania_DEM_Exact_Style_QGIS_3_40.py").read())
```

Change the path if your script is stored elsewhere.

## Expected result

The DEM should immediately change from grayscale or its existing raster style to the Tanzania elevation color scheme.

The QGIS Python Console should print output similar to:

```text
==============================================
TANZANIA DEM STYLE APPLIED SUCCESSFULLY
==============================================
Layer: tanzania_elevation
Renderer: singlebandpseudocolor
Interpolation: DISCRETE

Exact classes loaded:
Below 0 m            | break=-1e-06 | RGBA=0,0,0,0
0 - 100 m            | break=100.0 | RGBA=169,205,111,255
101 - 200 m          | break=200.0 | RGBA=204,221,137,255
201 - 500 m          | break=500.0 | RGBA=247,232,163,255
...
```

The important verification lines are:

```text
Renderer: singlebandpseudocolor
Interpolation: DISCRETE
```

## How the discrete classes work

The script uses `QgsColorRampShader` with:

```python
Qgis.ShaderInterpolationMethod.Discrete
```

Each class value acts as an upper break.

For example:

```python
QgsColorRampShader.ColorRampItem(
    100.0,
    QColor("#A9CD6F"),
    "0 - 100 m"
)
```

means values up to the 100 m break use the first green class.

The next item:

```python
QgsColorRampShader.ColorRampItem(
    200.0,
    QColor("#CCDD89"),
    "101 - 200 m"
)
```

covers the next elevation interval up to 200 m.

## Transparency below 0 m

The first shader item is:

```python
QgsColorRampShader.ColorRampItem(
    -0.000001,
    QColor(0, 0, 0, 0),
    "Below 0 m"
)
```

The alpha value is zero, so elevations below 0 m are transparent.

This is useful when the DEM contains bathymetry, negative coastal values, or unwanted values below sea level.

## Editing the elevation breaks

The classes are defined inside the `items` list.

For example:

```python
items = [
    QgsColorRampShader.ColorRampItem(
        -0.000001,
        QColor(0, 0, 0, 0),
        "Below 0 m"
    ),

    QgsColorRampShader.ColorRampItem(
        100.0,
        QColor("#A9CD6F"),
        "0 - 100 m"
    ),

    QgsColorRampShader.ColorRampItem(
        200.0,
        QColor("#CCDD89"),
        "101 - 200 m"
    ),
]
```

To change a class, edit the upper break, color, or label.

For example, to change the first visible class to 0–150 m:

```python
QgsColorRampShader.ColorRampItem(
    150.0,
    QColor("#A9CD6F"),
    "0 - 150 m"
)
```

## Editing the colors

Colors use hexadecimal values inside `QColor()`.

Example:

```python
QColor("#A9CD6F")
```

You can replace the hex value with another valid color.

For example:

```python
QColor("#4CAF50")
```

## Editing the labels

The third value in every `ColorRampItem` is the legend label.

Example:

```python
"1001 - 1500 m"
```

You can rename it without changing the actual elevation break.

For example:

```python
"Highlands 1001 - 1500 m"
```

## Adding another class

Add another `QgsColorRampShader.ColorRampItem` in the correct elevation order.

Example:

```python
QgsColorRampShader.ColorRampItem(
    5000.0,
    QColor("#8C3B2A"),
    "4001 - 5000 m"
),
```

Then adjust the final class if needed.

## Highest elevation class

The final item uses a very large upper value:

```python
QgsColorRampShader.ColorRampItem(
    1000000000.0,
    QColor("#A65235"),
    "Above 4000 m"
)
```

This ensures that all raster values above 4000 m receive the last dark-brown color, including values higher than the DEM used during development.

## Classification limits

The script currently sets:

```python
renderer.setClassificationMin(-776.0)
renderer.setClassificationMax(5786.0)
```

These values match the Tanzania DEM used during development.

If your DEM has a very different elevation range, you can change these two values.

For example:

```python
renderer.setClassificationMin(0.0)
renderer.setClassificationMax(8849.0)
```

The actual fixed class breaks in the `items` list are still what determine the colors.

## Do not click Classify afterward

After the script applies the style, do not press **Classify** in the QGIS raster symbology panel unless you intentionally want QGIS to rebuild the classes.

The script already creates the exact discrete break values.

Pressing **Classify** can replace them with automatically calculated intervals.

## Troubleshooting

### No layer selected

If the console shows an error saying no layer is selected, click the DEM in the Layers panel and run the script again.

### Selected layer is not a raster

Make sure the active layer is your DEM raster and not a vector layer, basemap, boundary shapefile, or other layer type.

### DEM does not change color

Check the Python Console output.

You should see:

```text
Renderer: singlebandpseudocolor
Interpolation: DISCRETE
```

If you do, open:

**Layer Properties → Symbology**

and confirm that the render type is **Singleband pseudocolor**.

### Negative values are not visible

This is intentional. Values below 0 m are assigned a fully transparent color.

If you want negative values visible, replace:

```python
QColor(0, 0, 0, 0)
```

with an opaque color such as:

```python
QColor("#5DADE2")
```

### Python Console reports an enum error

The current script is intended for modern QGIS 3.x versions using:

```python
Qgis.ShaderInterpolationMethod.Discrete
Qgis.ShaderClassificationMethod.Continuous
```

If using a significantly older QGIS version, these enum names may differ.

## Main PyQGIS classes used

The script relies on:

```python
QgsRasterLayer
QgsRasterShader
QgsColorRampShader
QgsSingleBandPseudoColorRenderer
QColor
iface
```

The renderer is created with:

```python
renderer = QgsSingleBandPseudoColorRenderer(
    layer.dataProvider(),
    1,
    raster_shader
)
```

and applied with:

```python
layer.setRenderer(renderer)
layer.triggerRepaint()
```

The QGIS interface is then refreshed using:

```python
iface.layerTreeView().refreshLayerSymbology(layer.id())
iface.mapCanvas().refresh()
```

## Notes

- The script styles band 1 of the selected raster.
- The script does not modify raster pixel values.
- The script does not write a new TIFF.
- The script does not require a QML or TXT color-map file.
- The style exists in the current QGIS layer/project after the script runs.
- If you want to reuse the applied style, you can save it from QGIS using **Layer Properties → Style → Save Style**.

## Repository

`Heed725/QGIS-DEM-Colorizer-Script`

This repository is intended as a simple reusable PyQGIS example for applying fixed DEM elevation classes directly from the QGIS Python Console.
