import arcpy
from arcpy.sa import *

# === CONFIGURACIÓN INICIAL ===
arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = r"C:/tyaid"
arcpy.env.overwriteOutput = True

# === RUTAS DE ARCHIVOS ===
chm = "chm.tif"
chm_filtered = "chm_filtered.tif"
chm_smooth = "chm_smooth.tif"
local_max = "local_max.tif"
seed_points = "seeds.shp"
seed_raster = "seed_raster.tif"
inverted_chm = "inverted_chm.tif"
watershed_result = "tree_crowns.tif"
shapefile_output = "tree_crowns.shp"

# === 1. FILTRAR ALTURAS < 4M ===
filtered = Con(Raster(chm) > 4, Raster(chm))
filtered.save(chm_filtered)

# === 2. SUAVIZADO CON MEDIA MÓVIL ===
smooth = FocalStatistics(chm_filtered, NbrRectangle(3, 3, "CELL"), "MEAN", "DATA")
smooth.save(chm_smooth)

# === 3. DETECCIÓN DE PUNTOS MÁXIMOS ===
local_maxima = Con(
    Raster(chm_smooth) == FocalStatistics(chm_smooth, NbrRectangle(3, 3, "CELL"), "MAXIMUM"),
    1
)
local_maxima.save(local_max)

# === 4. CONVERTIR PUNTOS MÁXIMOS A SHAPE ===
arcpy.RasterToPoint_conversion(local_max, seed_points, "Value")

# === 5. CONVERTIR SHAPE A RÁSTER DE SEMILLAS (FID COMO ID) ===
arcpy.PointToRaster_conversion(seed_points, "FID", seed_raster, cell_assignment="MAXIMUM", cellsize=Raster(chm).meanCellWidth)

# === 6. INVERTIR CHM (REQUIERE FLOWDIRECTION) ===
inverted = Times(chm_smooth, -1)
inverted.save(inverted_chm)

# === 7. CREAR FLOWDIRECTION + WATERSHED ===
flow_dir = FlowDirection(inverted)
crowns_raster = Watershed(flow_dir, Raster(seed_raster))
crowns_raster.save(watershed_result)

# === 8. CONVERTIR RESULTADO FINAL A SHAPEFILE ===
arcpy.RasterToPolygon_conversion(watershed_result, shapefile_output, "NO_SIMPLIFY", "VALUE")

print("✅ Segmentación terminada. Copas exportadas a shapefile:", shapefile_output)



# === BINARIO: 1 donde CHM > 4, 0 en el resto ===
chm_binary = "chm_binary.tif"
binary_raster = Con(Raster(chm) > 4, 1, 0)
binary_raster.save(chm_binary)

print("✅ Raster binario generado:", chm_binary)



import arcpy
from arcpy.sa import *

# === CONFIGURACIÓN ===
arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = r"C:/tyaid"
arcpy.env.overwriteOutput = True

# === RUTAS ===
chm = "chm.tif"
chm_binary = "chm_binary.tif"
chm_binary_vector_all = "chm_binary_all.shp"
chm_binary_vector_1only = "chm_binary_1only.shp"

# === 1. CREAR RASTER BINARIO (1 si CHM > 4, 0 en otro caso) ===
binary_raster = Con(Raster(chm) > 4, 1, 0)
binary_raster.save(chm_binary)

# === 2. CONVERTIR A POLÍGONO (incluye zonas con 0 y 1) ===
arcpy.RasterToPolygon_conversion(chm_binary, chm_binary_vector_all, "NO_SIMPLIFY", "Value")

# === 3. FILTRAR SOLO POLÍGONOS CON GRIDCODE = 1 ===
arcpy.MakeFeatureLayer_management(chm_binary_vector_all, "bin_layer", '"GRIDCODE" = 1')
arcpy.CopyFeatures_management("bin_layer", chm_binary_vector_1only)

print("✅ Polígonos creados solo para zonas CHM > 4m:", chm_binary_vector_1only)


import arcpy

arcpy.env.workspace = r"C:/tyaid"
arcpy.env.overwriteOutput = True

# Archivos de entrada
segmentacion = "tree_crowns.shp"          # Resultado segmentación
zonas_altas = "chm_binary_1only.shp"      # Zonas CHM > 4 m

# Archivo de salida
interseccion_out = "segmentacion_1.shp"

# Ejecutar intersección
arcpy.Intersect_analysis([segmentacion, zonas_altas], interseccion_out)

print(f"✅ Intersección completada. Resultado guardado en: {interseccion_out}")


import arcpy

arcpy.env.workspace = r"C:/tyaid"
arcpy.env.overwriteOutput = True

# Shapefile donde quieres agregar el campo y calcular área
segmentacion = "segmentacion_1.shp"

# 1. Añadir campo sup_m2 (si no existe)
fields = [f.name for f in arcpy.ListFields(segmentacion)]
if "sup_m2" not in fields:
    arcpy.AddField_management(segmentacion, "sup_m2", "DOUBLE")
    print("Campo 'sup_m2' creado.")

# 2. Calcular área en metros cuadrados y guardar en sup_m2
# Suponiendo que el sistema de coordenadas es proyectado en metros
arcpy.CalculateField_management(segmentacion, "sup_m2", "!shape.area!", "PYTHON3")

print("Área calculada y guardada en campo 'sup_m2'.")


# Por último elimino los poligonos de la capa con superficie menor a 25 m2 por ejemplo


