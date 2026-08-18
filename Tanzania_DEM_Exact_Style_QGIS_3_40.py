# ============================================================
# Tanzania DEM exact elevation style
# QGIS 3.38 / 3.40 / 3.44 compatible
# ============================================================
#
# Select the DEM raster in the Layers panel BEFORE running.
#
# Exact classes:
#   < 0 m          = transparent
#   0 - 100 m      = #A9CD6F
#   101 - 200 m    = #CCDD89
#   201 - 500 m    = #F7E8A3
#   501 - 1000 m   = #F9D58D
#   1001 - 1500 m  = #E7B882
#   1501 - 2000 m  = #E09762
#   2001 - 3000 m  = #C87C52
#   3001 - 4000 m  = #B15E38
#   > 4000 m       = #A65235
#
# Run in QGIS Python Console:
# exec(open(r"C:\Users\Admin\Downloads\Tanzania_DEM_Exact_Style_QGIS_3_40.py").read())
# ============================================================

from qgis.core import (
    Qgis,
    QgsRasterLayer,
    QgsRasterShader,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer
)
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface


# ------------------------------------------------------------
# 1. Get selected raster
# ------------------------------------------------------------
layer = iface.activeLayer()

if layer is None:
    raise Exception(
        "No layer selected. Click your DEM raster (for example tanzania_elevation) "
        "in the Layers panel, then run the script again."
    )

if not isinstance(layer, QgsRasterLayer):
    raise Exception(
        "The selected layer is not a raster. Select the DEM TIFF and run again."
    )

if not layer.isValid():
    raise Exception("The selected DEM raster is not valid.")

band = 1


# ------------------------------------------------------------
# 2. Create the discrete shader
#
# IMPORTANT:
# In QGIS DISCRETE mode, each item value is the UPPER LIMIT
# and QGIS uses the color of that item for values up to it.
#
# The first item is transparent and ends just below zero.
# ------------------------------------------------------------
shader = QgsColorRampShader(
    -776.0,
    1000000000.0,
    None,
    Qgis.ShaderInterpolationMethod.Discrete,
    Qgis.ShaderClassificationMethod.Continuous
)

shader.setClip(False)


# ------------------------------------------------------------
# 3. Exact class breaks
# ------------------------------------------------------------
items = [
    # Everything below zero is transparent
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

    QgsColorRampShader.ColorRampItem(
        500.0,
        QColor("#F7E8A3"),
        "201 - 500 m"
    ),

    QgsColorRampShader.ColorRampItem(
        1000.0,
        QColor("#F9D58D"),
        "501 - 1000 m"
    ),

    QgsColorRampShader.ColorRampItem(
        1500.0,
        QColor("#E7B882"),
        "1001 - 1500 m"
    ),

    QgsColorRampShader.ColorRampItem(
        2000.0,
        QColor("#E09762"),
        "1501 - 2000 m"
    ),

    QgsColorRampShader.ColorRampItem(
        3000.0,
        QColor("#C87C52"),
        "2001 - 3000 m"
    ),

    QgsColorRampShader.ColorRampItem(
        4000.0,
        QColor("#B15E38"),
        "3001 - 4000 m"
    ),

    # Large upper value means every DEM value above 4000
    # receives the final dark-brown color.
    QgsColorRampShader.ColorRampItem(
        1000000000.0,
        QColor("#A65235"),
        "Above 4000 m"
    ),
]

shader.setColorRampItemList(items)


# ------------------------------------------------------------
# 4. Put shader into raster renderer
# ------------------------------------------------------------
raster_shader = QgsRasterShader()
raster_shader.setRasterShaderFunction(shader)

renderer = QgsSingleBandPseudoColorRenderer(
    layer.dataProvider(),
    band,
    raster_shader
)

# Explicit classification limits
renderer.setClassificationMin(-776.0)
renderer.setClassificationMax(5786.0)


# ------------------------------------------------------------
# 5. Apply renderer
# ------------------------------------------------------------
layer.setRenderer(renderer)
layer.triggerRepaint()

iface.layerTreeView().refreshLayerSymbology(layer.id())
iface.mapCanvas().refresh()


# ------------------------------------------------------------
# 6. Verify what QGIS actually received
# ------------------------------------------------------------
print("")
print("==============================================")
print("TANZANIA DEM STYLE APPLIED SUCCESSFULLY")
print("==============================================")
print("Layer:", layer.name())
print("Renderer:", layer.renderer().type())
print("Interpolation:", shader.colorRampTypeAsQString())
print("")
print("Exact classes loaded:")

for item in shader.colorRampItemList():
    c = item.color
    print(
        f"{item.label:20s} | "
        f"break={item.value} | "
        f"RGBA={c.red()},{c.green()},{c.blue()},{c.alpha()}"
    )

print("")
print("Expected renderer: singlebandpseudocolor")
print("Expected interpolation: DISCRETE")
print("Do NOT click Classify after running this script.")
print("==============================================")
