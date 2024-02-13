from pathlib import Path

import pytest

from imap_data_access.file_validation import ScienceFilepath


def test_extract_filename_components():
    valid_filename = "imap_mag_l1a_burst_20210101_20210102_v01-01.pkts"

    expected_output = {
        "mission": "imap",
        "instrument": "mag",
        "datalevel": "l1a",
        "descriptor": "burst",
        "startdate": "20210101",
        "enddate": "20210102",
        "version": "v01-01",
        "extension": "pkts",
    }

    assert (
        ScienceFilepath.extract_filename_components(valid_filename) == expected_output
    )

    # Descriptor is required
    invalid_filename = "imap_mag_l1a_20210101_20210102_v01-01.cdf"

    with pytest.raises(ScienceFilepath.InvalidScienceFileError):
        ScienceFilepath.extract_filename_components(invalid_filename)

    # start and end time are required
    invalid_filename = "imap_mag_l1a_20210101_v01-01"
    with pytest.raises(ScienceFilepath.InvalidScienceFileError):
        ScienceFilepath.extract_filename_components(invalid_filename)

    valid_filepath = Path("/test/imap_mag_l1a_burst_20210101_20210102_v01-01.cdf")
    expected_output["extension"] = "cdf"
    assert (
        ScienceFilepath.extract_filename_components(valid_filepath) == expected_output
    )

    invalid_ext = "imap_mag_l1a_burst_20210101_20210102_v01-01.txt"
    with pytest.raises(ScienceFilepath.InvalidScienceFileError):
        ScienceFilepath.extract_filename_components(invalid_ext)


def test_construct_sciencefilepathmanager():
    valid_filename = "imap_mag_l1a_burst_20210101_20210102_v01-01.cdf"
    sfm = ScienceFilepath(valid_filename)
    assert sfm.mission == "imap"
    assert sfm.instrument == "mag"
    assert sfm.data_level == "l1a"
    assert sfm.descriptor == "burst"
    assert sfm.startdate == "20210101"
    assert sfm.enddate == "20210102"
    assert sfm.version == "v01-01"
    assert sfm.extension == "cdf"

    invalid_filename = "imap_mag_l1a_burst_20210101_20210102_v01-01"
    with pytest.raises(ScienceFilepath.InvalidScienceFileError):
        ScienceFilepath(invalid_filename)

    invalid_filename = "imap_mag_l1a_burst_20210101_20210102_v01-01.pkts"
    with pytest.raises(ScienceFilepath.InvalidScienceFileError):
        ScienceFilepath(invalid_filename)

    invalid_filename = "imap_sdc_l1a_burst_20210101_20210102_v01-01.cdf"
    with pytest.raises(ScienceFilepath.InvalidScienceFileError):
        ScienceFilepath(invalid_filename)

    valid_filepath = Path("/test/imap_mag_l1a_burst_20210101_20210102_v01-01.cdf")
    sfm = ScienceFilepath(valid_filepath)

    assert sfm.instrument == "mag"
    assert sfm.data_level == "l1a"
    assert sfm.descriptor == "burst"
    assert sfm.startdate == "20210101"
    assert sfm.enddate == "20210102"
    assert sfm.version == "v01-01"
    assert sfm.extension == "cdf"


def test_is_valid_date():
    valid_date = "20210101"
    assert ScienceFilepath.is_valid_date(valid_date)

    invalid_date = "2021-01-01"
    assert not ScienceFilepath.is_valid_date(invalid_date)

    invalid_date = "20210132"
    assert not ScienceFilepath.is_valid_date(invalid_date)

    invalid_date = "2021010"
    assert not ScienceFilepath.is_valid_date(invalid_date)


def test_construct_upload_path():
    valid_filename = "imap_mag_l1a_burst_20210101_20210102_v01-01.cdf"
    sfm = ScienceFilepath(valid_filename)
    expected_output = Path(
        "imap/mag/l1a/2021/01/imap_mag_l1a_burst_20210101_20210102_v01-01.cdf"
    )

    assert sfm.construct_path() == expected_output


def test_data_dir():
    optional_data_dir = Path("/test/data")
    valid_filename = Path("imap_mag_l1a_burst_20210101_20210102_v01-01.cdf")

    sfm = ScienceFilepath(valid_filename, data_dir=optional_data_dir)
    expected_output = Path(
        "/test/data/imap/mag/l1a/2021/01/"
        "imap_mag_l1a_burst_20210101_20210102_v01-01.cdf"
    )

    assert sfm.construct_path() == expected_output
