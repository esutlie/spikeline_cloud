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
    compare_sorters = True
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

    if compare_sorters:
        # comp_TDC_HS = sc.compare_two_sorters(sorting1=sorters['kilosort3'], sorting2=sorters['herdingspikes'])
        # match12 = comp_TDC_HS.hungarian_match_12
        # match21 = comp_TDC_HS.hungarian_match_21
        compare_path = os.path.join(os.path.dirname(os.getcwd()), 'comp_multi')
        compare_new = False
        if compare_new:
            comp_multi = sc.compare_multiple_sorters(sorting_list=list(sorters.values()), name_list=list(sorters.keys()),
                                                     verbose=True)
            comp_multi.save_to_folder(compare_path)
        else:
            comp_multi = sc.MultiSortingComparison.load_from_folder(compare_path)


        units = comp_multi.units
        units_df = pd.DataFrame.from_dict(units).transpose()
        units_df['sorters'] = [', '.join(list(units_df.loc[i].unit_ids.keys())) for i in range(len(units_df))]
        path = os.path.join('C:\\''github', 'spikeline', 'phy_folder_for_all_sort')
        cluster_info = pd.read_csv(os.path.join(path, 'cluster_info.tsv'), sep='\t')
        cluster_info['sorters'] = units_df['sorters']
        ax = sns.histplot(data=cluster_info, x='sorters', hue='group', multiple="dodge", shrink=.8)
        plt.xticks(rotation=45)
        plt.show()

        noise = cluster_info[cluster_info.group == 'noise']
        mua = cluster_info[cluster_info.group == 'mua']
        good = cluster_info[cluster_info.group == 'good']
        make_upset(noise, title='noise')
        make_upset(mua, title='mua')
        make_upset(good, title='good')
        # sw.plot_multicomp_graph(comp_multi)
        # plt.show()
        # sw.plot_multicomp_agreement_by_sorter(comp_multi)
        # plt.show()
        # sw.plot_multicomp_agreement(comp_multi)
        # plt.show()

        all_sort = comp_multi.get_agreement_sorting(minimum_agreement_count=1)
        # export_for_phy({f'all_sort1': all_sort}, recording_preprocessed)

        # for i in range(len(sorters)):
        #     agree_sort = comp_multi.get_agreement_sorting(minimum_agreement_count=i + 1)
        #     export_for_phy({f'agree_{i + 1}': agree_sort}, recording_preprocessed, tic=tic)
        #
        # sorting_agreement = comp_multi.get_agreement_sorting(minimum_agreement_count=2)
        # print('Units in agreement between kilosort and herding_spikes:', sorting_agreement.get_unit_ids())
        # w_multi = sw.plot_multicomp_graph(comp_multi)
        # plt.show()
        pass


if __name__ == '__main__':
    main()
