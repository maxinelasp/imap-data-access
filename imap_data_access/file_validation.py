"""Methods for managing and validating filenames."""
import re
import pathlib

def extract_filename_components(filename: type[str | pathlib.Path]):
    """
    Extracts all components from filename.

    Will return a dictionary with the following keys:
    { instrument, datalevel, descriptor, startdate, enddate, version, extension }

    Descriptor is an optional field. If it is not present in the filename, the dict
    value for "descriptor" will be "".

    If a match is not found, a ValueError will be raised.

    Parameters
    ----------
    filename : Pathlib.Path or str
        Path of dependency data.

    Returns
    -------
    components : dict
        Dictionary containing components.

    """
    pattern = (
        r"^imap_"
        r"(?P<instrument>[^_]+)_"
        r"(?P<datalevel>[^_]+)_"
        r"(?P<descriptor>[^_]*)_?"  # optional
        r"(?P<startdate>\d{8})_"
        r"(?P<enddate>\d{8})_"
        r"(?P<version>v\d{2}-\d{2})"
        r"\.(cdf|pkts)$"
    )
    if isinstance(filename, pathlib.Path):
        filename = filename.name

    match = re.match(pattern, filename)
    if match is None:
        raise ValueError(f"Filename {filename} does not match expected pattern")

    components = match.groupdict()
    return components
