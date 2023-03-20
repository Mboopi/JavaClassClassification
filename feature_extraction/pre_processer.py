import pandas as pd
from feature_exploration import find_file_paths, convert_name

class PreProcesser:
    def __init__(self, CSV_paths: list):
        self.CSVs = [] # Store the CSV files, taken from the paths to the CSVs.
        for path in CSV_paths:
            self.CSVs.append(pd.read_csv(path))
    
        self.combined_CSV = None # Stores the combined CSV.

        pd.set_option("display.max_colwidth", None) # For testing purposes, don't truncate name when printing.

    '''Method that combines the individual CSV files into 1 CSV file. 
    Duplicate entries are merged into 1 entry by summing up the values of their columns.'''
    def combine_CSV_files(self):
        self.combined_CSV = pd.concat(file for file in self.CSVs) # Concatenate the individual files into 1 file.
        self.combined_CSV = self.combined_CSV.groupby('Name', as_index=False).sum() # Merge duplicate classes.

    '''Method that merges the anonymous ($X where X is a digit) into the outer class, i.e. the anonymous class
    is considered to be the same as the outer class.'''
    def merge_anom_classes(self):
        self.combined_CSV["Name"] = self.combined_CSV["Name"].str.removesuffix("[ ]") # First remove any [ ] from class names.
        self.combined_CSV = self.combined_CSV[~self.combined_CSV['Name'].str.contains("Test")] # Drop Test classes.
        self.combined_CSV["Name"] = self.combined_CSV["Name"].replace(to_replace="[$]\d+", value="", regex=True) # Remove any occurences of $int.
        self.combined_CSV = self.combined_CSV.groupby('Name', as_index=False).sum() # Merge duplicate classes.

    '''Method that given a list of reference classes, drops the non-reference classes from the combined CSV file.'''
    def drop_redundant_classes(self, reference_classes: list):
        self.merge_anom_classes()
        # https://stackoverflow.com/questions/27965295/dropping-rows-from-dataframe-based-on-a-not-in-condition
        self.combined_CSV = self.combined_CSV[self.combined_CSV['Name'].isin(reference_classes)] # Keep only the reference classes.

    '''Method that saves the combined CSV file.'''
    def save_file(self, file_path: str):
        self.combined_CSV.to_csv(file_path, sep=",", index=False)        
    

if __name__ == "__main__":
    PROJECT_NAME = "sweethome3d"
    # PROJECT_NAME = "test_project"

    # Classes that are used by the paper, i.e. our reference classes.
    labels_csv = pd.read_csv(f"./data/ground_truth/{PROJECT_NAME}/labeled_classes.csv")
    labels_csv.pop("index")
    labels_csv.pop("case")
    
    # Convert the name notation to the notation used by JProfiler and store the classes in a list.
    reference_classes = []
    for name in labels_csv["fullpathname"]:
        reference_classes.append(convert_name(name))

    # Paths to CSV recorded objects CSVs.
    recorded_objects_all = find_file_paths("All.csv", PROJECT_NAME)
    recorded_objects_gc = find_file_paths("Garbage.csv", PROJECT_NAME)

    all_objects_processor = PreProcesser(recorded_objects_all)
    all_objects_processor.combine_CSV_files()
    all_objects_processor.drop_redundant_classes(reference_classes)
    all_objects_processor.save_file(f"./feature_extraction/raw_data/{PROJECT_NAME}/RecordedObjectsAll.csv")

    gc_objects_processor = PreProcesser(recorded_objects_gc)
    gc_objects_processor.combine_CSV_files()
    gc_objects_processor.drop_redundant_classes(reference_classes)
    gc_objects_processor.save_file(f"./feature_extraction/raw_data/{PROJECT_NAME}/RecordedObjectsGarbage.csv")