import os
import matplotlib.pyplot as plt
from open_phy import open_phy
from process_functions import *
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw
import pandas as pd
import seaborn as sns

os.environ['KILOSORT3_PATH'] = os.path.join('C:\\', 'github', 'Kilosort')
os.environ['KILOSORT2_5_PATH'] = os.path.join('C:\\', 'github', 'Kilosort2_5')
os.environ['IRONCLUST_PATH'] = os.path.join('C:\\', 'github', 'ironclust')

def test_loop(params):
    # Get the recording
    recording_folder = os.path.join('D:\\', 'Test', 'ES029')
    recording_name = 'ES029_2022-09-14_bot72_0_g0'
    recording_save = os.path.join('C:\\', 'github', 'spikeline', 'recording_save')
    tic = ticker()
    recording_preprocessed = get_recording(recording_folder, recording_name, recording_save, load_new=False)
    tic = ticker(tic, text='loading recording')

    sorter_list = params['sorter_list']
    path = os.path.join('C:\\', 'github', 'spikeline', 'gt_sorter')  # ES029_2022-09-14_bot72_0_g0
    gt_sorter = se.PhySortingExtractor.load_from_folder(path)

    sets = [{}]
    for param_set in sets:
        sorters = run_spike_sorters(recording_preprocessed, sorter_list, run_new=False)
        tic = ticker(tic, text='sorting')
        gt_comp = sc.compare_sorter_to_ground_truth(gt_sorter, sorters[sorter_list[0]], gt_name='ground_truth',
                                                    tested_name=sorter_list[0], compute_labels=True, verbose=True)
        print('test')


if __name__ == '__main__':
    p = {
        'sorter_list': ['kilosort3']
        # 'sorter_list': ['kilosort3', 'kilosort2_5', 'ironclust', 'herdingspikes']

    }
    test_loop(p)
