import os
def save_fb_lj_in(output_path, **params):
    template_path = os.path.join(os.getcwd(), "temp", "template.fb_lj")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    try:
        final_content = template_content.format(**params)
    except KeyError as e:
        raise KeyError(f"Missing parameter for template placeholder: {str(e)}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
