# Mini 的模型推理工程师之路

一次一个小实验。这里放观众使用的图文教程、运行代码和实验包。

**[打开图文教程 →](https://newbdez33.github.io/mini-inference-lab/)**

| 实验 | 这次做什么 | 下载 |
| --- | --- | --- |
| [01 · 让模型介绍自己](episode-01/README.md) | 在 CPU 上运行一个小模型，再换一个问题。 | [mini-lab-01.zip](https://github.com/newbdez33/mini-inference-lab/raw/refs/heads/main/packages/mini-lab-01.zip) |

实验包解压后自带 `mini-lab-01` 文件夹，包含完整脚本、依赖清单、操作说明和实际运行记录。无需自己新建目录或编写 `requirements.txt`。

目前主教程使用 macOS、Apple Silicon、Python 3.12 和 CPU。Windows 与 Linux 的命令放在教程末尾，并标明验证范围。

## 更新教程

`episode-01/README.md` 是教程正文的唯一来源。修改后，在仓库根目录构建页面和实验包：

```sh
uv run --with Markdown==3.11.3 scripts/build_site.py
python3 -m unittest discover -s episode-01 -p 'test_*.py'
```

GitHub Pages 发布 `main` 分支的 `docs/`。静态页面已构建，无需观众安装网页工具。视频制作内容在单独的私有仓库维护。
