import numpy as np

def save_array(filename, data, column_names, comment):
    if data.ndim != 2 or data.shape[1] != len(column_names):
        raise ValueError(
            "The number of column names must match the number of data columns."
        )

    # savetxt automatically prefixes the header with "# "
    header = f"{comment}\n" + ",".join(column_names)

    np.savetxt(
        filename,
        data,
        delimiter=",",
        header=header,
        comments="# ",
    )

def save_dict(filename:str, dataDict:dict, comment:str):
    # savetxt automatically prefixes the header with "# "
    
    column_names = dataDict.keys()
    header = f"{comment}\n" + ",".join(column_names)
    data = np.array(tuple(dataDict.values())).transpose()
    np.savetxt(
        filename,
        data,
        delimiter=",",
        header=header,
        comments="# ",
    )

def load_array(filename):
    with open(filename, "r") as file:
        skip_lines = 0
        last_comment_index = -1
    
        # Read lines sequentially to find the last comment line
        for i, line in enumerate(file):
            if line.strip().startswith("#"):
                last_comment_index = i
            else:
                break  # Stop checking once regular data starts
        
        # If comments exist, skip everything up to the very last comment line
        if last_comment_index != -1:
            skip_lines = last_comment_index

        # Reset the file pointer to the beginning of the file
        file.seek(0)
        return np.genfromtxt(
            file,
            delimiter=",",
            names=True,
            comments="#",
            skip_header=skip_lines,
            dtype=float,
        )
