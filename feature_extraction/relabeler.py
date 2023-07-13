# Script for relabeling the labels of a CSV, given another CSV with the new labels.
import pandas as pd

def apply_new_label(x):
    if not pd.isna((x["labelNew"])):
        return labels_dict[x["labelNew"]]
    else:
        return x["label"]

original_CSV = pd.read_csv("/Users/mboopi/Documents/GitHub/JavaClassClassification/data/dataset/sweethome3d/features_sweethome3d_FINAL_v10_RELABELED2.csv")
# original_CSV = pd.read_csv("/Users/mboopi/Documents/GitHub/JavaClassClassification/data/dataset/sweethome3d/static_features_sweethome3d_FINAL.csv")
relabeled = pd.read_csv("/Users/mboopi/Documents/GitHub/JavaClassClassification/data/ground_truth/sweethome3d/sweethome3d_relabeled_utf.csv", delimiter=";").drop(columns=["remark", "responsibility"])

labels_dict = {"CO": "Coordinator", "CT": "Controller", "ST": "Structurer",
               "IT": "Interfacer", "IH": "Information Holder", "SP": "Service Provider", "DISCARD": "DISCARD"}

# Do left join to keep the original rows, then if new label for row exist,
# apply that label otherwise keep original label.
new_CSV = pd.merge(original_CSV, relabeled, on="className", how="left")
# new_CSV["label_temp"] = new_CSV.apply(lambda x: x["labelNew"] if x["labelNew"] else x["label"], axis=1)
new_CSV["label"] = new_CSV.apply(lambda x: apply_new_label(x), axis=1)
# new_CSV = new_CSV.drop(columns=["labelOld", "labelNew", "labelSecondary"]) # Single label.

# Multi label.
new_CSV["labelSecondary"] = new_CSV["labelSecondary"].apply(lambda x: labels_dict[x] if not pd.isna(x) else "")
new_CSV = new_CSV.drop(columns=["labelOld", "labelNew"])

new_CSV.to_csv("/Users/mboopi/Documents/GitHub/JavaClassClassification/data/dataset/sweethome3d/features_sweethome3d_FINAL_v10_MULTILABEL.csv", index=False)
# new_CSV.to_csv("/Users/mboopi/Documents/GitHub/JavaClassClassification/data/dataset/sweethome3d/static_features_sweethome3d_FINAL_MULTILABEL.csv", index=False)