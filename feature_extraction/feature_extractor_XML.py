import xml.etree.ElementTree as ET
import copy
import pandas as pd
import numpy as np
from feature_exploration import convert_name

class FeatureExtractorXML:
    def __init__(self, call_tree):
        self.call_tree = call_tree
        self.ROUND = 3 # Decimals of rounding.
        self.output = {} # Store the intermediate features in this dict.
        self.output_CSV = None # Store the final features in this CSV.
        class_info = {"numIntCalls": 0, "numExtCalls": 0, "numIncomingCalls": 0, "uniqueOutgoingCalls": set(), 
                      "uniqueIncomingCalls": set(), "numLeaves": 0, "totalExecTime": 0, 
                      "helpCount": 0, "totalDepth": 0, "numObjectsCreated": 0,
                      "incomingCallsInside": 0, "incomingCallsOutside": 0, "outgoingCallsInside": 0, "outgoingCallsOutside": 0}
        # helpCount represents the total count of the node itself, helper for computing avg_exec_time and avg_depth.
        
        nodes = self.call_tree.findall(".//node")
        for node in nodes: # Fill in the dictionary with the class names as the keys, with their value being a copy of the class_info dict.
            class_name = node.attrib["class"]
            if not class_name in self.output:
                self.output[class_name] = copy.deepcopy(class_info) 
                # A shallow copy would copy the inner dict as well as the integer key-values like numIntCalls, 
                # but for an object e.g. set() it would only copy a reference to that set instead of copying the actualt set.
        
        # self.remove_non_src_classes(self.call_tree, self.call_tree.findall("node"), firstCall=True)
        self.traverse_call_tree(self.call_tree, self.call_tree.findall("node"), firstCall=True)
    
    '''Method that removes all classes that are not part of the project as well as Test classes.'''
    def remove_non_src_classes(self, parent_node, children, firstCall=False):
        for child in children:
            if not firstCall:
                if not "com.eteks.sweethome3d" in child.attrib["class"]:# or "Test" in child.attrib["class"]:
                    parent_node.remove(child)
                    print("REMOVED")
                else:
                    self.remove_non_src_classes(child, child.findall("node"))
            else:
                self.remove_non_src_classes(child, child.findall("node"))
  

    '''Method that removes all classes that are not part of the reference classes (the classes that are used by the paper)'''
    def drop_redundant_classes(self, reference_classes: list):
        self.output = {key: value for key, value in self.output.items() if key in reference_classes}

    '''Method that for a given parent and a list of their child nodes, recursively traverses the tree downwards and extracts the intermediate features.'''
    def traverse_call_tree(self, parent_node: ET.Element, children: list, current_depth: int = 0, firstCall: bool = False):
        if not firstCall:
            parent_name = parent_node.attrib["class"]
            parent_count = int(parent_node.attrib["count"])
            parent_selftime = int(parent_node.attrib["selfTime"])

            if parent_node.attrib["leaf"] == "true": # For checking whether a node is a leaf, we only need to look at that node itself.
                self.output[parent_name]["numLeaves"] += parent_count
        
            self.output[parent_name]["totalExecTime"] += parent_selftime
            self.output[parent_name]["totalDepth"] += parent_count * current_depth
            self.output[parent_name]["helpCount"] += parent_count

        for child in children: # If there are no children the loop won't execute, this represents the base case of recursion.
            if not firstCall:
                child_name = child.attrib["class"]
                child_count = int(child.attrib["count"])
                child_method = child.attrib["methodName"]

                if "init" in child_method or "cinit" in child_method:
                    self.output[parent_name]["numObjectsCreated"] += child_count

                # Extract features...
                if parent_name == child_name:
                    # Parent calls itself: its internal calls increases, unique outgoing and unique incoming calls may increase.
                    self.output[parent_name]["numIntCalls"] += child_count
                    self.output[parent_name]["uniqueOutgoingCalls"].add(parent_name)
                    self.output[parent_name]["uniqueIncomingCalls"].add(parent_name)
                else:
                    # Parent calls a child: its external calls increases, unique outgoing calls may increase.
                    if PROJECT_NAME in child_name:
                        self.output[parent_name]["numExtCalls"] += child_count 
                        self.output[parent_name]["uniqueOutgoingCalls"].add(child_name)
                    
                        # Furthermore: the childs incoming calls increases, unique incoming calls may increase.
                        self.output[child_name]["numIncomingCalls"] += child_count 
                        self.output[child_name]["uniqueIncomingCalls"].add(parent_name)

            self.traverse_call_tree(child, child.findall("node"), current_depth = current_depth + 1)
    
    def extract_features(self):
        self.output_CSV = pd.DataFrame.from_dict(self.output, orient="index")

        self.output_CSV["numOutgoingCalls"] = self.output_CSV["numIntCalls"] + self.output_CSV["numExtCalls"] + self.output_CSV["numLeaves"]

        self.output_CSV["numUniqueIncomingCalls"] = self.output_CSV["uniqueIncomingCalls"].apply(lambda x: len(x))  
        self.output_CSV["numUniqueOutgoingCalls"] = self.output_CSV["uniqueOutgoingCalls"].apply(lambda x: len(x))   
        self.output_CSV["avgExecTime"] = (self.output_CSV["totalExecTime"] / self.output_CSV["helpCount"]).round(self.ROUND)
        self.output_CSV["avgDepth"] = (self.output_CSV["totalDepth"] / self.output_CSV["helpCount"]).round(self.ROUND)

        self.output_CSV["ratioInternalExternal"] = (self.output_CSV["numIntCalls"] / self.output_CSV["numExtCalls"]).round(self.ROUND)
        self.output_CSV["ratioIncomingOutgoing"] = (self.output_CSV["numIncomingCalls"] / self.output_CSV["numOutgoingCalls"]).round(self.ROUND)
        self.output_CSV["percObjectCreation"] = (self.output_CSV["numObjectsCreated"] / self.output_CSV["numOutgoingCalls"]).round(self.ROUND)
        self.output_CSV["percLeaves"] = (self.output_CSV["numLeaves"] / (self.output_CSV["numOutgoingCalls"] + self.output_CSV["numLeaves"])).round(self.ROUND)

        self.output_CSV.drop("uniqueIncomingCalls", axis=1, inplace=True)
        self.output_CSV.drop("uniqueOutgoingCalls", axis=1, inplace=True)
        self.output_CSV.drop("totalExecTime", axis=1, inplace=True)
        self.output_CSV.drop("totalDepth", axis=1, inplace=True) 
        self.output_CSV.drop("helpCount", axis=1, inplace=True)

        # Sometimes, the ratio or percentage can't be computed because the denominator equals 0, fill it as -1 to represent N/A.
        self.output_CSV = self.output_CSV.replace(np.inf, -1)
        self.output_CSV = self.output_CSV.fillna(-1)

    def add_true_labels(self, reference_classes:list, true_labels: list):
        data = {"className": reference_classes, "label": true_labels}
        df = pd.DataFrame(data)
        
        self.output_CSV.index.name = "className"
        self.output_CSV = pd.merge(self.output_CSV, df, on="className", how="inner")
        
    def save_file(self, file_path: str):
        self.output_CSV.to_csv(file_path, index=False)

    def test_print(self):
        print(len(self.output))
        for class_name in self.output:
            print(f"======{class_name}======")
            print(self.output[class_name])
            print("\n")


if __name__ == "__main__":
    PROJECT_NAME = "sweethome3d"
    # PROJECT_NAME = "test_project"
    # PROJECT_NAME = "Stable"

    # Classes that are used by the paper, i.e. our reference classes.
    labels_csv = pd.read_csv(f"./data/ground_truth/{PROJECT_NAME}/labeled_classes.csv")
    labels_csv.pop("index")
    labels_csv.pop("case")
    
    # Convert the name notation to the notation used by JProfiler and store the classes and their labels in seperate lists.
    reference_classes = []
    true_labels = []
    for index, row in labels_csv.iterrows():
        name = row["fullpathname"]
        label = row["label"]
        reference_classes.append(convert_name(name))
        true_labels.append(label)

    call_tree = ET.parse(f"./feature_extraction/raw_data/{PROJECT_NAME}/CallTree.xml")

    feature_extractor = FeatureExtractorXML(call_tree)
    feature_extractor.drop_redundant_classes(reference_classes)
    feature_extractor.extract_features()
    feature_extractor.add_true_labels(reference_classes, true_labels)

    feature_extractor.save_file(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_XML_v3.csv")