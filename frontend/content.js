// === Create sidebar iframe ===
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

// === Extract Job Description ===
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

// === Added: Extract Company Name & Job Title ===
function extractAndSendJobInfo() {
  // ✅ Get job title
  const titleEl = document.querySelector(".job-details-jobs-unified-top-card__job-title h1 a");
  const jobTitle = titleEl ? titleEl.innerText.trim() : "";

  // ✅ Get company name
  const companyEl = document.querySelector(".job-details-jobs-unified-top-card__company-name a");
  const companyName = companyEl ? companyEl.innerText.trim() : "";

  iframe.contentWindow.postMessage({
    type: "JOB_INFO",
    companyName,
    jobTitle
  }, "*");

  console.log("✅ Job info sent:", { companyName, jobTitle });
}

// === Listen to LinkedIn page changes ===
const observer = new MutationObserver(() => {
  extractAndSendJobDescription();
  extractAndSendJobInfo();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

// === Trigger once on initial load (as backup) ===
setTimeout(() => {
  extractAndSendJobDescription();
  extractAndSendJobInfo();
}, 1000);

