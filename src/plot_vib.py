# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
def plot_difference_bar(file_path, output_image_path):
    try:
        df = pd.read_csv(file_path, sep='\s+', skiprows=[1])
        df.columns = [c.strip() for c in df.columns]
        if 'Mode' not in df.columns or 'Difference' not in df.columns:
            print("错误：文件中必须包含 'Mode' 和 'Difference' 列")
            return
        plt.figure(figsize=(12, 6))
        plt.bar(df['Mode'], df['Difference'], color='skyblue', edgecolor='navy', alpha=0.8)
        plt.xlabel('Mode', fontsize=14)
        plt.ylabel('Difference', fontsize=14)
        plt.tick_params(axis='y', labelsize=12)
        plt.grid(False)
        plt.axhline(0, color='black', linewidth=0.8)
        plt.xticks(df['Mode'], rotation=60, fontsize=12)
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=300)
        plt.show()
        print(f"处理成功！图片已保存为: {output_image_path}")
    except Exception as e:
        print(f"发生错误: {e}")
