import os
def save_data_csv(density_input, hvap_input, template_path, output_path, rho_denom="7.8", hvap_denom="0.3"):
    try:
        densities = []
        if density_input:
            items = density_input.strip().split(';')
            for item in items:
                vals = item.replace('(', '').replace(')', '').split(',')
                if len(vals) == 3:
                    densities.append([v.strip() for v in vals])
        hvaps = {}
        if hvap_input:
            items = hvap_input.strip().split(';')
            for item in items:
                vals = item.replace('(', '').replace(')', '').split(',')
                if len(vals) == 3:
                    hvaps[(vals[0].strip(), vals[1].strip())] = vals[2].strip()
        if not os.path.exists(template_path):
            return False, f"Template not found: {template_path}"
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        parts = template_content.split("# data")
        if len(parts) < 2:
            return False, "Invalid template format: '# data' section not found"
        header_section = parts[0] + "# data\n"
        data_line_template = parts[1].strip()
        header_section = header_section.replace("{rho_denom}", str(rho_denom)).replace("{hvap_denom}", str(hvap_denom))
        final_data_lines = []
        for d in densities:
            t_val, p_val, rho_val = d
            h_val = hvaps.get((t_val, p_val), "0.0")
            line = data_line_template.replace("{temp}", t_val) \
                                     .replace("{pressure}", p_val) \
                                     .replace("{rho}", rho_val) \
                                     .replace("{hvap}", h_val)
            final_data_lines.append(line)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header_section)
            f.write("\n".join(final_data_lines))
            f.write("\n")
        return True, "Success"
    except Exception as e:
        return False, str(e)
