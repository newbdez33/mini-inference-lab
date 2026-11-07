"use strict";

const status = document.getElementById("copy-status");

function codeLanguage(code) {
  return (code.className.match(/language-([\w-]+)/) || [])[1] || "text";
}

function updateCopyButton(button, code) {
  const label = codeLanguage(code) === "text" ? "复制问题" : "复制命令";
  button.querySelector(".copy-label").textContent = label;
  button.setAttribute("aria-label", label + "：" + code.textContent.split("\n")[0]);
}

function createCopyButton(getCode) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-button";
  const icon = document.createElement("span");
  icon.className = "copy-icon";
  icon.setAttribute("aria-hidden", "true");
  const label = document.createElement("span");
  label.className = "copy-label";
  button.append(icon, label);
  updateCopyButton(button, getCode());
  button.addEventListener("click", async () => {
    const code = getCode();
    const text = code.textContent.replace(/\n$/, "");
    try {
      await navigator.clipboard.writeText(text);
      if (getCode() === code) label.textContent = "已复制";
      status.textContent = codeLanguage(code) === "text" ? "已复制问题，请在 Prompt 后粘贴。" : "已复制命令，可以粘贴到终端。";
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(code);
      selection.removeAllRanges();
      selection.addRange(range);
      label.textContent = "已选中";
      status.textContent = "请使用系统复制快捷键复制选中的内容。";
    }
    setTimeout(() => updateCopyButton(button, getCode()), 2200);
  });
  return button;
}

function formatCommand(code) {
  const fragment = document.createDocumentFragment();
  for (const [index, line] of code.textContent.split("\n").entries()) {
    if (index) fragment.append("\n");
    if (!line) continue;
    const row = document.createElement("span");
    row.className = "command-line";
    // Render prompts with CSS so they stay out of copied commands.
    row.dataset.prompt = codeLanguage(code) === "powershell" ? "PS>" : "$";
    const match = line.match(/^(\S+)(.*)$/);
    if (match) {
      const command = document.createElement("span");
      command.className = "command-name";
      command.textContent = match[1];
      row.append(command, match[2]);
    } else {
      row.textContent = line;
    }
    fragment.append(row);
  }
  code.replaceChildren(fragment);
}

const platforms = [
  {id: "macos", label: "macOS"},
  {id: "windows", label: "Windows"},
  {id: "linux", label: "Linux"},
];
const devices = [
  {id: "cpu", label: "CPU"},
  {id: "cuda", label: "GPU · NVIDIA CUDA"},
];
let selectedPlatform = "macos";
let selectedDevice = "cpu";
try {
  const saved = localStorage.getItem("mini-inference-platform");
  if (platforms.some(platform => platform.id === saved)) selectedPlatform = saved;
  const savedDevice = localStorage.getItem("mini-inference-device");
  if (devices.some(device => device.id === savedDevice)) selectedDevice = savedDevice;
} catch {}

const platformGroups = [];
const environmentPanels = [...document.querySelectorAll(".tutorial [data-platforms], .tutorial [data-devices]")];
const platformSwitcher = document.querySelector(".platform-switcher");
const platformRadios = [...document.querySelectorAll(".platform-options [data-platform]")];
const deviceSwitcher = document.querySelector(".device-switcher");
const deviceRadios = [...document.querySelectorAll(".device-options [data-device]")];

function effectiveDevice() {
  return selectedPlatform === "macos" ? "cpu" : selectedDevice;
}

function matchesEnvironment(panel) {
  return (!panel.dataset.platforms || panel.dataset.platforms.split(" ").includes(selectedPlatform)) &&
    (!panel.dataset.devices || panel.dataset.devices.split(" ").includes(effectiveDevice()));
}

function updateEnvironment() {
  const platformLabel = platforms.find(item => item.id === selectedPlatform).label;
  const device = effectiveDevice();
  for (const panel of environmentPanels) {
    panel.hidden = !matchesEnvironment(panel);
  }
  for (const group of platformGroups) {
    const code = group.getCode();
    group.label.textContent = `${codeLanguage(code) === "powershell" ? "PowerShell" : "Shell"} · ${platformLabel}`;
    updateCopyButton(group.copyButton, code);
  }
  for (const radio of platformRadios) {
    const selected = radio.dataset.platform === selectedPlatform;
    radio.setAttribute("aria-checked", String(selected));
    radio.tabIndex = selected ? 0 : -1;
  }
  for (const radio of deviceRadios) {
    const selected = radio.dataset.device === device;
    radio.setAttribute("aria-checked", String(selected));
    radio.tabIndex = selected ? 0 : -1;
  }
  if (deviceSwitcher) deviceSwitcher.hidden = selectedPlatform === "macos";
  for (const label of document.querySelectorAll("[data-device-label]")) {
    label.textContent = devices.find(item => item.id === device).label;
  }
  try {
    localStorage.setItem("mini-inference-platform", selectedPlatform);
    localStorage.setItem("mini-inference-device", selectedDevice);
  } catch {}
}

function bindChoiceControls(buttons, select) {
  for (const [index, button] of buttons.entries()) {
    button.addEventListener("click", () => select(button));
    button.addEventListener("keydown", event => {
      let next;
      if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (index + 1) % buttons.length;
      else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (index + buttons.length - 1) % buttons.length;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = buttons.length - 1;
      else return;
      event.preventDefault();
      select(buttons[next]);
      buttons[next].focus();
    });
  }
}

for (const [index, group] of [...document.querySelectorAll(".platform-commands")].entries()) {
  const panels = [...group.querySelectorAll(":scope > [data-platforms]")];
  const toolbar = document.createElement("div");
  toolbar.className = "code-toolbar";
  const title = document.createElement("span");
  title.className = "terminal-title";
  const icon = document.createElement("span");
  icon.className = "terminal-icon";
  icon.textContent = ">_";
  icon.setAttribute("aria-hidden", "true");
  const label = document.createElement("span");
  label.id = `command-${index + 1}-label`;
  title.append(icon, label);
  group.setAttribute("role", "group");
  group.setAttribute("aria-labelledby", label.id);
  for (const panel of panels) {
    panel.firstElementChild.classList.add("platform-label");
    panel.querySelector("pre").tabIndex = 0;
    formatCommand(panel.querySelector("code"));
  }
  const getCode = () => panels.find(matchesEnvironment).querySelector("code");
  const copyButton = createCopyButton(getCode);
  toolbar.append(title, copyButton);
  group.prepend(toolbar);
  group.classList.add("code-block", "command-block", "is-enhanced");
  platformGroups.push({label, getCode, copyButton});
}
bindChoiceControls(platformRadios, button => {
  selectedPlatform = button.dataset.platform;
  updateEnvironment();
});
bindChoiceControls(deviceRadios, button => {
  selectedDevice = button.dataset.device;
  updateEnvironment();
});
updateEnvironment();
if (platformSwitcher) platformSwitcher.hidden = false;

for (const pre of document.querySelectorAll(".tutorial pre")) {
  if (pre.closest(".platform-commands")) continue;
  const code = pre.querySelector("code");
  const language = codeLanguage(code);
  const isFileTree = code.textContent.startsWith("mini-lab-01/\n");
  if (isFileTree) code.classList.add("file-tree");
  const wrapper = document.createElement("div");
  wrapper.className = "code-block";
  const toolbar = document.createElement("div");
  toolbar.className = "code-toolbar";
  const label = document.createElement("span");
  label.textContent = isFileTree ? "FILES" : ({sh: "TERMINAL", powershell: "POWERSHELL", text: "PROMPT"}[language] || language.toUpperCase());
  toolbar.append(label);
  if (!isFileTree) toolbar.append(createCopyButton(() => code));
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
}, {rootMargin: "-24px 0px -65% 0px", threshold: 0});
for (const heading of document.querySelectorAll(".tutorial h2[id]")) observer.observe(heading);
