import re


def basename(filepath):
    basename = re.search(r'[^\\/]+(?=[\\/]?$)', filepath)
    if basename:
        return basename.group(0)
