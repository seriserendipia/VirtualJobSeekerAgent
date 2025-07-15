// === 创建 sidebar iframe ===
const iframe = document.createElement("iframe");
iframe.src = chrome.runtime.getURL("sidebar.html");
iframe.style.position = "fixed";
iframe.style.top = "80px";
iframe.style.right = "0";
iframe.style.width = "350px";
iframe.style.height = "85vh";
iframe.style.border = "none";
iframe.style.zIndex = "9999";
iframe.style.boxShadow = "0 0 10px rgba(0,0,0,0.3)";
document.body.appendChild(iframe);

// === 监听 LinkedIn 页面变化并提取 JD ===
function extractAndSendJobDescription() {
  let jdElement = document.querySelector("#job-details");

  if (!jdElement) {
    jdElement = document.querySelector(".jobs-box__html-content");
  }

  if (jdElement) {
    const jobDescription = jdElement.innerText.trim();
    if (jobDescription.length > 30) {
      iframe.contentWindow.postMessage({
        type: "JOB_DESCRIPTION",
        data: jobDescription
      }, "*");
      console.log("✅ JD sent to sidebar");
    }
  }
}

// === 使用 MutationObserver 检测页面内容变化 ===
const observer = new MutationObserver(() => {
  extractAndSendJobDescription();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

// 初始加载后稍等 1 秒也触发一次（保险）
setTimeout(extractAndSendJobDescription, 1000);
