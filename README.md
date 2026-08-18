# QGIS DEM Colorizer Script

A QGIS Processing Toolbox script for applying discrete elevation classes and colors directly to a DEM raster loaded in the current QGIS project.

The script includes a built-in Tanzania elevation scheme, but the class breaks, colors, transparency threshold, and legend labels can also be edited before running.

## Main features

- Applies colors directly to the visible DEM layer in the current QGIS project.
- Uses `QgsSingleBandPseudoColorRenderer` with a discrete color ramp.
- Runs in the QGIS main thread using `FlagNoThreading` so the project layer and map canvas can be updated safely.
- Automatically refreshes the layer legend and map canvas after styling.
- Includes a built-in Tanzania DEM color scheme enabled by default.
- Allows the user to untick the default scheme and define custom elevation classes.
- Supports editable upper elevation limits, hexadecimal colors, and legend labels.
- Supports adding and removing custom class rows.
- Makes values below a chosen threshold transparent in custom mode.
- Can save the resulting symbology as the raster's default style.
- Can export a `.qml` style beside the source DEM.
- Designed for QGIS 3.38, 3.40, 3.44 and compatible QGIS 3.x releases.

## Default Tanzania elevation colors

| Elevation class | Color |
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

The built-in final break is 5786 m, matching the Tanzania DEM used during development.

## File

The Processing script is:

```text
dynamic_dem_colorizer_processing_v5_FIXED.py
```

## Installation

### Method 1: Copy into the QGIS Processing scripts folder

1. Download `dynamic_dem_colorizer_processing_v5_FIXED.py`.
2. Open QGIS.
3. Go to:

   **Settings → User Profiles → Open Active Profile Folder**

4. Open the following folder inside the profile:

```text
processing\scripts
```

5. Copy `dynamic_dem_colorizer_processing_v5_FIXED.py` into that folder.
6. Return to QGIS.
7. Open the **Processing Toolbox**.
8. Refresh the Processing scripts if necessary, or restart QGIS.
9. Look under:

```text
Cartography
└── Dynamic DEM Colorizer - FIXED
```

### Typical Windows profile location

A common QGIS profile path is similar to:

```text
C:\Users\YOUR_USERNAME\AppData\Roaming\QGIS\QGIS3\profiles\default\processing\scripts
```

The exact profile can differ, so using **Open Active Profile Folder** is safer.

## Basic use

1. Load your DEM `.tif` into QGIS.
2. Open **Processing Toolbox**.
3. Search for:

```text
Dynamic DEM Colorizer - FIXED
```

4. Choose the DEM raster.
5. Leave **Use built-in Tanzania default colors** checked if you want the default scheme.
6. Leave **Save resulting symbology as raster default style** checked if you want QGIS to remember the style.
7. Leave **Also export QML beside the DEM** checked if you want a reusable `.qml` file.
8. Click **Run**.

The DEM should immediately change to the pseudocolor elevation rendering in the map canvas.

## Custom elevation classes

To define your own classes:

1. Untick:

```text
Use built-in Tanzania default colors
```

2. Set the value for:

```text
Custom mode: make values below this elevation transparent (m)
```

3. Edit the custom class table.

The table has three columns:

| Column | Meaning |
|---|---|
| Upper limit (m) | Highest raster value in that class |
| Color (#RRGGBB) | Hexadecimal QGIS color |
| Legend label | Text shown in the layer legend |

Example:

| Upper limit | Color | Legend label |
|---:|---|---|
| 100 | `#A9CD6F` | 0 - 100 m |
| 200 | `#CCDD89` | 101 - 200 m |
| 500 | `#F7E8A3` | 201 - 500 m |
| 1000 | `#F9D58D` | 501 - 1000 m |

The algorithm automatically sorts custom class rows by elevation.

Duplicate upper limits are rejected because every discrete break must be unique.

## How the class breaks work

The script uses QGIS discrete pseudocolor rendering. Each class value acts as the upper break for that class.

For example:

```text
100   #A9CD6F   0 - 100 m
200   #CCDD89   101 - 200 m
500   #F7E8A3   201 - 500 m
```

is interpreted as sequential discrete elevation classes ending at 100 m, 200 m, and 500 m.

## Transparency

In the built-in Tanzania mode:

```text
Below 0 m = transparent
```

In custom mode, the user can change the transparency threshold.

For example, setting:

```text
Transparent below = 10
```

will make values below approximately 10 m transparent before the visible custom classes begin.

## Save as default style

The option:

```text
Save resulting symbology as raster default style
```

is enabled by default.

When enabled, the script calls QGIS `saveDefaultStyle()` after applying the renderer.

If you do not want the style saved as the raster default, untick this option before running.

## Export QML

The option:

```text
Also export QML beside the DEM
```

is enabled by default.

For a raster such as:

```text
tanzania_elevation.tif
```

the script attempts to create:

```text
tanzania_elevation_Dynamic_DEM_Style.qml
```

in the same directory as the raster.

The QML can later be loaded from:

**Layer Properties → Style → Load Style**

## Why this version uses `FlagNoThreading`

QGIS Processing algorithms normally may execute in a background thread.

This script modifies the renderer of an existing project layer and refreshes the QGIS interface, so it requests execution in the main QGIS thread with `FlagNoThreading`.

This helps ensure that the visible project raster, legend, and map canvas are updated rather than only styling a temporary Processing layer reference.

## How the script finds the visible DEM

The tool first checks whether the selected raster's layer ID exists in the current `QgsProject`.

If necessary, it then compares raster source paths to find matching project layers.

This means the style is applied to the raster actually visible in your Layers panel.

## Processing log verification

After running, the Processing log reports information similar to:

```text
Found 1 raster layer(s) to colorize.
Color source: Built-in Tanzania default colors
Colorized project layer: tanzania_elevation

STYLE VERIFICATION
tanzania_elevation renderer = singlebandpseudocolor
```

It also prints the final RGBA class values and labels.

## Troubleshooting

### Tool does not appear in Processing Toolbox

Confirm the Python file is inside:

```text
processing\scripts
```

Then refresh Processing scripts or restart QGIS.

### DEM does not change color

Make sure the DEM is already loaded in the QGIS project and select the same raster in the Processing algorithm.

After running, check the Processing log. You should see:

```text
renderer = singlebandpseudocolor
```

### Colors disappear after clicking Classify

Do not click **Classify** after the script runs. The script already creates the required discrete break values.

Running QGIS classification afterward can replace the custom break values.

### QML is not created

Check that the folder containing the DEM is writable. If the raster directory is read-only, QGIS may not be able to save a QML beside it.

### Default style cannot be saved

The style is still applied to the current project layer even if the default-style save operation fails. Check the QGIS Processing log for the exact message.

## Requirements

- QGIS 3.x
- PyQGIS
- A raster DEM, normally a single-band elevation TIFF

No third-party Python packages are required.

## Repository structure

```text
QGIS-DEM-Colorizer-Script/
├── dynamic_dem_colorizer_processing_v5_FIXED.py
└── README.md
```

## License

No license file has been added yet. Add a license if you plan to redistribute or publish the script under explicit reuse terms.

## Author / repository

Repository: `Heed725/QGIS-DEM-Colorizer-Script`

Built as a reusable QGIS Processing workflow for DEM elevation cartography.
