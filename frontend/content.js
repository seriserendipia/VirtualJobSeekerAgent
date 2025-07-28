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

// === 新增：提取职位发布者 & 公司信息 ===
function extractAndSendRecipients() {
  // 🔵 Job poster（大部分职位没有，保留空值）
  let jobPosterName = "";
  let jobPosterTitle = "";

  // 🔵 公司信息
  let companyName = "";
  let companyLink = "";

  // ✅ 新的更精准选择器（定位到公司名称链接）
  const companyEl = document.querySelector(".artdeco-entity-lockup__title a");

  if (companyEl) {
    companyName = companyEl.innerText.trim();

    // LinkedIn 给的链接是相对路径，需要加前缀
    const rawLink = companyEl.getAttribute("href");
    if (rawLink.startsWith("/")) {
      // LinkedIn 默认链接带 /life/，点进去又回到职位页，我们去掉 /life/
      let cleanLink = rawLink.replace(/\/life\/?$/, "");
      companyLink = `https://www.linkedin.com${cleanLink}`;
    } else {
      companyLink = rawLink;
    }
  }

  // ✅ 发送给 sidebar
  iframe.contentWindow.postMessage({
    type: "RECIPIENT_INFO",
    data: {
      jobPosterName,
      jobPosterTitle,
      companyName,
      companyLink
    }
  }, "*");

  console.log("✅ Recipient info sent:", { jobPosterName, jobPosterTitle, companyName, companyLink });
}


// === 使用 MutationObserver 检测页面内容变化 ===
const observer = new MutationObserver(() => {
  extractAndSendJobDescription();
  extractAndSendRecipients();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

// === 初始加载后稍等 1 秒也触发一次（保险） ===
setTimeout(() => {
  extractAndSendJobDescription();
  extractAndSendRecipients();
}, 1000);

