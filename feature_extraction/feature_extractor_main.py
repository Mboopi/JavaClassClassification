import pandas as pd
from feature_exploration import convert_name

# Some final pre-processing steps:
# Combine the 2 CSV feature files, impute missing values, sort the rows based on class name, reorder the columns.

PROJECT_NAME = "sweethome3d"
# PROJECT_NAME = "jhotdraw"

# Read files.
features_CSV = pd.read_csv(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_CSV.csv")
features_XML = pd.read_csv(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_XML_v9.csv")


# Merge the CSV files and keep only the classes that are present in the call tree.
# Since some classes from the call tree are not in the recorded objects (mostly static classes), impute the missing values.
# numObjectsTotal, numObjectsDeallocated and avgObjectSize can be filled as 0 since this would represent that a class was not instantiated.
# percDeallocated however should not be 0, since that would be a division by 0, instead we fill it as -1 for N/A.
features_merged = pd.merge(features_XML, features_CSV, on="className", how="left")
features_merged = features_merged.sort_values("className")
features_merged["percDeallocated"] = features_merged["percDeallocated"].fillna(-1)
features_merged = features_merged.fillna(0)

new_order = ["className", "numIntCalls", "numExtCalls_A", "numExtCalls_B", "ratioInternalExternal",# "ratioInternalExternal_B", 
             "numIncomingCalls_A", "numIncomingCalls_B", "numOutgoingCalls_A", "numOutgoingCalls_B", "ratioIncomingOutgoing",# "ratioIncomingOutgoing_B",
             "numUniqueIncomingCalls", "numUniqueOutgoingCalls", "numDataStructureCalls", "percDataStructure",
             "numObjectsCreated_A", "numObjectsCreated_B", "percObjectCreation", 
             "return_none", "return_var", "return_data_struct", "return_java_obj", "return_project_obj", "return_ext_obj",
             "arg_none", "arg_var", "arg_data_struct", "arg_java_obj", "arg_project_obj", "arg_ext_obj",
             "numLeaves", "percLeaves", "avgExecTime", "avgDepth", "avgRelativeDepth", "numObjectsTotal", "numObjectsDeallocated", "percDeallocated", "avgObjectSize", 
             "numCallsToLayerNone",	"numCallsFromLayerNone", "numCallsToLayerBusiness",	"numCallsToLayerPresentation", "numCallsFromLayerPresentation",
             "numCallsFromLayerBusiness", "numCallsToLayerDataAccess", "numCallsFromLayerService", "numCallsToLayerService", "numCallsFromLayerDataAccess",
             "numCallsToLayerCrossCutting",	"numCallsFromLayerCrossCutting",
             "percCallsToLayerNone", "percCallsFromLayerNone", "percCallsToLayerBusiness", "percCallsToLayerPresentation", "percCallsFromLayerPresentation",
             "percCallsFromLayerBusiness", "percCallsToLayerDataAccess", "percCallsFromLayerService", "percCallsToLayerService", "percCallsFromLayerDataAccess",
             "percCallsToLayerCrossCutting", "percCallsFromLayerCrossCutting",
             "label"]
features_merged = features_merged.reindex(columns=new_order)


# Save file.
file_path = f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_FINAL_v9_RELABELED2.csv"
features_merged.to_csv(file_path, sep=",", index=False)   
