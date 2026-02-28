import os
def generate_fb_dih(output_path, **kwargs):
    template_path = os.path.join("temp", "template.fb_dih")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        formatted_content = content.format(**kwargs)
    except KeyError as e:
        raise KeyError(f"Missing placeholder value in template: {e}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
