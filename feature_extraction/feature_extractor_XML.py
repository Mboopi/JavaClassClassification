import xml.etree.ElementTree as ET
import copy
import pandas as pd
import numpy as np
import re
from static_features_handler import get_layer

data_types = ["Collection", "Dequeue", "Enumeration", "List", "Map", "Queue", "Set", 
                  "SortedMap", "SortedSet",
                  "ArrayDeque", "ArrayList", "Dictionary", "EnumMap", "EnumSet",
                  "HashMap", "HashSet", "Hashtable", "IdentityHashMap", "LinkedHashMap",
                  "LinkedHashSet", "LinkedList", "PriorityQueue", "Stack", "TreeMap", 
                  "TreeSet", "Vector", "WeakHashMap"]

'''Helper method to determine the argument types and return types from a methodSignature.'''
def get_type(sub_signature, package_name):
    if sub_signature == "V" or sub_signature == "": # Void means no return type.
        return "none"
    elif len(sub_signature) == 1 or sub_signature == "Ljava/lang/String": # Regular variables are primitives or a String.
        return "var"
    elif "Ljava/util" in sub_signature and any(dt in sub_signature for dt in data_types):
        return "data_struct"
    elif "[" in sub_signature:
        return "data_struct"
    elif "Ljava" in sub_signature:
        return "java_obj"
    elif package_name in sub_signature:
        return "project_obj"
    else:
        return "ext_obj"

'''Helper method to parse a methodSignature, with the help of get_type().'''
def parse_signature(signature, package_name):
    arg_types = []

    # Argument types come before ")" and return type after that.
    signature = signature.replace("(", "")
    sig = signature.split(")")

    return_type = get_type(sig[1], package_name)
    
    arg_sigs = re.split(r"(L.*?;|\[L.*?;|\[.|.)", sig[0]) # We're looking for individual characters, L_something...; or [ followed by either.
    if not arg_sigs == [""]: # I.e. if there are no arguments, e.g. ()I.
        arg_sigs = [x for x in arg_sigs if x != ""] # For some reason, re.split() also returns empty strings.
    
    for k in arg_sigs:
        arg_types.append(get_type(k, package_name))
    
    return arg_types, return_type

'''Helper method to recursively find all paths from root to a leaf.'''
def get_paths(parent, current_path, all_paths):
    # Add current node (parent) to current path.
    parent_name = parent.attrib.get("class", "")
    parent_count = parent.attrib.get("count", 0)
    if not parent_name == "":
        current_path.append((parent_name, int(parent_count)))

    # If current node is a leaf, add current path to list of all paths.
    # Else, recursively continue with child nodes.
    if parent.attrib.get("leaf", "false") == "true":
        all_paths.append(current_path.copy()) 
    else:
        children = parent.findall("node")
        for child in children: 
            get_paths(child, current_path, all_paths)
    
    # Remove the current node from the current path to backtrack and try other paths.
    if len(current_path) > 0:
        current_path.pop()


class FeatureExtractorXML:
    def __init__(self, call_tree):
        self.call_tree = call_tree
        self.ROUND = 3 # Decimals of rounding.
        self.output = {} # Store the intermediate features in this dict.
        self.output_CSV = None # Store the final features in this CSV.
        class_info = {"numIntCalls": 0, "numExtCalls_A": 0, "numIncomingCalls_A": 0, "uniqueOutgoingCalls": set(), 
                      "uniqueIncomingCalls": set(), "numLeaves": 0, "totalExecTime": 0, #"totalTime": 0,
                      "helpCount": 0, "totalDepth": 0, "avgRelativeDepth": 0, "numObjectsCreated_A": 0, "numObjectsCreated_B": 0,
                      "numExtCalls_B": 0, "numIncomingCalls_B": 0, "numDataStructureCalls": 0, 
                      "return_none": 0, "return_var": 0, "return_data_struct": 0, "return_java_obj": 0, "return_project_obj": 0, "return_ext_obj": 0,
                      "arg_none": 0, "arg_var": 0, "arg_data_struct": 0, "arg_java_obj": 0, "arg_project_obj": 0, "arg_ext_obj": 0}
                      # helpCount represents the total count of the node itself, helper for computing avg_exec_time and avg_depth.

        # The following 4 variables are used for extracting the average relative depth of each class.
        self.totalCount = {} # Helper variable that stores for each class, its total number of counts.
        self.avgRelativeDepth = {} # Helper variable that stores for each class, its average relative depth.
        self.all_paths = [] # Helper variable that stores all paths from root to a leaf.
        self.current_path = [] # Helper variable to store current path temporarily.
        
        self.user_package = "com.eteks.sweethome3d" # Used to seperate user defined classes from other classes. 
        

        nodes = self.call_tree.findall(".//node")
        for node in nodes: # Fill in the dictionary with the class names as the keys, with their value being a copy of the class_info dict.
            class_name = node.attrib["class"]
            if not class_name in self.output:
                self.output[class_name] = copy.deepcopy(class_info) 
                # A shallow copy would copy the inner dict as well as the integer key-values like numIntCalls, 
                # but for an object e.g. set() it would only copy a reference to that set instead of copying the actual set.
        
        # self.remove_non_src_classes(self.call_tree, self.call_tree.findall("node"), firstCall=True)
        self.traverse_call_tree(self.call_tree, self.call_tree.findall("node"), firstCall=True)
    
    '''Method that removes all classes that are not part of the project as well as Test classes.'''
    def remove_non_src_classes(self, parent_node, children, firstCall=False):
        for child in children:
            if not firstCall:
                if not self.user_package in child.attrib["class"]:# or "Test" in child.attrib["class"]:
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
            # parent_time = int(parent_node.attrib["time"])
        
            method_sig = parent_node.attrib["methodSignature"]
            arg_types, return_type = parse_signature(method_sig, "sweethome3d")
            self.output[parent_name][f"return_{return_type}"] = 1
            for arg_type in arg_types:
                self.output[parent_name][f"arg_{arg_type}"] = 1

            if parent_node.attrib["leaf"] == "true": # For checking whether a node is a leaf, we only need to look at that node itself.
                self.output[parent_name]["numLeaves"] += parent_count

            self.output[parent_name]["totalExecTime"] += parent_selftime
            # self.output[parent_name]["totalTime"] += parent_time
            self.output[parent_name]["totalDepth"] += parent_count * current_depth
            self.output[parent_name]["helpCount"] += parent_count

        for child in children: # If there are no children the loop won't execute, this represents the base case of recursion.
            if not firstCall:
                child_name = child.attrib["class"]
                child_count = int(child.attrib["count"])
                child_method = child.attrib["methodName"]

                if "init" in child_method or "cinit" in child_method:
                    if self.user_package in child_name:
                        self.output[parent_name]["numObjectsCreated_A"] += child_count
                    else:
                        self.output[parent_name]["numObjectsCreated_B"] += child_count

                # Extract features...
                if parent_name == child_name:
                    # Parent calls itself: its internal calls increases, unique outgoing and unique incoming calls may increase.
                    self.output[parent_name]["numIntCalls"] += child_count
                    self.output[parent_name]["uniqueOutgoingCalls"].add(parent_name)
                    self.output[parent_name]["uniqueIncomingCalls"].add(parent_name)

                else:
                    # Parent calls a child: its external calls increases, unique outgoing calls may increase.
                    if self.user_package in child_name:
                        self.output[parent_name]["numExtCalls_A"] += child_count 
                        self.output[parent_name]["uniqueOutgoingCalls"].add(child_name)
                    
                        # Furthermore: the childs incoming calls increases, unique incoming calls may increase.
                        if self.user_package in parent_name:
                            self.output[child_name]["numIncomingCalls_A"] += child_count 
                            self.output[child_name]["uniqueIncomingCalls"].add(parent_name)

                            # Parent makes a call to child layer and child receives call from parent layer.
                            if not "junit" in parent_name and not "junit" in child_name:
                                parent_layer = get_layer(parent_name)
                                child_layer = get_layer(child_name)
                                key_to = f"numCallsToLayer{child_layer}"
                                key_from = f"numCallsFromLayer{parent_layer}"
                                if not key_to in self.output[parent_name]:
                                    self.output[parent_name][key_to] = 0
                                if not key_from in self.output[child_name]:
                                    self.output[child_name][key_from] = 0

                                self.output[parent_name][key_to] += child_count
                                self.output[child_name][key_from] += child_count
                            
                        else:
                            self.output[child_name]["numIncomingCalls_B"] += child_count 
                        # self.output[child_name]["uniqueIncomingCalls"].add(parent_name)
                    else:
                        self.output[parent_name]["numExtCalls_B"] += child_count
                    
                    # Does the parent class call/interact with a Java data structure:
                    if any(dt in child_name for dt in data_types):
                        self.output[parent_name]["numDataStructureCalls"] += child_count

            self.traverse_call_tree(child, child.findall("node"), current_depth = current_depth + 1)
    
    def extract_average_relative_depth(self):
        get_paths(self.call_tree.getroot(), self.current_path, self.all_paths)

        for path in self.all_paths:
            for index, tuple in enumerate(path):
                className = tuple[0]
                count = tuple[1]
                if not className in self.totalCount.keys():
                    self.totalCount[className] = 0
                self.totalCount[className] += count
        
        for path in self.all_paths:
            for depth, tuple in enumerate(path):
                className = tuple[0]
                count = tuple[1]
                if not className in self.avgRelativeDepth.keys():
                    self.avgRelativeDepth[className] = 0
                relativeDepth = depth / (len(path) - 1)
                relativeDepth = relativeDepth * count / self.totalCount[className]
                self.avgRelativeDepth[className] += relativeDepth
        
        # Drop the redundant classes.
        self.avgRelativeDepth = {key: value for key, value in self.avgRelativeDepth.items() if key in reference_classes}

        for key, value in self.avgRelativeDepth.items():
            self.output[key]["avgRelativeDepth"] = value
            
    
    def extract_features(self):
        self.extract_average_relative_depth()
        self.output_CSV = pd.DataFrame.from_dict(self.output, orient="index")

        self.output_CSV["numOutgoingCalls"] = self.output_CSV["numIntCalls"] + self.output_CSV["numExtCalls_A"]

        self.output_CSV["numUniqueIncomingCalls"] = self.output_CSV["uniqueIncomingCalls"].apply(lambda x: len(x))  
        self.output_CSV["numUniqueOutgoingCalls"] = self.output_CSV["uniqueOutgoingCalls"].apply(lambda x: len(x))   
        self.output_CSV["avgExecTime"] = self.output_CSV["totalExecTime"] / self.output_CSV["helpCount"]
        self.output_CSV["avgDepth"] = self.output_CSV["totalDepth"] / self.output_CSV["helpCount"]
        # self.output_CSV["avgTime"] =  (self.output_CSV["totalTime"] / self.output_CSV["helpCount"]).round(self.ROUND)
        
        self.output_CSV["ratioInternalExternal"] = self.output_CSV["numIntCalls"] / self.output_CSV["numExtCalls_A"]
        self.output_CSV["ratioIncomingOutgoing"] = self.output_CSV["numIncomingCalls_A"] / self.output_CSV["numOutgoingCalls"]

        self.output_CSV["percObjectCreation"] = self.output_CSV["numObjectsCreated_A"] / self.output_CSV["numOutgoingCalls"]
        self.output_CSV["percLeaves"] = self.output_CSV["numLeaves"] / (self.output_CSV["numOutgoingCalls"] + self.output_CSV["numLeaves"])

        self.output_CSV.drop("uniqueIncomingCalls", axis=1, inplace=True)
        self.output_CSV.drop("uniqueOutgoingCalls", axis=1, inplace=True)
        self.output_CSV.drop("totalExecTime", axis=1, inplace=True)
        self.output_CSV.drop("totalDepth", axis=1, inplace=True) 
        self.output_CSV.drop("helpCount", axis=1, inplace=True)

        # Out of all outgoing calls a class make, what's the percentage that go to data structures?
        self.output_CSV["percDataStructure"] = self.output_CSV["numDataStructureCalls"] / (self.output_CSV["numExtCalls_B"] + self.output_CSV["numOutgoingCalls"])

        # If a class from layer X never calls a class from layer Y, the number of calls should be 0.
        keys_with_layer = [key for key in self.output_CSV.keys() if "Layer" in key]
        self.output_CSV[keys_with_layer] = self.output_CSV[keys_with_layer].fillna(0)

        # Derive percToLayerX and percFromLayerX features.
        cols_ToLayer = [col for col in self.output_CSV if 'ToLayer' in col]
        cols_FromLayer = [col for col in self.output_CSV if 'FromLayer' in col]
        for col in cols_ToLayer:
            self.output_CSV[f"perc{col[3:]}"] = self.output_CSV.apply(lambda row: 0 if (row[col] == 0 or row['numOutgoingCalls'] == 0) else row[col] / row['numOutgoingCalls'], axis=1)
        for col in cols_FromLayer:
            self.output_CSV[f"perc{col[3:]}"] = self.output_CSV.apply(lambda row: 0 if (row[col] == 0 or row['numIncomingCalls_A'] == 0) else row[col] / row['numIncomingCalls_A'], axis=1)

        # Sometimes, the ratio or percentage can't be computed because the denominator equals 0, fill it as -1 to represent N/A.
        self.output_CSV = self.output_CSV.replace(np.inf, -1)
        self.output_CSV = self.output_CSV.fillna(-1)

        self.output_CSV = self.output_CSV.applymap(lambda x: round(x, self.ROUND))

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
    # PROJECT_NAME = "jhotdraw"

    # Classes that are used by the paper, i.e. our reference classes. Or just a list of classes that we want for other projects.
    labels_csv = pd.read_csv(f"./data/ground_truth/{PROJECT_NAME}/labeled_classes_FINAL.csv", delimiter=",")
    
    # Convert the name notation to the notation used by JProfiler and store the classes and their labels in seperate lists.
    reference_classes = []
    true_labels = []
    for index, row in labels_csv.iterrows():
        # name = row["fullpathname"] # JHotDraw
        name = row["className"]
        label = row["label"]
        # reference_classes.append(convert_name(name)) # ONLY for SweetHome3D.
        reference_classes.append(name)
        true_labels.append(label)

    call_tree = ET.parse(f"./feature_extraction/raw_data/{PROJECT_NAME}/CallTree_withTime.xml")

    feature_extractor = FeatureExtractorXML(call_tree)
    feature_extractor.drop_redundant_classes(reference_classes)
    feature_extractor.extract_features()
    feature_extractor.add_true_labels(reference_classes, true_labels)

    feature_extractor.save_file(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_XML_v10.csv")