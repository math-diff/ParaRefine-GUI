import pandas as pd
import matplotlib.pyplot as plt
import os
def plot_and_save_data(file_path):
    abs_file_path = os.path.abspath(file_path)
    output_image_path = os.path.splitext(abs_file_path)[0] + "_plot.png"
    try:
        df = pd.read_csv(abs_file_path, sep='\s+', skiprows=[1])
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df['Iter'], df['Total'], marker='o', color='blue', linewidth=2, label='Total')
        ax.plot(df['Iter'], df['Dens_Obj'], marker='s', linestyle='-', alpha=0.7, label='Dens_Obj')
        ax.plot(df['Iter'], df['Hvap_Obj'], marker='^', linestyle='-', alpha=0.7, label='Hvap_Obj')
        ax.set_title('Training Progress Analysis', fontsize=14)
        ax.set_xlabel('Iteration (Iter)', fontsize=12)
        ax.set_ylabel('Objective Value', fontsize=12)
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend()
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"图表已成功保存至: {output_image_path}")
        plt.show()
    except Exception as e:
        print(f"处理过程中出错: {e}")
target_file = "score-0004.data"
plot_and_save_data(target_file)
