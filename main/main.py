"""
Neuropixels preprocessing and spike sorting
"""
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
os.environ['HDSORT_PATH'] = os.path.join('C:\\', 'github', 'HDsort')
os.environ['WAVECLUS_PATH'] = os.path.join('C:\\', 'github', 'wave_clus')
os.environ['COMBINATO_PATH'] = os.path.join('C:\\', 'github', 'combinato')
os.environ['TEMPDIR'] = os.path.join('D:\\', 'temp')


def main():
    load_new = False
    sort_new = False
    phy_export_new = False
    run_phy = False
    compare_sorters = False
    test_truth = True
    recording_folder = os.path.join('D:\\', 'Test', 'ES029')
    recording_name = 'ES029_2022-09-14_bot72_0_g0'
    project_dir = os.path.dirname(os.getcwd())
    recording_save = os.path.join(project_dir, 'recording_save')
    if load_new:
        recording_save = reset_folder(recording_save)
    tic = ticker()

    # Load or generate the preprocessed data
    recording_preprocessed = get_recording(recording_folder, recording_name, recording_save, load_new=load_new)
    tic = ticker(tic, text='loading recording')

    # Load or generate the sorter output
    sorter_list = ['kilosort3', 'kilosort2_5', 'ironclust', 'herdingspikes']
    sorters = run_spike_sorters(recording_preprocessed, sorter_list, run_new=sort_new)
    tic = ticker(tic, text='sorting')

    # Test ground truth
    if test_truth:
        gt_path = os.path.join(project_dir, 'ground_truth')
        gt_sorter = si.read_sorter_folder(gt_path)

    # Export the sorter output to a phy folder for manual curation
    if phy_export_new:
        save_folders = export_for_phy(sorters, recording_preprocessed, tic=tic)
    else:
        with open('save_folder_dict', 'rb') as f:
            save_folders = pickle.load(f)

    if run_phy:
        for save_folder in save_folders:
            print(f'Opening {save_folder} in phy...')
            open_phy(save_folder)
        tic = ticker(tic, text='manual curation')

    if compare_sorters:
        compare_path = os.path.join(os.path.dirname(os.getcwd()), 'comp_multi_1')
        compare_new = True
        if compare_new:
            comp_multi = sc.compare_multiple_sorters(sorting_list=list(sorters.values()),
                                                     name_list=list(sorters.keys()), verbose=True, delta_time=0.2,
                                                     match_score=.5, spiketrain_mode='union')
            comp_multi.save_to_folder(compare_path)
        else:
            comp_multi = sc.MultiSortingComparison.load_from_folder(compare_path)

        # visualize_comparison(comp_multi)
        # for u in [397, 680, 600, 915, 717, 608, 790, 393, 828, 241, 234, 172, 902, 222, 223, 63, 60, 376, 378, 259, 251,
        #           778, 242, 799, 5799, 898, 474, 476, 365, 319, 243]:
        #     print(f'{u}: {units[u]["unit_ids"]}')

        all_sort = comp_multi.get_agreement_sorting(minimum_agreement_count=1)
        export_for_phy({f'all_sort2': all_sort}, recording_preprocessed, filter=False)

        # sw.plot_crosscorrelograms(all_sort, unit_ids=[666, 502], bin_ms=.1)
        # plt.show()

        # for i in range(len(sorters)):
        #     agree_sort = comp_multi.get_agreement_sorting(minimum_agreement_count=i + 1)
        #     export_for_phy({f'agree_{i + 1}': agree_sort}, recording_preprocessed, tic=tic)
        #
        # sorting_agreement = comp_multi.get_agreement_sorting(minimum_agreement_count=2)
        # print('Units in agreement between kilosort and herding_spikes:', sorting_agreement.get_unit_ids())
        # w_multi = sw.plot_multicomp_graph(comp_multi)
        # plt.show()


if __name__ == '__main__':
    main()
