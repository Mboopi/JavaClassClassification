import pandas as pd
import os
import re
import xml.etree.ElementTree as ET

# Python file for initial exploration of features, i.e. number of unique classes in combination of files.
# It determines the unique classes in the live objects, garbage collected objects, call tree and allocation hotspots.

'''Method that given a keyword and project name, finds the files that contain this key word.
It returns a list of paths to each file.'''
def find_file_paths(key_word, project_name):
    file_paths = []

    for root, dirs, files in os.walk(".", topdown=True):
        if project_name in root and "execution_info" in root:
            for name in files:
                if project_name and key_word in name:
                    file_paths.append(os.path.join(root, name))
    
    return file_paths

'''Method that given a list of paths to CSVs, loads the files and returns them in a list.'''
def load_CSVs(file_paths):
    CSVs = []

    for file_path in file_paths:
        CSVs.append(pd.read_csv(file_path))

    return CSVs

'''Method that given a list of paths to XMLs, loads the files and returns them in a list.'''
def load_XMLs(file_paths):
    XMLs = []

    for file_path in file_paths:
        XMLs.append(ET.parse(file_path))
    
    return XMLs


'''Method that, given a class name, checks whether it is a valid class (for counting purposes).
Anonymous ($int) classes are considered as the same as parent class and therefore removed.
Inner ($string) classes are considered as a seperate class and therefore not removed.
Note: test classes are also considered as non-unique and therefore removed.
If the class_name contains a $-sign followed by an int, then it's an anonymous class so return False.
Otherwise, return True.'''
def is_valid_class(class_name):
    return not (bool(re.search('[$]\d+', class_name)) or bool(re.search('Test', class_name)))

'''Method that given a list of CSVs, returns a list of unique classes.'''
def unique_classes_CSV(CSVs):
    classes = []

    for csv in CSVs:
        for name in csv['Name']:
            class_name = name.removesuffix("[ ]") # Some classes in the CSV end with [ ].
            if is_valid_class(class_name):
                classes.append(class_name) 

    return [*set(classes)]

'''Method that given a list of XML trees, returns a list of unique classes.'''
def unique_classes_XML(XML_trees):
    classes = []

    for tree in XML_trees:
        node = tree.findall('.//node')

        for n in range(len(node)):
            class_name = node[n].attrib['class']

            if class_name.startswith('com.eteks.sweethome3d') and is_valid_class(class_name):
                classes.append(class_name)    

    return[*set(classes)]

'''Method that convert class name notation, as used by the replication package (Ho-Quang et al.) 
to notation used by JProfiler.'''
def convert_name(class_name):
    class_name = class_name.removeprefix("\src\\")
    class_name = class_name.removesuffix(".java")
    class_name = class_name.replace(".", "$")
    class_name = class_name.replace("\\", ".")

    return class_name

'''Method that compares two list of classes and returns the set difference (a - b).'''
def determine_missing(a, b):
    return set(a) - set(b)


if __name__ == "__main__":
    PROJECT_NAME = "sweethome3d"

    # Count unique objects in CSVs.
    rec_CSV_paths = find_file_paths("All.csv", PROJECT_NAME)
    gc_CSV_paths = find_file_paths("Garbage.csv", PROJECT_NAME)
    rec_CSVs = load_CSVs(rec_CSV_paths)
    gc_CSVs = load_CSVs(gc_CSV_paths)
    unique_classes_rec= unique_classes_CSV(rec_CSVs)
    unique_classes_gc = unique_classes_CSV(gc_CSVs)

    print(f"Number of uniquely recorded objects: {len(unique_classes_rec)}")
    print(f"Number of uniquely garbage collected objects: {len(unique_classes_gc)}")

    # Count unique objects in XMLs.
    call_XML_paths = find_file_paths("CallTree.xml", PROJECT_NAME)
    alloc_XML_paths = find_file_paths("Hotspots.xml", PROJECT_NAME)
    call_XMLs = load_XMLs(call_XML_paths)
    alloc_XMLs = load_XMLs(alloc_XML_paths)
    unique_classes_call = unique_classes_XML(call_XMLs)
    unique_classes_alloc = unique_classes_XML(alloc_XMLs)

    print(f"Number of unique classes in call trees: {len(unique_classes_call)}")
    print(f"Number of unique classes in allocation hotspots: {len(unique_classes_alloc)}")

    # Check how many classes from replication package we are missing.
    labels_csv = pd.read_csv("./data/ground_truth/sweethome3d/labeled_classes.csv")
    labels_csv.pop('index')
    labels_csv.pop('case')
    
    required_classes = []
    for name in labels_csv['fullpathname']:
        required_classes.append(convert_name(name))

    print(f"{len(determine_missing(required_classes, unique_classes_call))} classes from paper missing in the call tree.")

    missing_classes = determine_missing(required_classes, unique_classes_call)