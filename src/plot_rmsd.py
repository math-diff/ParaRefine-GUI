import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import os
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 14,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14,
    'figure.titlesize': 16
})
def plot_molecular_data(input_filename, output_filename='bond_angle_rmsd.png'):
    iters = []
    bonds = []
    angles = []
    dihedrals = []
    impropers = []
    if not os.path.exists(input_filename):
        print(f"错误: 找不到文件 {input_filename}")
        return
    with open(input_filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('Iter') or line.startswith('---'):
                continue
            parts = line.split()
            if len(parts) >= 5:
                try:
                    iters.append(int(parts[0]))
                    bonds.append(float(parts[1]))
                    angles.append(float(parts[2]))
                    dihedrals.append(float(parts[3]))
                    impropers.append(float(parts[4]))
                except ValueError:
                    continue
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    data_map = [
        (bonds, 'Bonds', 'blue', axs[0, 0]),
        (angles, 'Angles', 'green', axs[0, 1]),
        (dihedrals, 'Dihedrals', 'red', axs[1, 0]),
        (impropers, 'Impropers', 'purple', axs[1, 1])
    ]
    for data, title, color, ax in data_map:
        ax.plot(iters, data, color=color, linewidth=1.5, marker='o', markersize=4)
        ax.set_title(title)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('RMSD')
        ax.grid(False)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.tick_params(direction='in')
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    print(f"图像已保存至: {output_filename}")
    plt.show()
if __name__ == "__main__":
    input_file = 'rmsd-history.data'
