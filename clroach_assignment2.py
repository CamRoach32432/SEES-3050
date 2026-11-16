######################################################################
# Edit the following function definition, replacing the words
# 'name' with your name and 'hawkid' with your hawkid.
#
# Note: Your hawkid is the login name you use to access ICON, and not
# your firsname-lastname@uiowa.edu email address.
#
# def hawkid():
# return(["Caglar Koylu", "ckoylu"])
######################################################################
def hawkid():
    return(["Cameron Roach", "clroach"])

######################################################################
# Problem 1 (10 Points)
#
# This function reads all the feature classes in a workspace (folder or
#geodatabase) and
# prints the name of each feature class and the geometry type of that feature class
# in the following format:
# 'states is a point feature class'
######################################################################
def printFeatureClassNames(workspace):
    import arcpy
    import os

    arcpy.env.workspace = r"S:\2026_Fall\SEES-3050\STUDENT\clroach\Assignment2\hw2.gdb"
    
    datasets = arcpy.ListDatasets(feature_type='feature')
    datasets = [''] + datasets if datasets is not None else []
    
    for ds in datasets:
        for fc in arcpy.ListFeatureClasses(feature_dataset=ds):
            path = os.path.join(arcpy.env.workspace, ds, fc)
            print(path)
printFeatureClassNames(r"S:\2026_Fall\SEES-3050\STUDENT\clroach\Assignment2\hw2.gdb")

######################################################################
# Problem 2 (20 Points)
#
# This function reads all the attribute names in a feature class or shape file and
# prints the name of each attribute name and its type (e.g., integer, float,

# only if it is a numerical type
######################################################################
def printNumericalFieldNames(inputFc, workspace):
    arcpy.env.workspace = workspace
    fields = arcpy.ListFields(inputFc)
    numericTypes = ["Integer", "SmallInteger", "Double", "Single"]

    for field in fields:
        if field.type in numericTypes:
            print(f"{field.name} is a {field.type}field")
printNumericalFieldNames(r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\hw2.gdb\hospitals", r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\hw2.gdb")

######################################################################
# Problem 3 (30 Points)
#
# Given a geodatabase with feature classes, and shape type (point, line or polygon)
#and an output geodatabase:
# this function creates a new geodatabase and copying only the feature classes with
#the given shape type into the new geodatabase
######################################################################
def exportFeatureClassesByShapeType(input_geodatabase, shapeType, output_geodatabase):
    import arcpy
    import os
    outputFolder = os.path.dirname(output_geodatabase)
    outName = os.path.basename(output_geodatabase)
    arcpy.env.workspace = input_geodatabase
    if not arcpy.Exists(output_geodatabase):
        arcpy.CreateFileGDB_management(outputFolder, outName)
        
    featureclasses = arcpy.ListFeatureClasses()
    for fc in featureclasses:
        fcShapeType = arcpy.Describe(fc).shapeType.lower()
        if fcShapeType == shapeType.lower():
            outputFC = os.path.join(output_geodatabase, fc)
            if arcpy.Exists(outputFC):
                arcpy.Delete_management(outputFC)
                
            arcpy.Copy_management(fc, outputFC)
            print(f"Copied {fc} to {output_geodatabase}")
exportFeatureClassesByShapeType(r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\hw2.gdb", "point", r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\points.gdb")
            


######################################################################
# Problem 4 (40 Points)
#
# Given an input feature class or a shape file and a table in a geodatabase or a
#folder workspace,
# join the table to the feature class using one-to-one and export to a new feature
#class.
# Print the results of the joined output to show how many records matched and
#unmatched in the join operation.
######################################################################
def exportAttributeJoin(inputFc, idFieldInputFc, inputTable, idFieldTable,
workspace):
    import arcpy
    import os
    arcpy.env.workspace = workspace
    arcpy.env.qualifiedFieldNames = False

    layerName = "tempLayer"
    arcpy.management.MakeFeatureLayer(inputFc, layerName)

    joined = arcpy.management.AddJoin(layerName, idFieldInputFc, inputTable, idFieldTable, "KEEP_ALL")
    
    outName = os.path.basename(inputFc) + "_joined"
    outPath = os.path.join(workspace, outName)
    
    if arcpy.Exists(outPath):
        arcpy.Delete_management(outPath)

    result = arcpy.management.CopyFeatures(joined, outPath)
    print(outPath)
exportAttributeJoin(
    r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\hw2.gdb\hospitals",
    "OBJECTID",
    r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\hw2.gdb\mytable",
    "OBJECTID",
    r"S:\2026_Fall\SEES-3050\STUDENT\clroach\GeospatialAssignment2\hw2.gdb"
)

if __name__ == '__main__' and hawkid()[1] == "hawkid":
    print('### Error: YOU MUST provide your hawkid in the hawkid() function.')


