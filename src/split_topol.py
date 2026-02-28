import os
def extract_system_section(input_file, output_file="topol.top"):
    target_marker = "[ system ]"
    if not os.path.exists(input_file):
        print(f"Error: no found '{input_file}'")
        return
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        content_to_keep = []
        content_to_cut = []
        found = False
        for line in lines:
            if target_marker in line:
                found = True
            if found:
                content_to_cut.append(line)
            else:
                content_to_keep.append(line)
        if not found:
            print(f"Warning: Marker '{target_marker}' not found. No changes made.")
            return
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(content_to_cut)
        print(f"已被提取的部分已写入: {output_file}")
        with open(input_file, 'w', encoding='utf-8') as f_in_rewrite:
            f_in_rewrite.writelines(content_to_keep)
        print(f"原文件已更新 (已移除 system 部分): {input_file}")
    except Exception as e:
        print(f"发生错误: {e}")
