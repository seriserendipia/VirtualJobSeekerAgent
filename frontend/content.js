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

// === 提取 Job Description ===
function extractAndSendJobDescription() {
  let jdElement = document.querySelector("#job-details") || document.querySelector(".jobs-box__html-content");

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

// === 新增：提取公司名 & 岗位名 ===
function extractAndSendJobInfo() {
  // ✅ 获取职位名称
  const titleEl = document.querySelector(".job-details-jobs-unified-top-card__job-title h1 a");
  const jobTitle = titleEl ? titleEl.innerText.trim() : "";

  // ✅ 获取公司名称
  const companyEl = document.querySelector(".job-details-jobs-unified-top-card__company-name a");
  const companyName = companyEl ? companyEl.innerText.trim() : "";

  iframe.contentWindow.postMessage({
    type: "JOB_INFO",
    companyName,
    jobTitle
  }, "*");

  console.log("✅ Job info sent:", { companyName, jobTitle });
}

// === 监听 LinkedIn 页面变化 ===
const observer = new MutationObserver(() => {
  extractAndSendJobDescription();
  extractAndSendJobInfo();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

// === 初始加载时触发一次（保险） ===
setTimeout(() => {
  extractAndSendJobDescription();
  extractAndSendJobInfo();
}, 1000);

