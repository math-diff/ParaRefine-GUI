import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
def plot_energy(input_path, save_path='dih_energy.png'):
    try:
        df = pd.read_csv(input_path, sep='\s+')
        if df.shape[1] < 1:
            raise ValueError("数据列数不足")
        if df.columns[0] == '#':
            correct_columns = df.columns[1:].tolist()
            df = df.iloc[:, :-1]
            df.columns = correct_columns
    except Exception as e:
        raise RuntimeError(f"读取文件失败: {e}")
    plt.figure(figsize=(10, 6))
    required_cols = ['Num', 'QMEnergy', 'MMEnergy', 'DeltaE(MM-QM)']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"输入文件中缺少必要的列: {col}")
    x = df['Num']
    y1 = df['QMEnergy']
    y2 = df['MMEnergy']
    y3 = df['DeltaE(MM-QM)']
    plt.plot(x, y1, label='QMEnergy', color='red', linewidth=1.5)
    plt.plot(x, y2, label='MMEnergy', color='blue', linewidth=1.5)
    plt.plot(x, y3, label='DeltaE(MM-QM)', color='green', linewidth=1.5)
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', integer=True))
    plt.title('Energy Analysis', fontsize=16, fontweight='bold')
    plt.xlabel('Num', fontsize=14)
    plt.ylabel('Energy', fontsize=14)
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.legend(fontsize=12)
    plt.grid(False)
    plt.tight_layout()
    try:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存为: {save_path}")
    except Exception as e:
        print(f"保存图片失败: {e}")
    plt.show()
if __name__ == "__main__":
    if os.path.exists('EnergyCompare.txt'):
        plot_energy('EnergyCompare.txt', 'dih_energy.png')
    else:
        print("当前目录下未找到 EnergyCompare.txt")
