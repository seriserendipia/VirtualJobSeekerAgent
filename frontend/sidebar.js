// ============================
// Google授权类
// ============================
class GoogleAuth {
    async getAccessToken() {
        return new Promise((resolve, reject) => {
            if (!chrome || !chrome.identity) {
                reject(new Error("Chrome identity API not available"));
                return;
            }

            chrome.identity.getAuthToken({ interactive: true }, (token) => {
                if (chrome.runtime.lastError) {
                    if (chrome.runtime.lastError.message.includes('context invalidated')) {
                        reject(new Error("扩展上下文已失效，请重新加载扩展程序"));
                    } else {
                        reject(chrome.runtime.lastError);
                    }
                    return;
                }
                resolve(token);
            });
        });
    }
}

// ============================
// 全局变量
// ============================
window.googleAuth = new GoogleAuth();

let currentJobDescription = "";
let resumeContent = "";
let chatHistory = [];

window.generatedEmailData = {
  subject: "Sample Mail:Follow-up on Job Application",
  body: "Dear Hiring Manager,\n\nI am excited to apply for the position and believe my skills are a great match.\n\nBest regards,\n[Your Name]"
};

// ============================
// 简历上传处理
// ============================
document.getElementById("resume-upload").addEventListener("change", function (event) {
  const file = event.target.files[0];
  const statusEl = document.getElementById("resume-status");

  if (!file) {
    statusEl.innerText = "📎 No resume uploaded";
    return;
  }

  const fileType = file.type;

  if (fileType === "application/pdf") {
    resumeContent = "[Resume content from PDF file goes here]";
    localStorage.setItem("resumeText", resumeContent);
    statusEl.innerText = `📄 Uploaded PDF: ${file.name}`;
  } else if (fileType === "text/plain") {
    const reader = new FileReader();
    reader.onload = function (e) {
      resumeContent = e.target.result;
      localStorage.setItem("resumeText", resumeContent);
      statusEl.innerText = `📄 Uploaded TXT: ${file.name}`;
    };
    reader.onerror = function () {
      statusEl.innerText = "❌ Failed to read txt file";
    };
    reader.readAsText(file);
  } else {
    statusEl.innerText = "❌ Unsupported file type. Only PDF or TXT allowed.";
  }
});

// ============================
// 页面加载处理
// ============================
window.addEventListener("DOMContentLoaded", () => {
  const savedResume = localStorage.getItem("resumeText");
  const statusEl = document.getElementById("resume-status");
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");

  if (savedResume) {
    resumeContent = savedResume;
    if (statusEl) {
      statusEl.innerText = "📄 Resume restored from last session.";
    }
    console.log("✅ Resume restored from localStorage");
  }

  if (responseBox && window.generatedEmailData) {
    responseBox.innerText = `📧 Generated Email\n\nSubject: ${window.generatedEmailData.subject}\n\n${window.generatedEmailData.body}`;
    if (sendEmailBtn) {
      sendEmailBtn.style.display = 'inline-block';
    }
  }
});

// ============================
// 接收 Job Description & Job Info
// ============================
window.addEventListener("message", (event) => {
  if (event.data.type === "JOB_DESCRIPTION") {
    currentJobDescription = event.data.data;
    const jdBox = document.getElementById("jd-preview");
    if (jdBox) jdBox.innerText = currentJobDescription.slice(0, 1000) + "...";
  }

  if (event.data.type === "JOB_INFO") {
    console.log("📥 Got job info:", event.data);
    document.getElementById("company-name").value = event.data.companyName || "N/A";
    document.getElementById("job-title").value = event.data.jobTitle || "N/A";
  }
});

// ============================
// 聊天功能
// ============================
function addMessageToChat(content, sender = "ai") {
  const chatBox = document.getElementById("chat-box");
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`;
  bubble.innerText = content;
  chatBox.appendChild(bubble);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function addMessage(content, sender) {
  chatHistory.push({ sender, content });
  addMessageToChat(content, sender);
}

document.getElementById("send-chat-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input");
  const text = userInput.value.trim();
  if (!text) return;

  if (!window.generatedEmailData || !window.generatedEmailData.subject || !window.generatedEmailData.body) {
    addMessageToChat("❌ Please generate an email first before making modifications.", "ai");
    return;
  }

  addMessageToChat(text, "user");
  userInput.value = "";
  addMessageToChat("Modifying email...", "ai");

  try {
    const payload = {
      job_description: currentJobDescription,
      resume: resumeContent,
      current_subject: window.generatedEmailData?.subject || "",
      current_body: window.generatedEmailData?.body || "",
      user_prompt: text
    };

    const res = await fetch("http://localhost:5000/generate_and_modify_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    const subject = result.subject || '';
    const body = result.body || '';
    const message = result.message || '';

    if (message) console.log("Backend message:", message);

    window.generatedEmailData = { subject, body };
    const responseBox = document.querySelector(".placeholder");
    responseBox.innerText = `📧 Updated Email\n\nSubject: ${subject}\n\n${body}`;
    const sendEmailBtn = document.getElementById("send-email-from-file-btn");
    if (sendEmailBtn) sendEmailBtn.style.display = 'inline-block';

    const aiBubbles = document.querySelectorAll(".bubble.ai");
    const lastAiBubble = aiBubbles[aiBubbles.length - 1];
    if (lastAiBubble) lastAiBubble.innerText = "✅ Email updated! The updated email is shown above.";

  } catch (err) {
    console.error("❌ Email modification error:", err);
    const aiBubbles = document.querySelectorAll(".bubble.ai");
    const lastAiBubble = aiBubbles[aiBubbles.length - 1];
    if (lastAiBubble) lastAiBubble.innerText = `❌ Failed to modify email: ${err.message}`;
  }
});

// ============================
// 生成邮件
// ============================
document.getElementById("generate-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input").value;
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");

  responseBox.innerText = "⏳ Generating email... Please wait.";

  try {
    const payload = {
      job_description: currentJobDescription,
      resume: resumeContent,
      current_subject: window.generatedEmailData?.subject || "",
      current_body: window.generatedEmailData?.body || "",
      user_prompt: userInput || ""
    };

    const res = await fetch("http://localhost:5000/generate_and_modify_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    const subject = result.subject || '';
    const body = result.body || '';
    const message = result.message || '';

    if (message) console.log("Backend message:", message);
    window.generatedEmailData = { subject, body };

    responseBox.innerText = `📧 Generated Email\n\nSubject: ${subject}\n\n${body}`;
    sendEmailBtn.style.display = 'inline-block';

  } catch (err) {
    console.error("[ERROR] Failed to fetch email:", err);
    responseBox.innerText = "❌ Failed to generate email. Please try again.";
  }
});

// ============================
// 发送邮件
// ============================
document.getElementById("send-email-from-file-btn").addEventListener("click", async () => {
  const responseBox = document.querySelector(".placeholder");

  if (!window.generatedEmailData || !window.generatedEmailData.subject || !window.generatedEmailData.body) {
    responseBox.innerText = "❌ Please generate an email first.";
    return;
  }

  try {
    responseBox.innerText = "🔐 正在获取Google授权...";

    if (!chrome || !chrome.runtime || !chrome.runtime.id) {
      throw new Error("扩展上下文已失效，请重新加载扩展程序");
    }

    const accessToken = await window.googleAuth.getAccessToken();
    responseBox.innerText = "📧 正在发送邮件...";

    const toEmail = document.getElementById("recipient-email").value || "recruiter@company.com";

    const res = await fetch("http://localhost:5000/send-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify({
        subject: window.generatedEmailData.subject,
        body: window.generatedEmailData.body,
        to: toEmail,
        access_token: accessToken
      }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    if (result.success) {
      responseBox.innerText = "✅ Email sent successfully with Google OAuth!";
    } else {
      responseBox.innerText = `❌ Failed to send email: ${result.message || 'Unknown error'}`;
      console.error("[ERROR] Email sending failed:", result.error);
    }

  } catch (error) {
    console.error("[ERROR] Email sending failed:", error);
    if (error.message.includes('context invalidated') || error.message.includes('扩展上下文已失效')) {
      responseBox.innerText = "❌ 扩展上下文已失效，请在Chrome扩展管理页面重新加载此扩展程序";
    } else {
      responseBox.innerText = `❌ Failed to send email: ${error.message}`;
    }
  }
});

// ============================
// 获取收件人邮箱按钮功能
// ============================
document.getElementById("get-recipient-btn").addEventListener("click", async () => {
  const companyName = document.getElementById("company-name").value;
  const jobTitle = document.getElementById("job-title").value;
  const status = document.getElementById("recipient-status");
  const emailInput = document.getElementById("recipient-email");

  if (!companyName || !jobTitle) {
    status.innerText = "❌ Missing company name or job title.";
    return;
  }

  status.innerText = "🔍 Looking for recruiter email...";

  try {
    const res = await fetch("http://localhost:5000/get_recipient_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify({ company: companyName, title: jobTitle })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    if (result.email) {
      emailInput.value = result.email;
      status.innerText = "✅ Email found and filled.";
    } else {
      status.innerText = "⚠️ No email found. You can manually enter it below.";
      emailInput.placeholder = "Enter recipient email manually";
    }

  } catch (err) {
    console.error("❌ Error fetching recipient email:", err);
    status.innerText = "❌ Failed to get recipient email. Try again later.";
  }
});