import xml.etree.ElementTree as ET
import re

file_path = "./feature_extraction/raw_data/test_project/CallTree.xml"
tree = ET.parse(file_path)
root = tree.getroot()

file_path2 = "./feature_extraction/raw_data/test_project/CallTree2.xml"
tree2 = ET.parse(file_path2)
root2 = tree2.getroot()

root.extend(root2)

for child in root.iter():
    if child.tag == "node":
        child.attrib.pop("lineNumber")
        child.attrib.pop("percent")
        child.attrib.pop("time")
        
        regex = "[$d]\d+"
        class_name = child.attrib["class"]
        if bool(re.search(regex, class_name)):
            child.set("class", re.sub(regex, "", class_name))
        # print(child.tag, child.attrib)

with open("./feature_extraction/raw_data/test_project/CallTreePROCESSED.xml", "wb") as f:
    tree.write(f, encoding="utf-8")
  
# test = root.findall(".//node[@class='$']")
# for t in test:
#     print(t.attrib)
