import pandas as pd
import matplotlib.pyplot as plt
import os
def plot_and_save(filename):
    try:
        df = pd.read_csv(filename, sep='\s+', skiprows=[1])
    except Exception as e:
        print(f"读取文件出错: {e}")
        return
    mapping = {
        'Iter': 'Iteration',
        '|grad|': 'Gradient',
        '|gradient|': 'Gradient',
        'Grad': 'Gradient',
        'Reg': 'Regularization',
        'LiqLiq': 'Target'
    }
    df.rename(columns=mapping, inplace=True)
    if 'Target' not in df.columns:
        if 'ligand_optgeo' in df.columns and 'ligand_vib' in df.columns:
            df['Target'] = df['ligand_optgeo'] + df['ligand_vib']
        elif 'ligand_optgeo' in df.columns:
            df['Target'] = df['ligand_optgeo']
    plot_cols = ['Target', 'Regularization', 'Total', 'Gradient']
    if 'Iteration' not in df.columns:
        print(f"错误：在文件 {filename} 中未找到迭代列 (Iter 或 Iteration)。")
        return
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes_flat = axes.flatten()
    styles = {
        'Target': {'color': 'blue', 'marker': 'o'},
        'Regularization': {'color': 'green', 'marker': 'o'},
        'Total': {'color': 'red', 'marker': 'o'},
        'Gradient': {'color': 'purple', 'marker': 'o'}
    }
    for i, col_name in enumerate(plot_cols):
        ax = axes_flat[i]
        if col_name in df.columns:
            style = styles.get(col_name, {'color': 'black', 'marker': 'o'})
            ax.plot(df['Iteration'], df[col_name],
                    marker=style['marker'],
                    markersize=6,
                    markerfacecolor=style['color'],
                    markeredgecolor='white',
                    markeredgewidth=0.5,
                    color=style['color'],
                    linewidth=1.5,
                    label=col_name)
            ax.set_title(col_name, fontsize=16, fontweight='bold')
            ax.set_xlabel('Iteration', fontsize=14)
            ax.set_ylabel('Value', fontsize=14)
            ax.grid(False)
            ax.tick_params(axis='both', which='major', labelsize=14)
            if len(df['Iteration']) <= 20:
                ax.set_xticks(df['Iteration'].astype(int))
        else:
            ax.text(0.5, 0.5, f'{col_name} Not Found',
                    ha='center', va='center', color='gray', fontsize=12)
            ax.set_title(col_name, fontsize=16, fontweight='bold')
            ax.grid(False)
    plt.suptitle(f'Optimization Progress: {filename}', fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    base_name = os.path.splitext(filename)[0]
    output_name = f'{base_name}.png'
    plt.savefig(output_name, dpi=300)
    print(f"成功处理文件 {filename}，图表已保存为: {output_name}")
    plt.show()
if __name__ == "__main__":
    target_file = 'score-0004.data'
    if os.path.exists(target_file):
        plot_and_save(target_file)
    else:
        print(f"未找到文件: {target_file}，请检查文件名。")
