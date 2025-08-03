// Google授权类，用于获取这个浏览器登录的Google邮箱的access_token
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

// 全局实例
window.googleAuth = new GoogleAuth();

let currentJobDescription = "";
let resumeConteaddMessageToChatnt = "";

// ✅ 简历上传处理
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

// ✅ 恢复之前保存的简历内容
window.addEventListener("DOMContentLoaded", () => {
  const savedResume = localStorage.getItem("resumeText");
  const statusEl = document.getElementById("resume-status");

  if (savedResume) {
    resumeContent = savedResume;
    if (statusEl) {
      statusEl.innerText = "📄 Resume restored from last session.";
    }
    console.log("✅ Resume restored from localStorage");
  }
});

// ✅ 接收 Job Description + 公司 & 岗位名
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

// ✅ 聊天功能
document.getElementById("send-chat-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");

  const text = userInput.value.trim();
  if (!text) return;

  // 1️⃣ 添加用户消息
  addMessageToChat(text, "user");
  userInput.value = "";

  // 2️⃣ 添加 AI 占位消息
  addMessageToChat("Thinking...", "ai");

  // 3️⃣ 发送到后端（这里 mock）
  try {
    const res = await fetch("http://localhost:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    document.querySelectorAll(".bubble.ai").slice(-1)[0].innerText = data.reply || "[Mock reply from backend]";
  } catch (err) {
    console.error("❌ Chat error:", err);
    document.querySelectorAll(".bubble.ai").slice(-1)[0].innerText = "[Error: failed to get response]";
  }
});

function addMessageToChat(content, sender = "ai") {
  const chatBox = document.getElementById("chat-box");
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`;
  bubble.innerText = content;
  chatBox.appendChild(bubble);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ✅ Generate Email / Send Email 逻辑（保持团队原代码）
document.getElementById("generate-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input").value;
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");

  responseBox.innerText = "⏳ Generating email... Please wait.";

  try {
    const payload = {
      job_description: currentJobDescription,
      resume: resumeContent,
      user_prompt: userInput
    };

    const res = await fetch("http://localhost:5000/generate_email", {
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
    if (result.generated_email && typeof result.generated_email === 'object') {
      const subject = result.generated_email.subject || '';
      const body = result.generated_email.body || '';
      responseBox.innerText = `📧 Generated Email\n\nSubject: ${subject}\n\n${body}`;
    } else {
      responseBox.innerText = `📧 Generated Email:\n\n${result.generated_email || "(No content returned)"}`;
    }

    sendEmailBtn.style.display = 'inline-block';

  } catch (err) {
    console.error("[ERROR] Failed to fetch email:", err);
    responseBox.innerText = "❌ Failed to generate email. Please try again.";
  }
});

// 保存结构化的邮件数据到全局变量，初始化为示例邮件
window.generatedEmailData = {
  subject: "Sample Mail:Follow-up on Job Application",
  body: "Dear Hiring Manager,\n\nI am excited to apply for the position and believe my skills are a great match.\n\nBest regards,\n[Your Name]"
};



// 简历上传处理
document.getElementById("send-email-from-file-btn").addEventListener("click", async () => {
  alert('Attempting to send email using data from email_content.json...');
  const responseBox = document.querySelector(".placeholder");
  const emailContent = responseBox.innerText;

  if (!emailContent || emailContent.includes("Generating email")) {
    responseBox.innerText = "❌ Please generate an email first.";
    return;
  }
  const res = await fetch("http://localhost:5000/send-email-from-file", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-From-Extension": "true",
    },
    body: JSON.stringify({ emailContent }),
  });

  const result = await res.json();
  if (!result.success) {
    console.error("[ERROR] Email sending failed:", result.error);
  }
});
// 恢复之前保存的简历内容和显示初始邮件
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

  // 显示初始的sample email
  if (responseBox && window.generatedEmailData) {
    responseBox.innerText = `📧 Generated Email\n\nSubject: ${window.generatedEmailData.subject}\n\n${window.generatedEmailData.body}`;
    // 显示发送按钮，因为有有效的邮件数据
    if (sendEmailBtn) {
      sendEmailBtn.style.display = 'inline-block';
    }
  }
});

// Job Description预览区，接收来自 content.js 的消息
window.addEventListener("message", (event) => {
  if (event.data.type === "JOB_DESCRIPTION") {
    currentJobDescription = event.data.data;

    // 可选：在页面显示前 300 字预览
    const jdBox = document.getElementById("jd-preview");
    if (jdBox) {
      jdBox.innerText = currentJobDescription.slice(0, 1000) + '...';  // 可自行调整显示长度
    }
  }
});

// 生成邮件文本按钮点击事件
document.getElementById("generate-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input").value;
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");


  responseBox.innerText = "⏳ Generating email... Please wait.";

  try {
    const payload = {
      job_description: currentJobDescription,     // JD：从页面抓取的
      resume: resumeContent,
      user_prompt: userInput                      // 用户提问
    };

    const res = await fetch("http://localhost:5000/generate_email", {
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
    // 判断 generated_email 是否为对象，优先显示 subject 和 body
    if (result.generated_email && typeof result.generated_email === 'object') {
      const subject = result.generated_email.subject || '';
      const body = result.generated_email.body || '';
      responseBox.innerText = `📧 Generated Email\n\nSubject: ${subject}\n\n${body}`;

      // 保存结构化的邮件数据到全局变量，供发送时使用
      window.generatedEmailData = {
        subject: subject,
        body: body
      };
    } else {
      responseBox.innerText = `📧 Generated Email:\n\n${result.generated_email || "(No content returned)"}`;
      window.generatedEmailData = null;
    }

    // 显示发送按钮
    sendEmailBtn.style.display = 'inline-block';

  } catch (err) {
    console.error("[ERROR] Failed to fetch email:", err);
    responseBox.innerText = "❌ Failed to generate email. Please try again.";
  }
});

// 现在使用Google OAuth认证
// 发送邮件按钮点击事件
document.getElementById("send-email-from-file-btn").addEventListener("click", async () => {
  alert('Attempting to send email using data from email_content.json...');
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

    // 调用后端API，传递token和结构化的邮件数据
    const res = await fetch("http://localhost:5000/send-email-from-file", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify({
        emailData: {
          subject: window.generatedEmailData.subject,
          body: window.generatedEmailData.body
        },
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
      responseBox.innerText = `❌ Failed to send email: ${result.error || 'Unknown error'}`;
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


// TODO: 聊天记录
let chatHistory = [];

function addMessageToChat(content, sender = "ai") {
  const chatBox = document.getElementById("chat-box");
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`; // user 或 ai
  bubble.innerText = content;
  chatBox.appendChild(bubble);
  chatBox.scrollTop = chatBox.scrollHeight; // 滚动到底部
}

function addMessage(content, sender) {
  chatHistory.push({ sender, content });
  addMessageToChat(content, sender);
}
