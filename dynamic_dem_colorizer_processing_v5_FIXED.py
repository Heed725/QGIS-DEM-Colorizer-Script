# -*- coding: utf-8 -*-
"""
Dynamic DEM Colorizer v5 - FIXED IN-PLACE COLORING
QGIS 3.38 / 3.40 / 3.44+

IMPORTANT FIXES
---------------
1. Runs in the QGIS main thread using FlagNoThreading.
2. Finds and styles the ACTUAL raster layer already loaded in the project.
3. Rebuilds a renderer for every matching visible/project raster.
4. Forces legend and map canvas refresh after styling.
5. Keeps the Tanzania style as the checked default.
6. Untick default colors to use the editable class table.
7. No TXT import option.
"""

import os

from qgis.core import (
    Qgis,
    QgsColorRampShader,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputString,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterMatrix,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProject,
    QgsRasterLayer,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
)
from qgis.PyQt.QtGui import QColor


class DynamicDEMColorizerV5(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    USE_DEFAULT = "USE_DEFAULT"
    TRANSPARENT_BELOW = "TRANSPARENT_BELOW"
    CLASS_TABLE = "CLASS_TABLE"
    SAVE_LAYER_DEFAULT = "SAVE_LAYER_DEFAULT"
    EXPORT_QML = "EXPORT_QML"

    # ----------------------------------------------------------
    # Built-in Tanzania scheme
    # Each tuple:
    # (upper break, color, alpha, label)
    # ----------------------------------------------------------
    TANZANIA_DEFAULT = [
        (-0.000001, "#000000", 0,   "Below 0 m"),
        (100.0,     "#A9CD6F", 255, "0 - 100 m"),
        (200.0,     "#CCDD89", 255, "101 - 200 m"),
        (500.0,     "#F7E8A3", 255, "201 - 500 m"),
        (1000.0,    "#F9D58D", 255, "501 - 1000 m"),
        (1500.0,    "#E7B882", 255, "1001 - 1500 m"),
        (2000.0,    "#E09762", 255, "1501 - 2000 m"),
        (3000.0,    "#C87C52", 255, "2001 - 3000 m"),
        (4000.0,    "#B15E38", 255, "3001 - 4000 m"),
        (5786.0,    "#A65235", 255, "Above 4000 m"),
    ]

    # Default editable rows shown when the dialog opens.
    EDITABLE_DEFAULTS = [
        [100,  "#A9CD6F", "0 - 100 m"],
        [200,  "#CCDD89", "101 - 200 m"],
        [500,  "#F7E8A3", "201 - 500 m"],
        [1000, "#F9D58D", "501 - 1000 m"],
        [1500, "#E7B882", "1001 - 1500 m"],
        [2000, "#E09762", "1501 - 2000 m"],
        [3000, "#C87C52", "2001 - 3000 m"],
        [4000, "#B15E38", "3001 - 4000 m"],
        [5786, "#A65235", "Above 4000 m"],
    ]

    def name(self):
        return "dynamic_dem_colorizer_v5"

    def displayName(self):
        return "Dynamic DEM Colorizer - FIXED"

    def group(self):
        return "Cartography"

    def groupId(self):
        return "cartography"

    def createInstance(self):
        return DynamicDEMColorizerV5()

    def flags(self):
        # This tool changes project layer renderers and refreshes the GUI.
        # Force Processing to run in QGIS's main thread.
        try:
            return super().flags() | QgsProcessingAlgorithm.FlagNoThreading
        except AttributeError:
            try:
                return super().flags() | Qgis.ProcessingAlgorithmFlag.NoThreading
            except Exception:
                return super().flags()

    def shortHelpString(self):
        return (
            "Colorizes the selected DEM directly in the current QGIS project.\n\n"
            "DEFAULT MODE:\n"
            "Leave 'Use built-in Tanzania default colors' checked.\n\n"
            "CUSTOM MODE:\n"
            "Untick it, then edit/add/remove elevation rows.\n\n"
            "Editable table columns:\n"
            "Upper limit (m) | Color (#RRGGBB) | Legend label\n\n"
            "This version modifies the actual project raster and refreshes "
            "the map canvas immediately."
        )

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                "DEM raster",
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.USE_DEFAULT,
                "Use built-in Tanzania default colors",
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TRANSPARENT_BELOW,
                "Custom mode: make values below this elevation transparent (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterMatrix(
                self.CLASS_TABLE,
                "Custom mode: elevation classes and colors",
                numberRows=len(self.EDITABLE_DEFAULTS),
                hasFixedNumberRows=False,
                headers=[
                    "Upper limit (m)",
                    "Color (#RRGGBB)",
                    "Legend label",
                ],
                defaultValue=self.EDITABLE_DEFAULTS,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SAVE_LAYER_DEFAULT,
                "Save resulting symbology as raster default style",
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.EXPORT_QML,
                "Also export QML beside the DEM",
                defaultValue=True,
            )
        )

        self.addOutput(
            QgsProcessingOutputString(
                "STATUS",
                "Status",
            )
        )

        self.addOutput(
            QgsProcessingOutputString(
                "QML_PATH",
                "Exported QML path",
            )
        )

    # ----------------------------------------------------------
    # QGIS enum compatibility
    # ----------------------------------------------------------
    def _discrete(self):
        try:
            return Qgis.ShaderInterpolationMethod.Discrete
        except AttributeError:
            return QgsColorRampShader.Discrete

    def _continuous_classification(self):
        try:
            return Qgis.ShaderClassificationMethod.Continuous
        except AttributeError:
            return QgsColorRampShader.Continuous

    # ----------------------------------------------------------
    # Normalize a raster source for matching loaded project layer
    # ----------------------------------------------------------
    def _clean_source(self, source):
        if not source:
            return ""
        return os.path.normcase(
            os.path.normpath(
                str(source).split("|")[0]
            )
        )

    # ----------------------------------------------------------
    # Locate the actual project raster(s)
    # ----------------------------------------------------------
    def _project_targets(self, input_layer):

        project = QgsProject.instance()
        targets = []

        # First preference: exact layer id exists in the project.
        project_layer = project.mapLayer(input_layer.id())

        if isinstance(project_layer, QgsRasterLayer):
            targets.append(project_layer)

        # Second preference: match source path/URI.
        input_source = self._clean_source(input_layer.source())

        if input_source:
            for layer in project.mapLayers().values():

                if not isinstance(layer, QgsRasterLayer):
                    continue

                if self._clean_source(layer.source()) == input_source:
                    if all(layer.id() != x.id() for x in targets):
                        targets.append(layer)

        # Fallback: at least style the layer returned by Processing.
        if not targets:
            targets.append(input_layer)

        return targets

    # ----------------------------------------------------------
    # Default shader items
    # ----------------------------------------------------------
    def _default_items(self):

        items = []

        for value, hex_color, alpha, label in self.TANZANIA_DEFAULT:

            if alpha == 0:
                color = QColor(0, 0, 0, 0)
            else:
                color = QColor(hex_color)
                color.setAlpha(alpha)

            items.append(
                QgsColorRampShader.ColorRampItem(
                    float(value),
                    color,
                    label,
                )
            )

        return items

    # ----------------------------------------------------------
    # Parse editable table
    # ----------------------------------------------------------
    def _custom_items(
        self,
        parameters,
        context,
        transparent_below,
    ):

        raw = self.parameterAsMatrix(
            parameters,
            self.CLASS_TABLE,
            context,
        )

        if not raw:
            raise QgsProcessingException(
                "The custom elevation table is empty."
            )

        # Matrix may be nested or flattened depending on QGIS build.
        if isinstance(raw[0], (list, tuple)):
            rows = list(raw)
        else:
            if len(raw) % 3 != 0:
                raise QgsProcessingException(
                    "Custom class table could not be read."
                )

            rows = [
                raw[i:i + 3]
                for i in range(0, len(raw), 3)
            ]

        parsed = []

        for row_no, row in enumerate(rows, start=1):

            if len(row) < 3:
                continue

            upper_raw, color_raw, label_raw = row[:3]

            # Ignore blank rows.
            if (
                str(upper_raw).strip() == ""
                and str(color_raw).strip() == ""
                and str(label_raw).strip() == ""
            ):
                continue

            try:
                upper = float(upper_raw)
            except (TypeError, ValueError):
                raise QgsProcessingException(
                    f"Row {row_no}: '{upper_raw}' is not a valid elevation."
                )

            color_text = str(color_raw).strip()
            color = QColor(color_text)

            if not color.isValid():
                raise QgsProcessingException(
                    f"Row {row_no}: '{color_text}' is not a valid QGIS color. "
                    "Use #RRGGBB, e.g. #A9CD6F."
                )

            label = str(label_raw).strip()

            if not label:
                label = f"<= {upper:g} m"

            parsed.append(
                (upper, color, label)
            )

        if not parsed:
            raise QgsProcessingException(
                "No valid custom elevation classes were found."
            )

        parsed.sort(key=lambda x: x[0])

        values = [x[0] for x in parsed]

        if len(values) != len(set(values)):
            raise QgsProcessingException(
                "Custom classes contain duplicate upper limits."
            )

        # Add transparent item immediately below the threshold.
        items = [
            QgsColorRampShader.ColorRampItem(
                float(transparent_below) - 0.000001,
                QColor(0, 0, 0, 0),
                f"Below {transparent_below:g} m",
            )
        ]

        for upper, color, label in parsed:

            if upper < transparent_below:
                continue

            items.append(
                QgsColorRampShader.ColorRampItem(
                    float(upper),
                    color,
                    label,
                )
            )

        if len(items) < 2:
            raise QgsProcessingException(
                "All custom classes are below the transparency threshold."
            )

        return items

    # ----------------------------------------------------------
    # Create a fresh renderer for ONE target raster
    # ----------------------------------------------------------
    def _make_renderer(self, layer, items):

        shader_min = float(items[0].value)
        shader_max = float(items[-1].value)

        shader = QgsColorRampShader(
            shader_min,
            shader_max,
            None,
            self._discrete(),
            self._continuous_classification(),
        )

        shader.setClip(False)

        # Fresh item objects/colors for this renderer.
        cloned_items = []

        for item in items:
            cloned_items.append(
                QgsColorRampShader.ColorRampItem(
                    float(item.value),
                    QColor(item.color),
                    str(item.label),
                )
            )

        shader.setColorRampItemList(cloned_items)

        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(shader)

        renderer = QgsSingleBandPseudoColorRenderer(
            layer.dataProvider(),
            1,
            raster_shader,
        )

        # Actual min/max for display metadata only.
        try:
            stats = layer.dataProvider().bandStatistics(1)
            renderer.setClassificationMin(float(stats.minimumValue))
            renderer.setClassificationMax(float(stats.maximumValue))
        except Exception:
            pass

        return renderer

    # ----------------------------------------------------------
    # QML location
    # ----------------------------------------------------------
    def _qml_path(self, layer):

        source = str(layer.source()).split("|")[0]

        if source and os.path.isfile(source):

            folder = os.path.dirname(source)
            base = os.path.splitext(
                os.path.basename(source)
            )[0]

            return os.path.join(
                folder,
                base + "_Dynamic_DEM_Style.qml",
            )

        return os.path.join(
            os.path.expanduser("~"),
            "Dynamic_DEM_Style.qml",
        )

    # ----------------------------------------------------------
    # Main
    # ----------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):

        input_layer = self.parameterAsRasterLayer(
            parameters,
            self.INPUT,
            context,
        )

        if input_layer is None or not isinstance(input_layer, QgsRasterLayer):
            raise QgsProcessingException(
                "Please choose a valid raster DEM."
            )

        if not input_layer.isValid():
            raise QgsProcessingException(
                "The DEM raster is invalid."
            )

        use_default = self.parameterAsBoolean(
            parameters,
            self.USE_DEFAULT,
            context,
        )

        transparent_below = self.parameterAsDouble(
            parameters,
            self.TRANSPARENT_BELOW,
            context,
        )

        if use_default:
            items = self._default_items()
            source_mode = "Built-in Tanzania default colors"
        else:
            items = self._custom_items(
                parameters,
                context,
                transparent_below,
            )
            source_mode = "Editable custom class table"

        targets = self._project_targets(input_layer)

        feedback.pushInfo(
            f"Found {len(targets)} raster layer(s) to colorize."
        )

        feedback.pushInfo(
            "Color source: " + source_mode
        )

        # ------------------------------------------------------
        # Apply style to every real project target
        # ------------------------------------------------------
        for target in targets:

            renderer = self._make_renderer(
                target,
                items,
            )

            target.setRenderer(renderer)
            target.setOpacity(1.0)
            target.triggerRepaint()

            # Notify QGIS that style changed.
            try:
                target.styleChanged.emit()
            except Exception:
                pass

            feedback.pushInfo(
                "Colorized project layer: " + target.name()
            )

        # ------------------------------------------------------
        # Force QGIS GUI refresh
        # ------------------------------------------------------
        try:
            from qgis.utils import iface

            for target in targets:
                iface.layerTreeView().refreshLayerSymbology(
                    target.id()
                )

            iface.mapCanvas().clearCache()
            iface.mapCanvas().refreshAllLayers()
            iface.mapCanvas().refresh()

        except Exception as exc:
            feedback.pushInfo(
                "Canvas refresh note: " + str(exc)
            )

        # ------------------------------------------------------
        # Save default style on the first actual project target
        # ------------------------------------------------------
        target_for_save = targets[0]

        if self.parameterAsBoolean(
            parameters,
            self.SAVE_LAYER_DEFAULT,
            context,
        ):

            try:
                result = target_for_save.saveDefaultStyle()

                feedback.pushInfo(
                    "Default style save result: " + str(result)
                )

            except Exception as exc:

                feedback.reportError(
                    "Could not save default style: "
                    + str(exc)
                )

        # ------------------------------------------------------
        # Export QML
        # ------------------------------------------------------
        qml_path = ""

        if self.parameterAsBoolean(
            parameters,
            self.EXPORT_QML,
            context,
        ):

            qml_path = self._qml_path(
                target_for_save
            )

            try:
                result = target_for_save.saveNamedStyle(
                    qml_path
                )

                feedback.pushInfo(
                    "QML save result: " + str(result)
                )

                if os.path.isfile(qml_path):
                    feedback.pushInfo(
                        "QML created: " + qml_path
                    )
                else:
                    feedback.reportError(
                        "QML was requested but the expected file "
                        "was not found."
                    )

            except Exception as exc:

                feedback.reportError(
                    "QML export failed: " + str(exc)
                )

                qml_path = ""

        # ------------------------------------------------------
        # Log renderer verification
        # ------------------------------------------------------
        feedback.pushInfo("")
        feedback.pushInfo("STYLE VERIFICATION")

        for target in targets:

            current_renderer = target.renderer()

            feedback.pushInfo(
                f"{target.name()} renderer = "
                f"{current_renderer.type() if current_renderer else 'NONE'}"
            )

        feedback.pushInfo("")
        feedback.pushInfo("FINAL CLASS BREAKS")

        for item in items:

            c = item.color

            feedback.pushInfo(
                f"{item.value:g} | "
                f"RGBA({c.red()},{c.green()},{c.blue()},{c.alpha()}) | "
                f"{item.label}"
            )

        return {
            "STATUS": (
                f"Colorized {len(targets)} project raster layer(s)"
            ),
            "QML_PATH": qml_path,
        }
