import pandas as pd

class FeatureExtractorCSV:
    def __init__(self, objects_all, objects_gc):
        self.objects_all = objects_all
        self.objects_gc = objects_gc
        self.ROUND = 3 # Decimals of rounding.
        self.output = pd.DataFrame(self.objects_all["Name"]) # Stores the extracted features in this CSV.

        pd.set_option("display.max_colwidth", None) # For testing purposes, don't truncate name when printing.
    
    def extract_num_of_total_objects(self):
        self.output["numObjectsTotal"] = self.objects_all["Instance Count"] * 1.0

    def extract_num_of_gc_objects(self):
        self.output = self.output.merge(self.objects_gc[["Name", "Instance Count"]], how="left").fillna(0)
        self.output.rename(columns = {"Instance Count": "numObjectsDeallocated"}, inplace = True)

    def extract_avg_size_object(self):
        # Object size measured in kB where we assume that 1 kB = 1000 bytes.
        self.output["avgObjectSize"] = self.objects_all["Size (bytes)"] / (self.objects_all["Instance Count"] * 1000)
        self.output["avgObjectSize"] = self.output["avgObjectSize"].round(self.ROUND)
    
    def extract_ratio_gc_objects(self):
        self.output["percDeallocated"] = self.output["numObjectsDeallocated"] / self.output["numObjectsTotal"]
        self.output["percDeallocated"] = self.output["percDeallocated"].round(self.ROUND)

    def save_file(self, file_path: str):
        self.output.rename(columns = {"Name": "className"}, inplace = True)
        self.output.to_csv(file_path, sep=",", index=False)   


if __name__ == "__main__":
    # PROJECT_NAME = "sweethome3d"
    PROJECT_NAME = "test_project"

    objects_all = pd.read_csv(f"./feature_extraction/raw_data/{PROJECT_NAME}/RecordedObjectsAll.csv")
    objects_gc = pd.read_csv(f"./feature_extraction/raw_data/{PROJECT_NAME}/RecordedObjectsGarbage.csv")

    feature_extractor = FeatureExtractorCSV(objects_all, objects_gc)
    feature_extractor.extract_num_of_total_objects()
    feature_extractor.extract_num_of_gc_objects()
    feature_extractor.extract_avg_size_object()
    feature_extractor.extract_ratio_gc_objects()

    feature_extractor.save_file(f"./data/dataset/{PROJECT_NAME}/features_{PROJECT_NAME}_CSV.csv")