import os
def generate_fb_vib(output_path, **kwargs):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "temp", "template.fb_vib")
    if not os.path.exists(template_file):
        raise FileNotFoundError(f"找不到模版文件: {template_file}")
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()
    try:
        formatted_content = template_content.format(**kwargs)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        print(f"成功生成文件: {output_path}")
    except KeyError as e:
        print(f"错误：模版中需要的参数缺失 -> {e}")
    except Exception as e:
        print(f"发生错误: {e}")
