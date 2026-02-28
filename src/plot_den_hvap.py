import pandas as pd
import matplotlib.pyplot as plt
import os
def plot_data(file_path, output_filename=None):
    try:
        df = pd.read_csv(file_path, sep='\s+', skiprows=[1])
        print("数据读取成功：")
        print(df)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        label_size = 14
        title_size = 14
        tick_size  = 14
        legend_size = 12
        ax1.plot(df['Iter'], df['Dens_Ref'], color='black', linestyle='--', label='Dens_Ref', marker='o')
        ax1.plot(df['Iter'], df['Dens_Calc'], color='red', linestyle='-', label='Dens_Calc', marker='s')
        ax1.set_xlabel('Iteration', fontsize=label_size)
        ax1.set_ylabel('Density', fontsize=label_size)
        ax1.set_title('Density: Ref vs Calc', fontsize=title_size)
        ax1.legend(fontsize=legend_size)
        ax1.tick_params(axis='both', labelsize=tick_size)
        ax2.plot(df['Iter'], df['Hvap_Ref'], color='black', linestyle='--', label='Hvap_Ref', marker='o')
        ax2.plot(df['Iter'], df['Hvap_Calc'], color='blue', linestyle='-', label='Hvap_Calc', marker='^')
        ax2.set_xlabel('Iteration', fontsize=label_size)
        ax2.set_ylabel('Hvap', fontsize=label_size)
        ax2.set_title('Hvap: Ref vs Calc', fontsize=title_size)
        ax2.legend(fontsize=legend_size)
        ax2.tick_params(axis='both', labelsize=tick_size)
        plt.tight_layout()
        if output_filename:
            save_path = output_filename
        else:
            save_path = 'density_hvap.png'
        plt.savefig(save_path, dpi=300)
        print(f"\n图表已保存为: {save_path}")
        plt.show()
    except FileNotFoundError:
        print(f"错误：找不到文件 '{file_path}'")
    except Exception as e:
        print(f"处理数据时出错: {e}")
if __name__ == "__main__":
    target_file = "density-hvap-0004.data"
    plot_data(target_file)
