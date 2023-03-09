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
        if project_name in root:
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
    return not (bool(re.search('[$]\d', class_name)) or bool(re.search('Test', class_name)))

'''Method that given a list of CSVs, returns a list of unique classes.'''
def unique_classes_CSV(CSVs):
    classes = []

    for csv in CSVs:
        for name in csv['Name']:
            if is_valid_class(name):
                classes.append(name)

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


if __name__ == "__main__":
    PROJECT_NAME = "sweethome3d"

    # Count unique objects in CSVs.
    live_CSV_paths = find_file_paths("Live.csv", PROJECT_NAME)
    gc_CSV_paths = find_file_paths("Garbage.csv", PROJECT_NAME)
    live_CSVs = load_CSVs(live_CSV_paths)
    gc_CSVs = load_CSVs(gc_CSV_paths)

    print(f"Number of uniquely recorded live objects: {len(unique_classes_CSV(live_CSVs))}")
    print(f"Number of uniquely recored garbage colleced objects: {len(unique_classes_CSV(gc_CSVs))}")

    # Count unique objects in XMLs.
    call_XML_paths = find_file_paths("CallTree.xml", PROJECT_NAME)
    alloc_XML_paths = find_file_paths("Hotspots.xml", PROJECT_NAME)
    call_XMLs = load_XMLs(call_XML_paths)
    alloc_XML_paths = load_XMLs(alloc_XML_paths)

    print(f"Number of unique classes in all call trees: {len(unique_classes_XML(call_XMLs))}")
    print(f"Number of unique classes in all allocation hotspots: {len(unique_classes_XML(alloc_XML_paths))}")