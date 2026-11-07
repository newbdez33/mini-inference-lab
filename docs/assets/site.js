"use strict";

const status = document.getElementById("copy-status");
for (const pre of document.querySelectorAll(".tutorial pre")) {
  const code = pre.querySelector("code");
  const text = code.textContent.replace(/\n$/, "");
  const language = (code.className.match(/language-([\w-]+)/) || [])[1] || "text";
  const isFileTree = text.startsWith("mini-lab-01/\n");
  const copyLabel = language === "text" ? "复制问题" : "复制命令";
  const wrapper = document.createElement("div");
  wrapper.className = "code-block";
  const toolbar = document.createElement("div");
  toolbar.className = "code-toolbar";
  const label = document.createElement("span");
  label.textContent = isFileTree ? "FILES" : ({sh: "TERMINAL", powershell: "POWERSHELL", text: "PROMPT"}[language] || language.toUpperCase());
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-button";
  button.textContent = copyLabel;
  button.setAttribute("aria-label", copyLabel + "：" + text.split("\n")[0]);
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "已复制";
      status.textContent = language === "text" ? "已复制问题，请在 Prompt 后粘贴。" : "已复制命令，可以粘贴到终端。";
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(code);
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = "已选中";
      status.textContent = "请使用系统复制快捷键复制选中的内容。";
    }
    setTimeout(() => { button.textContent = copyLabel; }, 2200);
  });
  toolbar.append(label);
  if (!isFileTree) toolbar.append(button);
  pre.before(wrapper);
  wrapper.append(toolbar, pre);
  pre.tabIndex = 0;
}

const links = [...document.querySelectorAll(".toc a")];
const observer = new IntersectionObserver(entries => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    for (const link of links) {
      if (link.hash === "#" + entry.target.id) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    }
  }
}, {rootMargin: "-100px 0px -65% 0px", threshold: 0});
for (const heading of document.querySelectorAll(".tutorial h2[id]")) observer.observe(heading);
