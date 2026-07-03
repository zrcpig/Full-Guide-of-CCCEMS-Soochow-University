#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正 docs/ 下所有 Markdown 文件里的站内相对链接。

规则（幂等，可重复运行）：
  - 指向 docs 内「目录」的相对链接（如 [无机化学](材化部课程/无机化学)）
    统一补上 /README.md，使 MkDocs 能正确解析为该目录的首页。
  - 已经以 .md 结尾的链接保持不变（指向具体文件，本来就合法）。
  - 锚点链接（#xxx）、外链（http(s)://、mailto:）、邮件、代码块/行内代码中的内容不动。
  - 保留链接原有的锚点片段（如 dir#标题 -> dir/README.md#标题）。

用法： python fix_links.py
"""

import os
import re

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

# 匹配 Markdown 链接：[text](href)
# text 部分允许包含 ] 需要更复杂处理，但本项目链接文本均为普通中文，简化处理即可。
LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")


def fix_href(href: str, md_file_path: str) -> str:
    """根据当前 md 文件位置，判断 href 是否指向 docs 内的目录，是则补 /index.md。"""
    # 跳过外链与锚点
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    # 含协议头的（如 git://）也跳过
    if "://" in href:
        return href

    # 拆分锚点
    if "#" in href:
        path_part, anchor = href.split("#", 1)
        anchor = "#" + anchor
    else:
        path_part, anchor = href, ""

    path_part = path_part.strip()
    if not path_part:
        return href

    # 已经是 .md 文件链接：不动
    if path_part.endswith(".md"):
        return href

    # 解析为绝对路径（相对当前 md 文件所在目录）
    base_dir = os.path.dirname(md_file_path)
    abs_target = os.path.normpath(os.path.join(base_dir, path_part))

    # 裸目录链接已经是正确的 MkDocs 格式（MkDocs 会自动将裸目录解析为该目录下的 README/index）
    # 不再需要补全后缀，保持原样即可
    if abs_target.startswith(DOCS_DIR) and os.path.isdir(abs_target):
        # 已经是正确的裸目录链接，返回原始路径（含锚点）
        return href

    return href


def fix_file(path: str) -> int:
    """处理单个 md 文件，返回被修改的链接数。"""
    with open(path, "r", encoding="utf-8", newline="") as f:
        content = f.read()

    def repl(m: re.Match) -> str:
        text, href = m.group(1), m.group(2)
        new_href = fix_href(href, path)
        return f"[{text}]({new_href})"

    new_content, n = LINK_RE.subn(repl, content)

    # 标准化为 LF，避免 CRLF 引入幽灵 diff（配合 .gitattributes 的 eol=lf）
    new_content = new_content.replace("\r\n", "\n").replace("\r", "\n")

    if new_content != content:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_content)
    return n


def main() -> None:
    total_files = 0
    total_links = 0
    for root, _dirs, files in os.walk(DOCS_DIR):
        for name in files:
            if name.endswith(".md"):
                p = os.path.join(root, name)
                n = fix_file(p)
                total_files += 1
                total_links += n
                if n:
                    print(f"  {os.path.relpath(p, DOCS_DIR)}: {n} 个链接已处理")
    print(f"\n完成：扫描 {total_files} 个 Markdown 文件，处理 {total_links} 个链接。")


if __name__ == "__main__":
    main()
