"""Methods for managing and validating filenames and filepaths"""
import re
import pathlib
from datetime import datetime

VALID_INSTRUMENTS = {
    "codice",
    "glows",
    "hit",
    "hi-45",
    "hi-90",
    "idex",
    "lo",
    "mag",
    "swapi",
    "swe",
    "ultra-45",
    "ultra-90",
}

VALID_DATALEVELS = {"l0", "l1", "l1a", "l1b", "l1c", "l1d", "l2"}

VALID_FILE_EXTENSION = {"pkts", "cdf"}

FILENAME_CONVENTION = (
            "<mission>_<instrument>_<datalevel>_<descriptor>_"
            "<startdate>_<enddate>_<version>.<extension>"
        )


class InvalidScienceFileError(Exception):
    """Indicates a bad file type"""
    pass


class ScienceFilepathManager:
    def __init__(self, filename: str | pathlib.Path):
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
        filename : str | pathlib.Path
            Science data filename or file path.
        """
        # TODO: Accomodate path or filename
        self.filename = filename

        try:
            split_filename = ScienceFilepathManager.extract_filename_components(self.filename)
        except ValueError:
            raise InvalidScienceFileError(
                f"Invalid filename. Expected file to match format: "
                f"{FILENAME_CONVENTION}"
            )

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
        """ Validate the filename and populate the error message for wrong attributes.

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
                self.instrument,
                self.data_level,
                self.descriptor,
                self.startdate,
                self.enddate,
                self.version,
                self.extension,
            ]
        ):
            error_message = f"Invalid filename, missing attribute. Filename " \
                                 f"convention is {FILENAME_CONVENTION} \n"

        if self.instrument not in VALID_INSTRUMENTS:
            error_message += f"Invalid instrument {self.instrument}. Please choose " \
                             f"from " f"{VALID_INSTRUMENTS} \n"
        if self.data_level not in VALID_DATALEVELS:
            error_message += f"Invalid data level {self.data_level}. Please choose " \
                             f"from " f"{VALID_DATALEVELS} \n"
        if not self.is_valid_date(self.startdate):
            error_message += "Invalid start date format. Please use YYYYMMDD format. \n"
        if not self.is_valid_date(self.enddate):
            error_message += "Invalid end date format. Please use YYYYMMDD format. \n"
        if not bool(re.match(r"^v\d{2}-\d{2}$", self.version)):
            error_message += "Invalid version format. Please use vxx-xx format. \n"

        if self.extension not in VALID_FILE_EXTENSION or (
                (self.data_level == "l0" and self.extension != "pkts")
                or (self.data_level != "l0" and self.extension != "cdf")
        ):
            error_message += "Invalid extension. Extension should be pkts for data " \
                             "level l0 and cdf for data level higher than l0 \n"

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

    @staticmethod
    def extract_filename_components(filename: str | pathlib.Path):
        """
        Extracts all components from filename. Does not validate instrument or level.

        Will return a dictionary with the following keys:
        { instrument, datalevel, descriptor, startdate, enddate, version, extension }

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
            r"(?P<descriptor>[^_]+)_"
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
        components["extension"] = match.group(7)
        return components

    def construct_upload_path(self):
        """Construct upload path from class variables

        Returns
        -------
        str
            Upload path
        """
        upload_path = (
            f"imap/{self.instrument}/{self.data_level}/"
            f"{self.startdate[:4]}/{self.startdate[4:6]}/{self.filename}"
        )

        return upload_path
