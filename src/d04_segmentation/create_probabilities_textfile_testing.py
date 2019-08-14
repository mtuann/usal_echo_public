# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 14:03:56 2019

@author: court
"""

from src.d00_utils.db_utils import dbReadWriteViews
import os
import datetime
import pandas as pd


def create_probabilities_textfile_testing():
    """
    Produces text file with view ground truths for segmentation model testing. 
    
    This function writes a text file in the same format as the output of the 
    view classification model, but replacing the model classification 
    probabilities with the ground truth classification labels.
    
    
    The following steps are performend:
        1. Gets io_views: frames_by_volume_mask view & instances_unique_master_list
        2. Merges these to get filenames
        3. Filters the resulting table by param: instanceids
        4. Create probabilities table
        5. Writes the probabilities textfile to data/d04_segmentation folder
    
    :param: instanceids: a list of instance ids
    :return nothing
    """

    # 1. Gets frames_by_volume_mask view
    io_views = dbReadWriteViews()
    frames_by_volume_mask = io_views.get_table("frames_by_volume_mask")
    frames_by_volume_mask = frames_by_volume_mask.drop(columns=['indexinmglist', 'frame'])
    frames_by_volume_mask = frames_by_volume_mask.drop_duplicates()
    
    #frames_by_volume_mask = frames_by_volume_mask[
    #    frames_by_volume_mask["view_exists"] == True
    #]
    instances_unique_master_list = io_views.get_table("instances_w_labels_test_downsampleby5")
    print('instance_list size: {}'.format(instances_unique_master_list.shape))
    
    # 2. filter frames_by_volume_mask to only include instances_unique_master_list
    df = pd.merge(instances_unique_master_list, frames_by_volume_mask, how = "left", 
                  on = ['studyidk', 'instanceidk'])
    
    #frames_by_volume_mask[frames_by_volume_mask['instanceidk'].isin(instances_unique_master_list['instanceidk'])]
    
    #3. Drop instance index, and delete any duplicates
    #df = df.drop(columns=['indexinmglist'])
    #df = df.drop_duplicates()


    # 3. Create the probabilities table
    prob_tb = pd.DataFrame(
        columns=[
            "study",
            "image",
            "plax_far",
            "plax_plax",
            "plax_laz",
            "psax_az",
            "psax_mv",
            "psax_pap",
            "a2c_lvocc_s",
            "a2c_laocc",
            "a2c",
            "a3c_lvocc_s",
            "a3c_laocc",
            "a3c",
            "a4c_lvocc_s",
            "a4c_laocc",
            "a4c",
            "a5c",
            "other",
            "rvinf",
            "psax_avz",
            "suprasternal",
            "subcostal",
            "plax_lac",
            "psax_apex",
        ]
    )
    
    for i in df.index:
        prob_tb.at[i, "study"] = "/home/ubuntu/data/01_raw/test_downsampleby5"
        filename = df.at[i, "instancefilename"]
        studyidk = df.at[i, "studyidk"]
        prob_tb.at[i, "image"] = (
            "a_" + str(studyidk).strip() + "_" + str(filename).strip() + ".dcm"
        )
        if df.at[i, "view"] =="A4C":
            prob_tb.at[i, "a4c"] = 0.9898
        elif df.at[i, "view"] =="A2C":
            prob_tb.at[i, "a2c"] = 0.9898

    df_3 = prob_tb.fillna(0)
    print('df_3: {}'.format(df_3.shape))

    # 5. Writes the probabilities textfile to data/d04_segmentation folder
    project_dir = os.path.dirname(os.getcwd())
    data_dir = os.path.join(project_dir, "data", "d04_segmentation")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    time_stamp = datetime.date.today()
    file_name = "view_probabilities_test" + str(time_stamp) + ".txt"
    data_path = os.path.join(data_dir, file_name)

    df_3.to_csv(data_path, index=None, header=True, sep="\t")
