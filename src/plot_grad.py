# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import os
def plot_gradient(input_path):
    if not os.path.exists(input_path):
        print(f"错误: 找不到输入文件 {input_path}")
        return
    output_image_path = os.path.splitext(input_path)[0] + ".png"
    try:
        df = pd.read_csv(input_path, sep=r'\s{2,}', engine='python')
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    df.columns = [c.strip() for c in df.columns]
    target_col = None
    for col in df.columns:
        if 'Value' in col:
            target_col = col
            break
    if target_col:
        df = df.rename(columns={target_col: 'Grad_Val'})
    else:
        print(f"错误: 找不到数值列。")
        return
    df['Grad_Val'] = pd.to_numeric(df['Grad_Val'], errors='coerce')
    df = df.dropna(subset=['Grad_Val', 'Parameter Label'])
    df = df.iloc[::-1]
    num_rows = len(df)
    fig_height = max(8, num_rows * 0.3)
    plt.figure(figsize=(12, fig_height))
    colors = ['skyblue' if x >= 0 else 'salmon' for x in df['Grad_Val']]
    bars = plt.barh(df['Parameter Label'], df['Grad_Val'], color=colors, edgecolor='black', alpha=0.8)
    plt.axvline(0, color='black', linewidth=1)
    x_min, x_max = df['Grad_Val'].min(), df['Grad_Val'].max()
    x_range = x_max - x_min
    padding = (x_range * 0.01) if x_range != 0 else 0.1
    for bar in bars:
        width = bar.get_width()
        label_x_pos = width + padding if width >= 0 else width - padding
        ha = 'left' if width >= 0 else 'right'
        plt.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2e}',
                 va='center', ha=ha, fontsize=13)
    plt.xlabel('Gradient Value', fontsize=14)
    plt.ylabel('Parameter Label', fontsize=14)
    plt.title(f'Gradient Plot: {os.path.basename(input_path)}', fontsize=14, pad=15)
    plt.grid(axis='x', linestyle=':', alpha=0.6)
    plt.tick_params(axis='y', labelsize=12)
    plt.margins(x=0.2)
    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存至: {output_image_path}")
    plt.show()
