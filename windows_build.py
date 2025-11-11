import os
import re
import python_minifier
from pathlib import Path

# 定义文件路径
main_file = Path("src/pygone.py")
board_file = Path("src/board.py")
search_file = Path("src/search.py")
output_file = Path("src/pygone_combined.py")

# 读取所有文件（明确指定UTF-8编码）
main_code = main_file.read_text(encoding='utf-8')
board_code = board_file.read_text(encoding='utf-8')
search_code = search_file.read_text(encoding='utf-8')

# 替换导入语句
main_code = re.sub(r'from search import Search', search_code, main_code)
main_code = re.sub(r'from board import Board', board_code, main_code)

# 最小化代码
minified = python_minifier.minify(
    main_code,
    rename_locals=False,
    rename_globals=False,
    combine_imports=True,
    hoist_literals=False
)

# 写入合并后的文件（明确指定UTF-8编码）
with open(output_file, "w", encoding='utf-8') as f:
    f.write(minified)

print(f"已生成合并后的文件: {output_file}")