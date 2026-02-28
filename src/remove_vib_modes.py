import os
def process_removal(input_path, output_path, remove_str):
    target_points = []
    target_ranges = []
    tolerance = 0.02
    if remove_str:
        parts = remove_str.split(';')
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if '-' in p and p.count('-') == 1:
                try:
                    start_str, end_str = p.split('-')
                    start_val = float(start_str)
                    end_val = float(end_str)
                    target_ranges.append((min(start_val, end_val), max(start_val, end_val)))
                    continue
                except ValueError:
                    pass
            try:
                target_points.append(float(p))
            except ValueError:
                print(f"Warning: Could not parse frequency condition '{p}'")
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"
    with open(input_path, 'r') as f:
        lines = f.readlines()
    output_lines = []
    skip_block = False
    removed_count = 0
    for line in lines:
        stripped = line.strip()
        parts = stripped.split()
        is_freq_line = False
        current_val = 0.0
        if len(parts) == 1:
            try:
                current_val = float(parts[0])
                is_freq_line = True
            except ValueError:
                pass
        if is_freq_line:
            match_found = False
            for t in target_points:
                if abs(current_val - t) < tolerance:
                    match_found = True
                    break
            if not match_found:
                for start, end in target_ranges:
                    if (start - tolerance) <= current_val <= (end + tolerance):
                        match_found = True
                        break
            if match_found:
                skip_block = True
                removed_count += 1
            else:
                skip_block = False
        if skip_block:
            continue
        else:
            output_lines.append(line)
    try:
        with open(output_path, 'w') as f:
            f.writelines(output_lines)
        return True, f"Successfully generated {os.path.basename(output_path)}.\nRemoved {removed_count} frequency block(s)."
    except Exception as e:
        return False, f"Failed to write output file: {str(e)}"
