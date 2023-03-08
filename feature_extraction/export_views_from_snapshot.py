import sys
import os
import subprocess

# This python file should be run from the terminal. For instance, run the following command:
# python export_views_from_snapshot.py (...continue on next line...)
# <path to jpexport executable> <full path where snapshot file is located> <full name of package to be whitelisted>
# Note: there should be only 1 snapshot file, otherwise it will take the last file that it finds.

''' Method that initializes the required variables, it returns:
  -jpexportpath: path to /bin/jpexport executable.
  -snapshot_directory: path to the folder where the snapshot file is located, excluding the snapshot itself.
  -snapshot: name of snapshot file.
  -package: fully qualified package name for whitelisting (applies to Allocation Hotspots only), e.g. com.eteks.sweethome3d'''
def init():
    jpexport_path = sys.argv[1] # Get path to /bin/jpexport executable from argument passed from the command line.
    snapshot_directory= sys.argv[2]
    package = sys.argv[3]
    
    snapshot = "" # Full name of snapshot file, i.e. including full path and extension.
    file_extension = ".jps"
    ls = os.listdir(snapshot_directory)
   
    for file_name in ls:
        if file_extension in file_name:
            snapshot = f"{snapshot_directory}/{file_name}"
    
    return jpexport_path, snapshot_directory, snapshot, package

''' Method that exports a view from the snapshots by running in the terminal:
> ...jpexport "NAME_SNAPSHOT.jps" "VIEW_NAME" -option1=val1 ... -optionN=valN "OUTPUT_FILE.EXTENSION"
Arguments:
  -exec_path: path to jpexport executable.
  -snapshot: file name of the snapshot file.
  -view_name: one of the views supported by JProfiler.
  -options: options corresponding to the view.
  -output_name: name of the output file, should include its extension. '''
def export_view(exec_path, snapshot, view_name, options, output_name):
    cmd_string = f"{exec_path} '{snapshot}' '{view_name}' {options} '{output_name}'"
    subprocess.run(cmd_string, shell=True)


if __name__ == "__main__":
    jpexport_path, snapshot_directory, snapshot, package = init()
    snapshot_name = snapshot.removesuffix(".jps")

    view_names = ["CallTree", "AllocationHotspots", "RecordedObjects", "RecordedObjects"]
    options = ["-format=xml -aggregation=class -threadstatus=all",
               f"-format=xml -aggregation=class -package={package} -liveness=all -expandbacktraces=true",
               "-format=csv -aggregation=class -liveness=live",
               "-format=csv -aggregation=class -liveness=gc"]
    output_names = [f"{view_names[0]}.xml",
                    f"{view_names[1]}.xml",
                    f"{view_names[2]}Live.csv",
                    f"{view_names[3]}Garbage.csv"] 

    for i in range(len(view_names)):
        export_view(jpexport_path, snapshot, view_names[i], options[i], f"{snapshot_name}_{output_names[i]}")

'''
TO DO:
  -Change the script such that it works from any directory, i.e. 
   we should be able to pass the output directory to the command line, so that we can run this script
   from any location. This can be done by adding the output directory before the output name.
'''