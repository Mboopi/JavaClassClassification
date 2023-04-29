import json

# File for adding empty traces property to JSON file without any traces, because the JSON merger
# assumes that every JSON file contains a traces property with a list of trace names.

with open(f"/Users/mboopi/Documents/GitHub/JavaClassClassification/extra_visualization/sweethome3d_abstractinput.json", "r") as f:
    file = json.load(f)

nodes = file["elements"]["nodes"]
edges = file["elements"]["edges"]

for node in nodes:
    node["data"]["properties"]["traces"] = []

for edge in edges:
    edge["data"]["properties"]["traces"] = []

# modifed_file = json.dumps(file, indent=2)

with open(f"/Users/mboopi/Documents/GitHub/JavaClassClassification/extra_visualization/sweethome3d_abstractinput.json", "w") as outfile:
    json.dump(file, outfile, indent=2)
outfile.close()