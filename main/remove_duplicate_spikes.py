import os
import matplotlib.pyplot as plt
from open_phy import open_phy
from process_functions import *
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw
import pandas as pd
import seaborn as sns


def gt_phy_remove_dup_spikes(path):
    gt_sorter = se.read_phy(path, exclude_cluster_groups=['noise', 'mua'])
    gt_sorter = remove_dup(gt_sorter)
    save_path = os.path.join(os.path.dirname(os.getcwd()), 'gt_sorter')
    gt_sorter.save_to_folder('gt_sorter', save_path)


def remove_dup(sorter):
    frame_rate = 30000
    dup_cutoff = .2  # ms
    segment = sorter._sorting_segments[0]
    ind_to_remove = []
    for u in sorter.unit_ids:
        spike_ind = np.where(segment._all_clusters == u)[0]
        spike_times = segment._all_spikes[spike_ind]
        dup_ind = np.where(np.squeeze(spike_times[1:] - spike_times[:-1]) < dup_cutoff / 1000 * frame_rate)[0]
        if len(dup_ind):
            ind_to_remove += spike_ind[dup_ind].tolist()
    sorter._sorting_segments[0]._all_clusters = np.delete(segment._all_clusters, ind_to_remove)
    sorter._sorting_segments[0]._all_spikes = np.delete(segment._all_spikes, ind_to_remove)
    return sorter


def load_gt_save():  #example code
    path = os.path.join('C:\\', 'github', 'spikeline', 'gt_sorter')  # ES029_2022-09-14_bot72_0_g0
    gt_sorter = se.PhySortingExtractor.load_from_folder(path)
    return gt_sorter


if __name__ == '__main__':
    gt_path = os.path.join('C:\\', 'github', 'spikeline', 'phy_folder_for_ground_truth')  # ES029_2022-09-14_bot72_0_g0
    gt_phy_remove_dup_spikes(gt_path)
