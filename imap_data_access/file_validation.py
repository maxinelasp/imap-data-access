"""Methods for managing and validating filenames and filepaths"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import imap_data_access


def extract_filename_components(filename: str | Path):
    """
    Extracts all components from filename. Does not validate instrument or level.

    Will return a dictionary with the following keys:
    { instrument, datalevel, descriptor, startdate, enddate, version, extension }

    If a match is not found, a ValueError will be raised.

    Parameters
    ----------
    filename : Path or str
        Path of dependency data.

    Returns
    -------
    components : dict
        Dictionary containing components.

    """
    pattern = (
        r"^(?P<mission>imap)_"
        r"(?P<instrument>[^_]+)_"
        r"(?P<datalevel>[^_]+)_"
        r"(?P<descriptor>[^_]+)_"
        r"(?P<startdate>\d{8})_"
        r"(?P<enddate>\d{8})_"
        r"(?P<version>v\d{2}-\d{2})"
        r"\.(?P<extension>cdf|pkts)$"
    )
    if isinstance(filename, Path):
        filename = filename.name

    match = re.match(pattern, filename)
    if match is None:
        raise ValueError(
            f"Filename {filename} does not match expected pattern: "
            f"{imap_data_access.FILENAME_CONVENTION}"
        )

    components = match.groupdict()
    return components


def construct_path_from_filename(filename: str | Path) -> Path:
    """
    Given the filename, construct the expected upload path.

    Example path: imap/mag/l1a/2021/01/imap_mag_l1a_burst_20210101_20210102_v01-01.cdf

    Parameters
    ----------
    filename: str | Path
        File name or path to create the path from. Should match IMAP file convention:
        <mission>_<instrument>_<datalevel>_<descriptor>_<startdate>_<enddate>_<version>.<extension>

    Returns
    -------
    Path
        File path generated from the filename.

    """

    components = extract_filename_components(filename)

    return (
        Path(
            f"{components['mission']}/{components['instrument']}/"
            f"{components['datalevel']}/{components['startdate'][:4]}/"
            f"{components['startdate'][4:6]}"
        )
        / filename
    )


class InvalidScienceFileError(Exception):
    """Indicates a bad file type"""

    pass


class ScienceFilepathManager:
    def __init__(self, filename: str | Path):
        """Class to store file pattern

        Current filename convention:
        <mission>_<instrument>_<datalevel>_<descriptor>_<startdate>_<enddate>_<version>.<extension>

        NOTE: There are no optional parameters anymore. All parameters are required.
        <mission>: imap
        <instrument>: idex, swe, swapi, hi-45, ultra-45 and etc.
        <datalevel> : l1a, l1b, l1, l3a and etc.
        <descriptor>: descriptor stores information specific to instrument. This is
            decided by each instrument. For L0, "raw" is used.
        <startdate>: startdate is the earliest date in the data. Format - YYYYMMDD
        <enddate>: Some instrument and some data level requires to store date range.
            If there is no end date, then startdate will be used as enddate as well.
            Format - YYYYMMDD.
        <version>: This stores software version and data version. Version format is
            vxx-xx.

        Parameters
        ----------
        filename : str | Path
            Science data filename or file path.
        """
        # TODO: Accomodate path or filename
        self.filename = filename

        try:
            split_filename = extract_filename_components(self.filename)
        except ValueError as err:
            raise InvalidScienceFileError(
                f"Invalid filename. Expected file to match format: "
                f"{imap_data_access.FILENAME_CONVENTION}"
            ) from err

        self.mission = split_filename["mission"]
        self.instrument = split_filename["instrument"]
        self.data_level = split_filename["datalevel"]
        self.descriptor = split_filename["descriptor"]
        self.startdate = split_filename["startdate"]
        self.enddate = split_filename["enddate"]
        self.version = split_filename["version"]
        self.extension = split_filename["extension"]

        self.error_message = self.validate_filename()
        if self.error_message:
            raise InvalidScienceFileError(f"{self.error_message}")

    def validate_filename(self):
        """Validate the filename and populate the error message for wrong attributes.

        The error message will be an empty string if the filename is valid. Otherwise,
        all errors with the filename will be put into the error message.

        Returns
        -------
        error_message: str
            Error message for specific missing attribute, or "" if the file name is
            valid.
        """
        error_message = ""

        if any(
            attr is None or attr == ""
            for attr in [
                self.mission,
                self.instrument,
                self.data_level,
                self.descriptor,
                self.startdate,
                self.enddate,
                self.version,
                self.extension,
            ]
        ):
            error_message = (
                f"Invalid filename, missing attribute. Filename "
                f"convention is {imap_data_access.FILENAME_CONVENTION} \n"
            )
        if self.mission != "imap":
            error_message += f"Invalid mission {self.mission}. Please use imap \n"

        if self.instrument not in imap_data_access.VALID_INSTRUMENTS:
            error_message += (
                f"Invalid instrument {self.instrument}. Please choose "
                f"from "
                f"{imap_data_access.VALID_INSTRUMENTS} \n"
            )
        if self.data_level not in imap_data_access.VALID_DATALEVELS:
            error_message += (
                f"Invalid data level {self.data_level}. Please choose "
                f"from "
                f"{imap_data_access.VALID_DATALEVELS} \n"
            )
        if not self.is_valid_date(self.startdate):
            error_message += "Invalid start date format. Please use YYYYMMDD format. \n"
        if not self.is_valid_date(self.enddate):
            error_message += "Invalid end date format. Please use YYYYMMDD format. \n"
        if not bool(re.match(r"^v\d{2}-\d{2}$", self.version)):
            error_message += "Invalid version format. Please use vxx-xx format. \n"

        if self.extension not in imap_data_access.VALID_FILE_EXTENSION or (
            (self.data_level == "l0" and self.extension != "pkts")
            or (self.data_level != "l0" and self.extension != "cdf")
        ):
            error_message += (
                "Invalid extension. Extension should be pkts for data "
                "level l0 and cdf for data level higher than l0 \n"
            )

        return error_message

    @staticmethod
    def is_valid_date(input_date: str) -> bool:
        """Check input date string is in valid format and is correct date

        Parameters
        ----------
        input_date : str
            Date in YYYYMMDD format.

        Returns
        -------
        bool
            Whether date input is valid or not
        """

        # Validate if it's a real date
        try:
            # This checks if date is in YYYYMMDD format.
            # Sometimes, date is correct but not in the format we want
            datetime.strptime(input_date, "%Y%m%d")
            return True
        except ValueError:
            return False

    def upload_path(self):
        """Construct upload path from class variables

        Returns
        -------
        str
            Upload path
        """
        upload_path = (
            f"{self.mission}/{self.instrument}/{self.data_level}/"
            f"{self.startdate[:4]}/{self.startdate[4:6]}/{self.filename}"
        )

        return upload_path
