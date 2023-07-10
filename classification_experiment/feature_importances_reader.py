'''
Small script to load in the different txt files containing the feature and their importances.
Output: average feature importance per role, over all loaded files.
'''

features_dict = {}

smote = False

base_path = "classification_experiment/sweethome3d/"
base_name = "feat_importances_binary-"
suffixes = ["Controller", "Coordinator", "Information Holder", "Interfacer", "Service Provider", "Structurer"]

test_name = base_path + base_name + suffixes[0] + ".txt"

for suffix in suffixes:
    full_path = base_path + base_name + suffix + ".txt"

    with open(full_path, "r") as file:
        for line in file:
            line = line.strip()  # Remove leading/trailing whitespace and newline characters
            
            line_split = line.split(",")
            feature = line_split[0]
            importance = line_split[1]

            if feature in features_dict:
                features_dict[feature].append(round(float(importance), 3))
            else:
                features_dict[feature] = [round(float(importance), 3)]
        file.close()

for key, value in features_dict.items():
    print(key, value)

output_file = base_path + base_name + "combined.csv"
with open(output_file, 'w') as file:   
    file.write("feature, CT, CO, IH, IT, SP, ST" + "\n") 

    for key, value in features_dict.items():
        importances = f"{value}"
        importances = importances.replace('[', '').replace(']', '')
        file.write(f"{key}, {importances}" + "\n")
    
    file.close()

