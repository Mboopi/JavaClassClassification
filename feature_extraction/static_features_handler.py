'''
Small script to make the static features that were extracted from the srcML XML ready for training.
For instance, converting the name to a different notation, removing bad columns and layer information, adding true labels.
'''

import pandas as pd

PROJECT_NAME = "sweethome3d"

def convert_name(class_name):
    # Find the index of "CH/ifa/" and extract the substring from CH/ifa onwards.
    if PROJECT_NAME == "jhotdraw":
        find = "CH/ifa/"
        seperator = "/"
   
    if PROJECT_NAME == "sweethome3d":
        find = "com\\"
        seperator = "\\"

    index = class_name.find(find)
    class_name = class_name[index:]
    
    class_name = class_name.removesuffix(".java")
    class_name = class_name.replace(".", "$")
    class_name = class_name.replace(seperator, ".")

    return class_name

def get_layer(x):
    package = x.split(".")
    package_to_layer = {"": "None", "applet": "Presentation", "io": "DataAccess", "j3d": "Presentation",
                        "model": "Business", "plugin": "CrossCutting", "swing": "Presentation",
                        "tools": "Business", "viewcontroller": "Service"}

    if len(package) < 5:
        package_name = ""
    else:
        package_name = package[3]
    
    return package_to_layer[package_name]

if __name__ == "__main__":
    # Load raw static features.
    df = pd.read_csv("/Users/mboopi/Documents/GitHub/JavaClassClassification/feature_extraction/srcml_output/static_features_sweethome3d_raw.csv", index_col=False)

    # Remove test classes.
    df = df[~df['Fullpathname'].str.contains('Test')]

    print(df.columns)

    # Drop unnecessary columns.
    df = df.drop(columns=["Classname", "Unnamed: 31", "numInnerClasses"])

    # Rename Fullpathname.
    df = df.rename(columns={"Fullpathname": "className"})

    # Convert Fullpathname to our own notation.
    df["className"] = df["className"].apply(lambda x: convert_name(x))

    # Add layer information to the classes.
    df["layer"] = df["className"].apply(lambda x: get_layer(x))

    # Add labels to the classes.
    labels_csv = pd.read_csv(f"/Users/mboopi/Documents/GitHub/JavaClassClassification/data/ground_truth/{PROJECT_NAME}/labeled_classes_FINAL.csv", delimiter=",")

    df = pd.merge(df, labels_csv[["className", "label"]], on='className', how='inner')

    # Save processed final CSV.
    df.to_csv(f"/Users/mboopi/Documents/GitHub/JavaClassClassification/data/dataset/{PROJECT_NAME}/static_features_sweethome3d_FINAL.csv", index=False)