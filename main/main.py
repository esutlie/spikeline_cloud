"""
Neuropixels preprocessing and spike sorting
"""
import os
from open_phy import open_phy
from process_functions import *

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
    run_phy = True

    recording_folder = os.path.join('D:\\', 'Test', 'ES029')
    recording_name = 'ES029_2022-09-14_bot72_0_g0'
    recording_save = os.path.join('C:\\', 'github', 'spikeline', 'recording_save')
    if load_new:
        recording_save = reset_folder(recording_save)
    # else:
    #     recording_save = recording_save + '0'
    tic = ticker()

    # Load or generate the preprocessed data

    recording_preprocessed = get_recording(recording_folder, recording_name, recording_save, load_new=load_new)
    tic = ticker(tic, text='loading recording')

    # Load or generate the sorter output
    # sorter_list = ['combinato', 'hdsort', 'herdingspikes', 'ironclust', 'kilosort3', 'kilosort2_5',
    #                'mountainsort4', 'spykingcircus', 'tridesclous', 'waveclus']
    # sorter_list = ['mountainsort4']
    sorter_list = ['kilosort3', 'kilosort2_5', 'ironclust', 'herdingspikes']
    sorters = run_spike_sorters(recording_preprocessed, sorter_list, run_new=sort_new)
    tic = ticker(tic, text='sorting')

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

    # comp_multi = sc.compare_multiple_sorters(sorting_list=[sorting_ks, sorting_hs], name_list=['ks', 'hs'])
    # sorting_agreement = comp_multi.get_agreement_sorting(minimum_agreement_count=2)
    # print('Units in agreement between kilosort and herding_spikes:', sorting_agreement.get_unit_ids())
    # w_multi = sw.plot_multicomp_graph(comp_multi)
    # plt.show()


if __name__ == '__main__':
    main()
