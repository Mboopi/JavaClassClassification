import pandas as pd

# Some final pre-processing steps:
# Combine the 2 CSV feature files, impute missing values, sort the rows based on class name and reorder the columns.

PROJECT_NAME = "sweethome3d"
# PROJECT_NAME = "test_project"
# PROJECT_NAME = "Stable"

new_order = ["className", "numIntCalls", "numExtCalls", "ratioInternalExternal", "numIncomingCalls", "numOutgoingCalls", "ratioIncomingOutgoing",
             "numUniqueIncomingCalls", "numUniqueOutgoingCalls", "numObjectsCreated", "percObjectCreation", 
             "numLeaves", "percLeaves", "avgExecTime", "avgDepth", "numObjectsTotal", "numObjectsDeallocated", "percDeallocated", "avgObjectSize"]

features_CSV = pd.read_csv(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_CSV.csv")
features_XML = pd.read_csv(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_XML.csv")

# Merge the CSV files and keep only the classes that are present in the call tree.
features_merged = pd.merge(features_XML, features_CSV, on="className", how="left")
features_merged = features_merged.sort_values("className")

# Since some classes from the call tree are not in the recorded objects (mostly static classes), impute the missing values.
# numObjectsTotal, numObjectsDeallocated and avgObjectSize can be filled as 0 since this would represent that a class was not instantiated.
# percDeallocated however should not be 0, since that would be a division by 0, instead we fill it as -1 for N/A.
features_merged["percDeallocated"] = features_merged["percDeallocated"].fillna(-1)
features_merged = features_merged.fillna(0)

features_merged = features_merged.reindex(columns=new_order)

file_path = f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_FINAL.csv"
features_merged.to_csv(file_path, sep=",", index=False)   
