import spikeinterface.extractors as se
import os


def save_gt(phy_path, save_path):
    current_dir = os.path.dirname(os.getcwd())

    if phy_path[0] not in ['C', 'D']:
        phy_path = os.path.join(current_dir, phy_path)

    if save_path[0] not in ['C', 'D']:
        save_path = os.path.join(current_dir, save_path)

    gt_sorter = se.read_phy(phy_path, exclude_cluster_groups=['noise', 'mua'])
    gt_sorter.save(folder=save_path)


if __name__ == '__main__':
    save_gt('phy_folder_for_all_sort2', 'ground_truth')
