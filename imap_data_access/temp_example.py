import processing_input_file
# To construct some dependencies

# In the dependency resolution phase, we collect some information on ancillary files

science_file_1 = processing_input_file.ScienceInput("imap_mag_l1a_norm-magi_20240312_v000.cdf", "imap_mag_l1a_norm-magi_20240310_v000.cdf")
# ancillary_files = processing_input_file.AncillaryInput()
science_file_2 = processing_input_file.ScienceInput("imap_mag_l1a_burst-magi_20240312_v000.cdf", "imap_mag_l1a_burst-magi_20240310_v000.cdf")

print(science_file_1)
print(science_file_1.get_time_range())

processing_input = processing_input_file.ProcessingInputCollection([science_file_1])

serialized = processing_input.serialize()
print(serialized)
# serialized would get passed to the CLI


# Then, within the CLI, you can deserialize back into a ProcessingInputCollection object
processing_output = processing_input_file.ProcessingInputCollection()
processing_output.deserialize(serialized)

print(processing_output)

ancillary_file_1 = processing_input_file.AncillaryInput("imap_mag_l1b-cal_20250101_v001.cdf", "imap_mag_l1b-cal_20250103-20250104_v002.cdf")
print(ancillary_file_1)

anc_input = processing_input_file.ProcessingInputCollection([ancillary_file_1, science_file_1, science_file_2])

print(anc_input)
print(anc_input.serialize())

test_input = processing_input_file.ProcessingInputCollection()
print("====")
print(processing_output.deserialize(anc_input.serialize()))
print(processing_output.processing_input)

print(processing_output.get_science_files())