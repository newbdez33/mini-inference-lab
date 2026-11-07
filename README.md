# Mini 的模型推理工程师之路

一次一个小实验。这里放观众使用的图文教程、运行代码和实验包。

**[打开课程目录 →](https://newbdez33.github.io/mini-inference-lab/)**

| 实验 | 这次做什么 | 预计用时 | 下载 |
| --- | --- | --- | --- |
| [01 · 跑通第一次模型推理](https://newbdez33.github.io/mini-inference-lab/1/) | 在 CPU 上运行一个小模型，再换一个问题。 | 10–15 分钟 | [mini-lab-01.zip](https://github.com/newbdez33/mini-inference-lab/raw/refs/heads/main/packages/mini-lab-01.zip) |

预计用时包括阅读和动手操作，首次安装与下载的等待时间另计。

实验包解压后自带 `mini-lab-01` 文件夹，只包含运行脚本和依赖清单。操作说明与示例回答见网页教程，无需自己新建目录或编写 `requirements.txt`。

教程提供 macOS、Windows 和 Linux 的命令，可以在页面顶部或命令块中切换平台；验证范围在文末说明。

## 更新教程

根路径是课程目录，第一课位于 `/1/`；旧 `/ep1/` 链接自动跳转。`episode-01/README.md` 是第一课正文的唯一来源；目录模板为 `scripts/catalog.html`，课程模板为 `scripts/lesson.html`。两页共用 `docs/assets/site.css` 和深浅主题设置。修改后，在仓库根目录构建页面和实验包：

```sh
uv run --with Markdown==3.11.3 scripts/build_site.py
python3 -m unittest discover -s episode-01 -p 'test_*.py'
```

GitHub Pages 发布 `main` 分支的 `docs/`。静态页面已构建，无需观众安装网页工具。视频制作内容在单独的私有仓库维护。
