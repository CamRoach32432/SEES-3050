"""Assignment 3: Spatial Overlays and Areal Interpolation.
Complete three functions using ArcPy and pathlib.Path. Prepare and project
copies before analysis; preserve inputs and avoid hardcoded paths or values.
Check input paths, geometry types, fields, coordinate systems, and output names.
Use try/except handling to catch and report errors.
Find and download census boundaries, a census/ACS numeric attribute, and roads (or another dataset with line geometry).
"""


def hawkid():
    return ["Cameron Roach", "clroach"]

import os
import arcpy
# Problem 1 (20 points)
def prepare_data(in_features, gdb_path, out_sr,
                     csv_path=None, join_field=None, value_field=None):
    """Create or reuse the geodatabase; import and project one feature dataset.
    Use the input base name and return the prepared feature class path.
    For polygons, import a CSV's ID attribute and one numeric value
    and join that value using the join_field that . Supply all three join
    arguments together. Preserve inputs and reject existing output names.
    """
    join_args = [csv_path, join_field, value_field]
    if any(join_args) and not all(join_args):
        raise ValueError("Supply csv_path, join_field, and value_field together.")

    if not arcpy.Exists(in_features):
        raise ValueError("Input features not found.")
    if csv_path and not os.path.isfile(csv_path):
        raise ValueError("CSV not found.")
    if csv_path and arcpy.Describe(in_features).shapeType != "Polygon":
        raise ValueError("The join only works on polygons.")

    if not arcpy.Exists(gdb_path):
        arcpy.management.CreateFileGDB(os.path.dirname(gdb_path),
                                       os.path.basename(gdb_path))

    base = os.path.splitext(os.path.basename(in_features))[0]
    out_fc = os.path.join(gdb_path, arcpy.ValidateTableName(base, gdb_path))

    if arcpy.Exists(out_fc):
        raise ValueError(out_fc + " already exists.")
    if csv_path:
        csv_base = os.path.splitext(os.path.basename(csv_path))[0]
        csv_table = os.path.join(gdb_path, arcpy.ValidateTableName(csv_base, gdb_path))
        if arcpy.Exists(csv_table):
            raise ValueError(csv_table + " already exists.")

    arcpy.management.Project(in_features, out_fc, out_sr)

    if csv_path:
        arcpy.conversion.ExportTable(csv_path, csv_table)
        arcpy.management.AddField(csv_table, "JOIN_ID", "TEXT", field_length=20)
        arcpy.management.CalculateField(csv_table, "JOIN_ID",
                                        "str(int(!" + join_field + "!))", "PYTHON3")
        arcpy.management.JoinField(out_fc, join_field, csv_table,
                                   "JOIN_ID", [value_field])
    return out_fc


folder = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3"

result = prepare_data(
    os.path.join(folder, "block_groups.shp"),
    os.path.join(folder, "chp12data.gdb"),
    arcpy.SpatialReference(26915),
    os.path.join(folder, "population.csv"),
    "GEOID",
    "POP_TOTAL",
)
print(result)

from pathlib import Path
gdb = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3\chp12data.gdb"
bg = os.path.join(gdb, "block_groups")
sites = os.path.join(gdb, "sites")
buffer_fc = os.path.join(gdb, "buffer")
sr = arcpy.Describe(bg).spatialReference
def fc(name):
    return str(Path(gdb) / name)
out_coordinate_system = arcpy.SpatialReference(26915)
zone = fc("dissolved_risk_zone")

import random

# no EPA TRI records or actual release measurements.
N_SITES = 10
SEED = 15
BUFFER_METERS = 2000
with arcpy.da.SearchCursor(bg, ["GEOID", "SHAPE@"]) as rows:
    candidates = sorted(list(rows), key=lambda row: row[0])
if not 1 <= N_SITES <= len(candidates):
    raise ValueError("N_SITES must be between 1 and the number of block groups.")
chosen = random.Random(SEED).sample(candidates, N_SITES)
for number, (geoid, geometry) in enumerate(chosen, 1):
    print(number, geometry.labelPoint)

sites = fc("hypothetical_tri_sites")
if arcpy.Exists(sites):
    arcpy.management.Delete(sites)
arcpy.management.CreateFeatureclass(gdb, "hypothetical_tri_sites", "POINT", spatial_reference=out_coordinate_system)
arcpy.management.AddField(sites, "SITE_ID", "LONG")
arcpy.management.AddField(sites, "SITE_NAME", "TEXT", field_length=60)
arcpy.management.AddField(sites, "BG_GEOID", "TEXT", field_length=12)
with arcpy.da.InsertCursor(sites, ["SHAPE@", "SITE_ID", "SITE_NAME", "BG_GEOID"]) as rows:
    for number, (geoid, geometry) in enumerate(chosen, 1):
        point = arcpy.PointGeometry(geometry.labelPoint, out_coordinate_system)
        rows.insertRow([point, number, f"Hypothetical site {number}", geoid])
# Interior representative points of sampled block groups, not random industrial locations.
print("Hypothetical sites:", N_SITES)

DATA_FOLDER = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3"
sites_shp = str(Path(DATA_FOLDER) / 'tri_sites.shp')
if arcpy.Exists(sites_shp):
    arcpy.management.Delete(sites_shp)
print(sites_shp)
arcpy.management.CreateFeatureclass(str(DATA_FOLDER), "tri_sites.shp", "POINT", spatial_reference=out_coordinate_system)
arcpy.management.AddField(sites_shp, "SITE_ID", "LONG")
arcpy.management.AddField(sites_shp, "SITE_NAME", "TEXT", field_length=60)
arcpy.management.AddField(sites_shp, "BG_GEOID", "TEXT", field_length=12)
with arcpy.da.InsertCursor(sites_shp, ["SHAPE@", "SITE_ID", "SITE_NAME", "BG_GEOID"]) as rows:
    for number, (geoid, geometry) in enumerate(chosen, 1):
        point = arcpy.PointGeometry(geometry.labelPoint, out_coordinate_system)
        rows.insertRow([point, number, f"Hypothetical site {number}", geoid])
# Interior representative points of sampled block groups, not random industrial locations.
print("Hypothetical sites SAVED INTO SHP:", N_SITES)

# Problem 2 (40 points)
import os
import arcpy
import csv
import math
def estimatePopulationInZone(source_polygons, population_field, study_zone,
                             output_fc):
    """Similar to the week 10 and 11 notebook exercises, you overlay a buffer with source_polygons 
    such as census units, and calculate the proportion of a source polygon that overlaps 
    with the buffer (the study zone) using areal interpolation. 
    Combine the study zone, intersect, calculate area-weighted population,
    and total the estimates. Save SRC_KM2, PART_KM2, and EST_POP; return the total.
    Inputs must share a projected CRS in meters. 
    """
        #try the buffers with the shapefile points
    if BUFFER_METERS <= 0:
        raise ValueError("BUFFER_METERS must be positive.")
    buffers_shp = fc("individual_buffers_shp")
    zone_shp = fc("dissolved_risk_zone_shp")
    #arcpy.analysis.Buffer(sites, buffers, f"{BUFFER_METERS} Meters", dissolve_option="NONE")
    #arcpy.analysis.Buffer(sites, zone, f"{BUFFER_METERS} Meters", dissolve_option="ALL")
    buffer_ = arcpy.analysis.Buffer(sites_shp, zone_shp, f"{BUFFER_METERS} Meters")
    dissolved_buffer_ = arcpy.management.Dissolve(buffer_, "dissolved_buffer_shp")
    # Dissolving prevents counting residents twice in overlapping site buffers.
    # The radius is a hypothetical screening distance, not a toxicological threshold.
    import geopandas as gpd
    
    # Input shapefile
    sites = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3\tri_sites.shp"
    
    # Read points
    gdf = gpd.read_file(sites)
    
    # Confirm CRS
    print(gdf.crs)
    
    # EPSG:26915 (NAD83 UTM Zone 15N)
    # Buffer distance is therefore interpreted in meters
    
    # Create buffers
    buffers = gdf.copy()
    buffers["geometry"] = gdf.geometry.buffer(BUFFER_METERS)
    
    # Dissolve all buffers into a single geometry
    dissolved_geom = buffers.unary_union
    
    # Create output GeoDataFrame
    risk_zone = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[dissolved_geom],
        crs=gdf.crs,
    )
    
    # Save outputs
    buffers.to_file(r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3\individual_buffers_gpd.shp")
    risk_zone.to_file(r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3\dissolved_risk_zone_gpd.shp")
    
    print("Done")
    with open(os.path.join(DATA_FOLDER, "population.csv"), encoding="utf-8-sig", newline="") as file:
        records = list(csv.DictReader(file))
    ids = [row["GEOID"] for row in records]
    if len(ids) != len(set(ids)) or any(len(x) != 12 or not x.isdigit() for x in ids):
        raise ValueError("Population GEOIDs must be unique 12-digit strings.")
    with arcpy.da.SearchCursor(bg, ["GEOID"]) as rows:
        bg_ids = {row[0] for row in rows}
    if bg_ids != set(ids):
        raise ValueError("Boundary and population GEOIDs do not match.")
    
    pop_table = fc("population")
    if arcpy.Exists(pop_table):
        arcpy.management.Delete(pop_table)
    arcpy.management.CreateTable(gdb, "population")
    arcpy.management.AddField(pop_table, "GEOID", "TEXT", field_length=12)
    arcpy.management.AddField(pop_table, "POP_TOTAL", "LONG")
    arcpy.management.AddField(pop_table, "POP_MOE90", "DOUBLE")
    with arcpy.da.InsertCursor(pop_table, ["GEOID", "POP_TOTAL", "POP_MOE90"]) as rows:
        for row in records:
            count, moe = int(row["POP_TOTAL"]), float(row["POP_MOE90"])
            if count < 0 or not math.isfinite(moe) or moe < 0:
                raise ValueError("Inspect missing/suppressed Census values.")
            rows.insertRow([row["GEOID"], count, moe])
    existing = {f.name for f in arcpy.ListFields(bg)}
    for field in ["POP_TOTAL", "POP_MOE90"]:
        if field in existing:
            arcpy.management.DeleteField(bg, field)
    arcpy.management.JoinField(bg, "GEOID", pop_table, "GEOID", ["POP_TOTAL", "POP_MOE90"])
    print("Joined population to", len(bg_ids), "block groups.")
    
    arcpy.management.AddField(bg, "BG_KM2", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(bg, [["BG_KM2", "AREA"]], area_unit="SQUARE_KILOMETERS")
    overlap = fc("block_groups_at_risk")
    arcpy.analysis.Intersect([bg, dissolved_buffer_[0]], overlap, join_attributes="ALL")
    for field in ["PART_KM2", "PCT_AREA", "EST_POP"]:
        arcpy.management.AddField(overlap, field, "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(overlap, [["PART_KM2", "AREA"]], area_unit="SQUARE_KILOMETERS")
    fields = ["POP_TOTAL", "BG_KM2", "PART_KM2", "PCT_AREA", "EST_POP"]
    with arcpy.da.UpdateCursor(overlap, fields) as rows:
        for row in rows:
            population, full_area, part_area, _, _ = row
            if population is None or population < 0 or full_area <= 0:
                raise ValueError("Check joined population and original polygon area.")
            fraction = part_area / full_area
            if not -1e-6 <= fraction <= 1 + 1e-6:
                raise ValueError("Unexpected area fraction; inspect geometry.")
            row[3] = 100 * fraction
            row[4] = population * fraction
            rows.updateRow(row)
    # Assumption: residents are uniformly distributed across each full polygon.
    # Areas include water; ACS sampling and interpolation uncertainty are not modeled.

    from collections import defaultdict
    risk = defaultdict(lambda: [0.0, 0.0])
    with arcpy.da.SearchCursor(overlap, ["GEOID", "PART_KM2", "EST_POP"]) as rows:
        for geoid, area, population in rows:
            risk[geoid][0] += area
            risk[geoid][1] += population
    
    summary_fc = fc("block_group_risk_summary")
    arcpy.management.CopyFeatures(bg, summary_fc)
    for field in ["RISK_KM2", "PCT_AREA", "EST_POP", "PCT_POP"]:
        arcpy.management.AddField(summary_fc, field, "DOUBLE")
    fields = ["GEOID", "BG_KM2", "POP_TOTAL", "RISK_KM2", "PCT_AREA", "EST_POP", "PCT_POP"]
    with arcpy.da.UpdateCursor(summary_fc, fields) as rows:
        for row in rows:
            geoid, full_area, population = row[:3]
            area, estimate = risk[geoid]
            row[3] = area
            row[4] = 100 * area / full_area
            row[5] = estimate
            row[6] = 100 * estimate / population if population > 0 else None
            rows.updateRow(row)
            return sum(estimate for area, estimate in risk.values())


import os

gdb = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3\chp12data.gdb"

total = estimatePopulationInZone(
    os.path.join(gdb, "block_groups"),
    "POP_TOTAL",
    os.path.join(gdb, "dissolved_risk_zone"),
    os.path.join(gdb, "block_groups_overlap"),
)
print(total)

# Problem 3 (40 points)
def summarizeLineLength(lines, polygons, polygon_id_field, output_fc):
    """Compute the total length of lines that intersect a polygon. 
    Intersect, measure lengths, summarize by polygon ID, and join totals back.
    Save all polygons with LINE_KM (zero if no lines); return output_fc.
    Use a shared projected CRS in meters.
    """
    # Problem 3 (40 points)
def summarizeLineLength(lines, polygons, polygon_id_field, output_fc):
    """Compute the total length of lines that intersect a polygon. 
    Intersect, measure lengths, summarize by polygon ID, and join totals back.
    Save all polygons with LINE_KM (zero if no lines); return output_fc.
    Use a shared projected CRS in meters.
    """
    for dataset in [lines, polygons]:
        sref = arcpy.Describe(dataset).spatialReference
        if sref.type != "Projected" or sref.linearUnitName.lower() not in ["meter", "metre"]:
            raise ValueError("Select an appropriate projected coordinate system in meters.")

    overlap = r"memory\line_overlap"
    if arcpy.Exists(overlap):
        arcpy.management.Delete(overlap)
    arcpy.analysis.Intersect([polygons, lines], overlap,
                             join_attributes="ALL", output_type="LINE")
    arcpy.management.AddField(overlap, "PART_KM", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        overlap, [["PART_KM", "LENGTH"]], length_unit="KILOMETERS")

    from collections import defaultdict
    risk = defaultdict(float)
    with arcpy.da.SearchCursor(overlap, [polygon_id_field, "PART_KM"]) as rows:
        for geoid, length in rows:
            risk[geoid] += length
    arcpy.management.Delete(overlap)

    arcpy.management.CopyFeatures(polygons, output_fc)
    arcpy.management.AddField(output_fc, "LINE_KM", "DOUBLE")
    with arcpy.da.UpdateCursor(output_fc, [polygon_id_field, "LINE_KM"]) as rows:
        for row in rows:
            row[1] = risk[row[0]]
            rows.updateRow(row)

    return output_fc

######################################################################
# MAKE NO CHANGES BEYOND THIS POINT.
######################################################################
if __name__ == "__main__" and hawkid()[1] == "hawkid":
    print("### Error: YOU MUST provide your HawkID in the hawkid() function.")

import os
import arcpy

gdb = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeoAssignment3\chp12data.gdb"
block_groups = os.path.join(gdb, "block_groups")
at_risk = os.path.join(gdb, "block_groups_at_risk")
test_lines = os.path.join(gdb, "test_outlines")
output = os.path.join(gdb, "block_groups_line_km")

source = at_risk if arcpy.Exists(at_risk) else block_groups
for old in [test_lines, output]:
    if arcpy.Exists(old):
        arcpy.management.Delete(old)
arcpy.management.PolygonToLine(source, test_lines)

result = summarizeLineLength(test_lines, block_groups, "GEOID", output)
print("Returned:", result)

count = 0
total = 0
with arcpy.da.SearchCursor(result, ["GEOID", "LINE_KM"]) as rows:
    for geoid, km in rows:
        print(geoid, round(km, 2), "km")
        count += 1
        total += km
print("Polygons:", count)
print("Total length:", round(total, 2), "km")




