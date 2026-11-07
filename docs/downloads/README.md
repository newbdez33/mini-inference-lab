# 跑通第一次模型推理

这是 Mini 的第一个模型推理实验：在自己的电脑上运行一个小模型，问它一个问题，再只换输入，看看回答怎么变。

**预计用时：10–15 分钟。** 包括阅读步骤和动手操作；首次安装 Python、安装依赖及下载模型的等待时间另计。

**本篇使用 Python，默认在 CPU 上运行；Windows 和 Linux 可选 NVIDIA GPU。** 首次运行要联网下载依赖和模型，等待时间取决于设备与网络。在页面顶部选择系统和运行设备，安装、检查和运行命令会一起切换。点击命令块右上角的“复制命令”，即可粘贴到终端。Windows 请使用 PowerShell，macOS 和 Linux 使用终端。

<div data-platforms="macos" markdown="1">

**macOS：** 本实验使用 CPU，无需选择运行设备。

</div>
<div data-platforms="windows linux" data-devices="cuda" markdown="1">

**GPU 模式：** 需要受 [PyTorch 2.15 支持](https://github.com/pytorch/pytorch/blob/v2.15.0/RELEASE.md#release-compatibility-matrix)的 NVIDIA 显卡，以及支持 CUDA 13.2 的驱动。不确定是否支持时，先选 CPU 完成实验。

</div>

<a id="download"></a>

## 01 · 下载并解压实验包

[下载 mini-lab-01.zip](https://github.com/newbdez33/mini-inference-lab/raw/refs/heads/main/packages/mini-lab-01.zip)

下载完成后，双击 ZIP 解压。包内已经有 `mini-lab-01` 文件夹，**不用自己新建目录，也不用自己写脚本或依赖清单**。

```text
mini-lab-01/
├── example_infer.py
└── requirements.txt
```

| 文件 | 你会用它做什么 |
| --- | --- |
| `example_infer.py` | 已写好的完整推理脚本，稍后直接运行。 |
| `requirements.txt` | 随实验包提供的依赖清单，用来安装指定版本的库。 |

**完成检查：** 打开解压后的文件夹，能看到上面两个文件。操作说明和示例回答直接看本页。

<a id="python"></a>

## 02 · 先确认 Python 能用

在页面顶部选好系统，再打开终端，运行：

<div class="platform-commands" markdown="1">
<div data-platforms="macos linux" markdown="1">

**macOS · Linux**

```sh
python --version
```

</div>
<div data-platforms="windows" markdown="1">

**Windows · PowerShell**

```powershell
python --version
```

</div>
</div>

> 建议在独立的 Python 虚拟环境（[venv](https://docs.python.org/zh-cn/3/library/venv.html)）中运行本实验，避免影响其他项目。

本实验需要 **Python 3.11 或更新版本**，命令统一写作 `python`。版本符合就可以继续，无需特地更换已有环境。这里是在检查电脑上已有的工具，还没有进入实验目录。

<details markdown="1">
<summary>找不到 Python，或版本太旧？</summary>

<div data-platforms="macos" markdown="1">

**macOS：** 已有 Homebrew 时，可以执行 `brew install python`。如果仍找不到 `python`，在当前终端执行 `export PATH="$(brew --prefix python)/libexec/bin:$PATH"`，让终端找到 Homebrew 提供的命令。没有 Homebrew 时，先按 [Homebrew 官方安装说明](https://docs.brew.sh/Installation)安装并完成 shell 配置。

</div>
<div data-platforms="windows" markdown="1">

**Windows：** 按 [Python 官方 Windows 说明](https://docs.python.org/3/using/windows.html)安装 Python，确认 `python` 已加入命令搜索路径，再重新打开 PowerShell。

</div>
<div data-platforms="linux" markdown="1">

**Linux：** 按 [Python 官方 Unix 说明](https://docs.python.org/3/using/unix.html)和发行版文档安装 Python 及 `python` 命令。Debian / Ubuntu 可通过 [python-is-python3](https://packages.debian.org/stable/python-is-python3) 软件包提供这个命令。

</div>

也可以使用自己熟悉的 Python 管理工具。**重新运行上面的版本检查，确认符合要求后再继续。**

</details>

<a id="directory"></a>

## 03 · 在实验目录打开终端

如果 ZIP 下载并解压在默认的“下载”目录，执行下面的命令。解压在其他位置时，把第一行的目录替换成实际路径。

<div class="platform-commands" markdown="1">
<div data-platforms="macos linux" markdown="1">

**macOS · Linux**

```sh
cd "$HOME/Downloads/mini-lab-01"
ls
```

</div>
<div data-platforms="windows" markdown="1">

**Windows · PowerShell**

```powershell
cd "$HOME\Downloads\mini-lab-01"
dir
```

</div>
</div>

**完成检查：** 两个文件名都能列出，没有文件或路径不存在的报错。后面所有命令都在这个终端、这个目录里执行。

<a id="environment"></a>

## 04 · 安装实验依赖

先在当前实验目录创建并激活虚拟环境：

<div class="platform-commands" markdown="1">
<div data-platforms="macos linux" markdown="1">

**macOS · Linux**

```sh
python -m venv .venv
source .venv/bin/activate
python -c "import sys; print(sys.executable)"
```

</div>
<div data-platforms="windows" markdown="1">

**Windows · PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
```

</div>
</div>

这会在当前目录创建 `.venv` 文件夹。**完成检查：** 最后一行打印的 Python 路径应位于当前实验目录的 `.venv` 中。确认后，再在同一个终端安装依赖。重新打开终端时，回到实验目录，再执行激活那一行即可。

安装实验包中列出的依赖。命令中的 `--require-virtualenv` 会在未使用虚拟环境时停止安装：

<div class="platform-commands" markdown="1">
<div data-platforms="macos" markdown="1">

**macOS**

```sh
python -m pip --require-virtualenv install -r requirements.txt
```

</div>
<div data-platforms="windows" data-devices="cpu" markdown="1">

**Windows · PowerShell · CPU**

```powershell
python -m pip --require-virtualenv install torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip --require-virtualenv install -r requirements.txt
```

先安装 CPU 版 PyTorch，再安装其余依赖。

</div>
<div data-platforms="linux" data-devices="cpu" markdown="1">

**Linux · CPU**

```sh
python -m pip --require-virtualenv install torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip --require-virtualenv install -r requirements.txt
```

先安装 CPU 版 PyTorch，再安装其余依赖。

</div>
<div data-platforms="windows" data-devices="cuda" markdown="1">

**Windows · PowerShell · NVIDIA GPU**

```powershell
nvidia-smi
python -m pip --require-virtualenv install torch==2.15.0+cu132 --index-url https://download.pytorch.org/whl/cu132
python -m pip --require-virtualenv install -r requirements.txt
```

先确认第一条命令能显示 NVIDIA 显卡和驱动信息，再安装 CUDA 版 PyTorch。更换 CPU／GPU 选项后，需要重新执行对应的安装命令。

</div>
<div data-platforms="linux" data-devices="cuda" markdown="1">

**Linux · NVIDIA GPU**

```sh
nvidia-smi
python -m pip --require-virtualenv install torch==2.15.0+cu132 --index-url https://download.pytorch.org/whl/cu132
python -m pip --require-virtualenv install -r requirements.txt
```

先确认第一条命令能显示 NVIDIA 显卡和驱动信息，再安装 CUDA 版 PyTorch。更换 CPU／GPU 选项后，需要重新执行对应的安装命令。

</div>
</div>

等安装结束、终端重新出现提示符后，再检查两个主要库：

<div class="platform-commands" markdown="1">
<div data-platforms="macos linux" data-devices="cpu" markdown="1">

**macOS · Linux**

```sh
python -c "import torch, transformers; print(torch.__version__); print(transformers.__version__)"
```

</div>
<div data-platforms="windows" data-devices="cpu" markdown="1">

**Windows · PowerShell**

```powershell
python -c "import torch, transformers; print(torch.__version__); print(transformers.__version__)"
```

</div>
<div data-platforms="windows" data-devices="cuda" markdown="1">

**Windows · PowerShell · NVIDIA GPU**

```powershell
python -c "import torch, transformers; print(torch.__version__); print(transformers.__version__)"
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print(torch.ones(1, device='cuda')); print(torch.cuda.get_device_name(0))"
```

</div>
<div data-platforms="linux" data-devices="cuda" markdown="1">

**Linux · NVIDIA GPU**

```sh
python -c "import torch, transformers; print(torch.__version__); print(transformers.__version__)"
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print(torch.ones(1, device='cuda')); print(torch.cuda.get_device_name(0))"
```

</div>
</div>

**完成检查：** 能打印 PyTorch 和 Transformers 的版本号，没有导入错误。实验包固定使用 PyTorch 2.15.0、Transformers 5.22.1 和 Jinja2 3.1.6。

<div data-platforms="windows linux" data-devices="cuda" markdown="1">

**GPU 检查：** 还要看到 `CUDA: True`、带 `device='cuda:0'` 的张量和显卡名称，且没有报错。只看到 `nvidia-smi` 成功还不够。检查失败时，先修复驱动或改选 CPU，并重新安装对应依赖。

</div>

`requirements.txt` 就在当前目录中，安装命令会读取它。它不会被自动下载，也不需要你另行创建。

<a id="first-run"></a>

## 05 · 第一个实验：问模型一个小问题

运行刚才下载的完整脚本：

<div class="platform-commands" markdown="1">
<div data-platforms="macos linux" data-devices="cpu" markdown="1">

**macOS · Linux · CPU**

```sh
python example_infer.py
```

</div>
<div data-platforms="windows" data-devices="cpu" markdown="1">

**Windows · PowerShell · CPU**

```powershell
python example_infer.py
```

</div>
<div data-platforms="windows" data-devices="cuda" markdown="1">

**Windows · PowerShell · NVIDIA GPU**

```powershell
python example_infer.py --device cuda
```

</div>
<div data-platforms="linux" data-devices="cuda" markdown="1">

**Linux · NVIDIA GPU**

```sh
python example_infer.py --device cuda
```

</div>
</div>

看到 `Prompt:` 后，输入下面这句话，再按回车：

```text
请用一句话解释什么是人工智能。
```

脚本会加载 `Qwen/Qwen2.5-0.5B-Instruct`。第一次需要从 Hugging Face 下载模型；后续复用缓存。看到 `Loading` 或下载进度时，先等待，不要重复启动脚本。

加载信息会显示本次使用的 `CPU` 或 `CUDA`。模型加载好后会出现 `Generating...`，然后是 `Answer:`。这是我们在 CPU 上实际运行得到的一次回答：

> 人工智能是一种模拟人类智能的理论与技术，能够使机器在执行任务时表现出与人类相似或超越人类的能力。它包括了机器学习、深度学习、自然语言处理等多个领域，并且正在逐渐渗透到我们的日常生活中。

这次模型写了两句话，没有完全遵循“一句话”的要求。这里保留原始回答，稍后再比较两次结果。

**完成检查：** 你的终端出现 `Answer:` 和一段非空文字，随后回到命令提示符。回答不必与这里逐字一致。

这个脚本每次只处理一个问题，然后退出。想再问一次，就再运行一次。

<a id="second-run"></a>

## 06 · 只换一个问题

仍然在同一个终端、同一个目录里，执行同一条命令：

<div class="platform-commands" markdown="1">
<div data-platforms="macos linux" data-devices="cpu" markdown="1">

**macOS · Linux · CPU**

```sh
python example_infer.py
```

</div>
<div data-platforms="windows" data-devices="cpu" markdown="1">

**Windows · PowerShell · CPU**

```powershell
python example_infer.py
```

</div>
<div data-platforms="windows" data-devices="cuda" markdown="1">

**Windows · PowerShell · NVIDIA GPU**

```powershell
python example_infer.py --device cuda
```

</div>
<div data-platforms="linux" data-devices="cuda" markdown="1">

**Linux · NVIDIA GPU**

```sh
python example_infer.py --device cuda
```

</div>
</div>

这次在 `Prompt:` 后输入：

```text
用一句话介绍猫。
```

模型、运行设备和生成设置都不改。我们在 CPU 上实际得到的回答是：

> 猫，以其优雅的外表、温顺的性格和多才多艺的生活方式，成为了许多人喜爱的宠物之一。

对照两次结果：内容有没有跟着问题改变？有没有遵循“一句话”的要求？接着可以换一个你自己感兴趣的问题。

**这次实验完成的标志：同一个模型，两个输入，两次实际回答。**

<a id="code"></a>

## 07 · 再看刚才运行的脚本

现在打开实验包里的 `example_infer.py`。你已经运行过它了，只需要沿着问题走一遍下面三步。

1. **加载。** `AutoTokenizer.from_pretrained` 读取分词器，`AutoModelForCausalLM.from_pretrained` 加载模型。
2. **整理输入。** `apply_chat_template` 把问题按模型的对话格式整理成输入。
3. **生成并还原文字。** `model.generate` 生成新的编号；脚本去掉输入部分，再用 `tokenizer.decode` 转回文字。

本集不修改这些代码。先记住这条顺序：**问题 → 模型输入 → 生成结果 → 文字回答。**

CPU 和 GPU 路径都使用 float32，关闭采样，最多生成 64 个新 token。脚本会把模型和输入放到所选设备，每次运行都会重新加载模型。这次验证的是流程，不比较性能，也不保证不同设备的输出逐字相同。

<a id="help"></a>

## 卡住时，从这里检查

| 看到的情况 | 下一步 |
| --- | --- |
| 找不到 `python` 命令 | 回到“先确认 Python 能用”，确认安装和命令搜索路径，再检查版本。 |
| `requirements.txt` 或脚本找不到 | 回到“在实验目录打开终端”，确认解压目录和文件名。不要新建空文件来绕过错误。 |
| `ModuleNotFoundError` | 回到“安装实验依赖”，确认顶部选对系统和运行设备，再用同一个 `python -m pip` 安装依赖。 |
| `Could not find an activated virtualenv` | 回到“安装实验依赖”，激活 `.venv` 并检查 Python 路径，再安装。 |
| `dependency conflicts`，出现本实验未使用的软件包 | 检查是否误装进原有环境。回到实验目录，使用独立的 `.venv`；原环境中已发生的版本变更需要单独处理。 |
| 安装失败，或版本检查失败 | 先确认 Python 版本符合上方要求，再检查网络和完整报错。 |
| 模型下载失败 | 检查能否访问模型页面，再运行同一条命令；已有缓存通常可以复用。 |
| 一直显示加载或下载进度 | 首次下载和推理可能需要等待；没有报错时先让当前进程完成。 |
| 内存不足 | 关闭其他占用内存的程序后重试。 |

<div data-platforms="windows linux" data-devices="cuda" markdown="1">

**GPU 相关错误：** `CUDA is not available` 时，检查 NVIDIA 驱动和 CUDA 版 PyTorch；出现 `no kernel image` 时，检查显卡是否在当前版本的支持范围内。出现 `CUDA out of memory` 时，先关闭其他占用显存的程序。也可以在顶部改选 CPU，重新执行对应的安装、检查和运行命令。

</div>

如果需要反馈问题，保留操作系统、Python 版本、执行的命令和完整报错；在 [仓库的 Issues](https://github.com/newbdez33/mini-inference-lab/issues) 中描述卡在哪一步。

<a id="other-systems"></a>
<a id="references"></a>

## 本次实验的依据

示例输出采集于 macOS、Apple Silicon、Python 3.12、CPU；本篇流程另用本机默认的 Python 3.14 验证通过。Windows 已用 Python 3.12、NVIDIA RTX 4090 和 CUDA 版 PyTorch 跑通两次提问，并验证切换到 CPU 版后的推理。Linux 和 Intel Mac 尚未在本次实验中实测。Python 最低版本要求来自固定依赖的发布说明：[PyTorch](https://pypi.org/project/torch/2.15.0/)、[Transformers](https://pypi.org/project/transformers/5.22.1/)。

Windows 的依赖版本、设备和回答见 [CPU／GPU 验证记录](https://github.com/newbdez33/mini-inference-lab/blob/main/episode-01/device-validation.json)。

模型版本固定为 `7ae557604adf67be50417f59c2c2f167def9a775`。两次完整输入、输出及环境信息保存在仓库的[实际运行记录](https://github.com/newbdez33/mini-inference-lab/blob/main/episode-01/terminal-recordings.json)中，无需下载或运行该文件。其中的进程耗时包含导入与加载，不是推理性能基准。

参考：[模型说明](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)、[Transformers 对话模板](https://huggingface.co/docs/transformers/main/en/chat_templating)、[PyTorch 安装说明](https://pytorch.org/get-started/locally/)、[PyTorch 2.15 兼容性说明](https://github.com/pytorch/pytorch/blob/v2.15.0/RELEASE.md#release-compatibility-matrix)。

下一次实验，再拆开看看一句话经过分词器后变成了什么。
