// ============================
// Google授权类
// ============================
class GoogleAuth {
    // 获取访问令牌 - Chrome扩展专用方式
    async getAccessToken() {
        return new Promise((resolve, reject) => {
            // 检查chrome.identity是否可用
            if (!chrome || !chrome.identity) {
                reject(new Error("Chrome identity API not available"));
                return;
            }

            chrome.identity.getAuthToken({
                interactive: true
            }, (token) => {
                if (chrome.runtime.lastError) {
                    // 如果是context invalidated错误，提示用户重新加载扩展
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

// 保存结构化的邮件数据到全局变量，初始化为示例邮件
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
// 页面加载事件处理
// ============================
window.addEventListener("DOMContentLoaded", () => {
  const savedResume = localStorage.getItem("resumeText");
  const statusEl = document.getElementById("resume-status");
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");

  // 恢复之前保存的简历内容
  if (savedResume) {
    resumeContent = savedResume;
    if (statusEl) {
      statusEl.innerText = "📄 Resume restored from last session.";
    }
    console.log("✅ Resume restored from localStorage");
  }

  // 显示初始的sample email
  if (responseBox && window.generatedEmailData) {
    responseBox.innerText = `📧 Generated Email\n\nSubject: ${window.generatedEmailData.subject}\n\n${window.generatedEmailData.body}`;
    // 显示发送按钮，因为有有效的邮件数据
    if (sendEmailBtn) {
      sendEmailBtn.style.display = 'inline-block';
    }
  }
});

// ============================
// 获取网页显示的jd和 公司名
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
  const chatBox = document.getElementById("chat-box");

  const text = userInput.value.trim();
  if (!text) return;

  // 检查是否已有生成的邮件数据
  if (!window.generatedEmailData || !window.generatedEmailData.subject || !window.generatedEmailData.body) {
    addMessageToChat("❌ Please generate an email first before making modifications.", "ai");
    return;
  }

  // 1️⃣ 添加用户消息
  addMessageToChat(text, "user");
  userInput.value = "";

  // 2️⃣ 添加 AI 占位消息
  addMessageToChat("Modifying email...", "ai");

  // 3️⃣ 发送到后端修改邮件
  try {
    const payload = {
      job_description: currentJobDescription,
      resume: resumeContent,
      current_subject: window.generatedEmailData?.subject || "",
      current_body: window.generatedEmailData?.body || "",
      user_prompt: text // 用户的修改要求
    };

    console.log("🔍 [DEBUG] Sending modification request:", {
      job_description_length: currentJobDescription?.length || 0,
      resume_length: resumeContent?.length || 0,
      current_subject: payload.current_subject,
      current_body_length: payload.current_body?.length || 0,
      user_prompt: payload.user_prompt
    });

    const res = await fetch("http://localhost:5000/generate_and_modify_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify(payload)
    });

    console.log("🔍 [DEBUG] Response status:", res.status);

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    const result = await res.json();
    console.log("🔍 [DEBUG] Response data:", result);
    
    // 处理后端统一返回格式：{subject: "...", body: "...", message?: "..."
    const subject = result.subject || '';
    const body = result.body || '';
    const message = result.message || '';
    
    console.log("🔍 [DEBUG] Extracted data:", {
      subject_length: subject?.length || 0,
      body_length: body?.length || 0,
      has_message: !!message
    });
    
    // 记录message字段到控制台
    if (message) {
      console.log("Backend message:", message);
    }
    
    // 更新全局邮件数据
    window.generatedEmailData = {
      subject: subject,
      body: body
    };
    
    console.log("🔍 [DEBUG] Updated global email data:", window.generatedEmailData);
    
    // 更新显示的邮件内容
    const responseBox = document.querySelector(".placeholder");
    const newContent = `📧 Updated Email\n\nSubject: ${subject}\n\n${body}`;
    console.log("🔍 [DEBUG] Setting responseBox content:", newContent);
    responseBox.innerText = newContent;
    
    // 确保发送按钮可见
    const sendEmailBtn = document.getElementById("send-email-from-file-btn");
    if (sendEmailBtn) {
      sendEmailBtn.style.display = 'inline-block';
    }

    // 替换占位消息为成功消息 - 修复后的代码
    const aiBubbles = document.querySelectorAll(".bubble.ai");
    const lastAiBubble = aiBubbles[aiBubbles.length - 1];
    if (lastAiBubble) {
      lastAiBubble.innerText = "✅ Email updated! The updated email is shown above.";
    }
    
  } catch (err) {
    console.error("❌ Email modification error:", err);
    // 修复后的错误处理代码
    const aiBubbles = document.querySelectorAll(".bubble.ai");
    const lastAiBubble = aiBubbles[aiBubbles.length - 1];
    if (lastAiBubble) {
      lastAiBubble.innerText = `❌ Failed to modify email: ${err.message}`;
    }
  }
});

// ============================
// 邮件生成和修改功能
// ============================
document.getElementById("generate-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input").value;
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");

  responseBox.innerText = "⏳ Generating email... Please wait.";

  try {
    // 前端总是发送所有字段，第一次生成时current_subject、current_body、user_prompt为空
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

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    const result = await res.json();
    
    // 处理后端统一返回格式：{subject: "...", body: "...", message?: "..."
    const subject = result.subject || '';
    const body = result.body || '';
    const message = result.message || '';
    
    // 记录message字段到控制台
    if (message) {
      console.log("Backend message:", message);
    }
    
    // 更新全局邮件数据
    window.generatedEmailData = {
      subject: subject,
      body: body
    };
    
    // 显示邮件内容
    responseBox.innerText = `📧 Generated Email\n\nSubject: ${subject}\n\n${body}`;
    sendEmailBtn.style.display = 'inline-block';

  } catch (err) {
    console.error("[ERROR] Failed to fetch email:", err);
    responseBox.innerText = "❌ Failed to generate email. Please try again.";
  }
});

// ============================
// 邮件发送功能
// ============================
document.getElementById("send-email-from-file-btn").addEventListener("click", async () => {
  const responseBox = document.querySelector(".placeholder");

  // 检查是否有生成的邮件数据
  if (!window.generatedEmailData || !window.generatedEmailData.subject || !window.generatedEmailData.body) {
    responseBox.innerText = "❌ Please generate an email first.";
    return;
  }

  try {
    responseBox.innerText = "🔐 正在获取Google授权...";

    // 检查扩展上下文是否有效
    if (!chrome || !chrome.runtime || !chrome.runtime.id) {
      throw new Error("扩展上下文已失效，请重新加载扩展程序");
    }

    // 获取Google访问令牌
    const accessToken = await window.googleAuth.getAccessToken();

    responseBox.innerText = "📧 正在发送邮件...";

    // 调用后端API，使用正确的端点 /send-email
    const res = await fetch("http://localhost:5000/send-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify({
        subject: window.generatedEmailData.subject,
        body: window.generatedEmailData.body,
        to: "recruiter@company.com", // TODO: 从招聘者查找API获取
        access_token: accessToken
      }),
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    const result = await res.json();

    if (result.success) {
      responseBox.innerText = "✅ Email sent successfully with Google OAuth!";
    } else {
      responseBox.innerText = `❌ Failed to send email: ${result.message || 'Unknown error'}`;
      console.error("[ERROR] Email sending failed:", result.error);
    }

  } catch (error) {
    console.error("[ERROR] Email sending failed:", error);

    // 特殊处理扩展上下文失效的错误
    if (error.message.includes('context invalidated') || error.message.includes('扩展上下文已失效')) {
      responseBox.innerText = "❌ 扩展上下文已失效，请在Chrome扩展管理页面重新加载此扩展程序";
    } else {
      responseBox.innerText = `❌ Failed to send email: ${error.message}`;
    }
  }
});
