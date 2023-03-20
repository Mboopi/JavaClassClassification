from feature_exploration import find_file_paths
import pandas as pd
import xml.etree.ElementTree as ET
import re

class xmlProcessor():
    def __init__(self, XML_paths: list):
        self.roots = [] # Store the individual roots of the XML files.
        self.trees = [] # Store the individual trees of the XML files.
        for path in XML_paths:
            tree = ET.parse(path)
            root = tree.getroot()
            self.roots.append(root)
            self.trees.append(tree)

        self.combined_roots = self.roots[0] # Store the combined roots. 
        self.combined_trees = self.trees[0] # The combined trees, which represent the actual XML files, will be self.trees[0]
                        
    '''Method that combines individual files into 1 file. Duplicate entries are merged by summing up the values of their columns.'''
    def combine_files(self):       
        for count, root in enumerate(self.roots):
            if not count == 0:
              self.combined_roots.extend(root)
    
    '''Method that merges the anonymous ($X where X is a digit) into the outer class, i.e. the anonymous class
    is considered to be the same as the outer class. Additionally, since it already iterates over the nodes anyway, 
    unimportant attributes are removed.'''
    def merge_anom_classes(self):
        for child in self.combined_roots.iter():
            if child.tag == "node" or child.tag == "hotspot":
                child.attrib.pop("lineNumber")
                child.attrib.pop("percent")

                if "time" in child.attrib.keys():
                    child.attrib.pop("time")
                
                regex = "[$d]\d+"
                class_name = child.attrib["class"]
                if bool(re.search(regex, class_name)):
                    child.set("class", re.sub(regex, "", class_name))

    '''Method that writes the combined XML to a file.'''
    def save_file(self, file_path: str):
        with open(file_path, "wb") as f:
            self.combined_trees.write(f, encoding="utf-8")   


if __name__ == "__main__":
    PROJECT_NAME = "sweethome3d"
    # PROJECT_NAME = "test_project"

    # Paths to CSV recorded objects CSVs.
    call_trees = find_file_paths("CallTree.xml", PROJECT_NAME)
    alloc_hotspots = find_file_paths("Hotspots.xml", PROJECT_NAME)

    call_tree_procesor = xmlProcessor(call_trees)
    call_tree_procesor.combine_files()
    call_tree_procesor.merge_anom_classes()
    call_tree_procesor.save_file(f"./feature_extraction/raw_data/{PROJECT_NAME}/CallTree.xml")

    hotspot_processor = xmlProcessor(alloc_hotspots)
    hotspot_processor.combine_files()
    hotspot_processor.merge_anom_classes()
    hotspot_processor.save_file(f"./feature_extraction/raw_data/{PROJECT_NAME}/AllocationHotspots.xml")