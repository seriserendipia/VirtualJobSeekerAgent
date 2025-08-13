// 延迟获取服务器URL，确保config.js已加载
function getServerURL() {
    if (typeof getServerUrl === 'function') {
        return getServerUrl();
    } else {
        console.warn('⚠️ getServerUrl function not available, using fallback');
        return "https://virtualjobseekeragent-production.up.railway.app"; // production fallback URL
    }
}

// ============================
// Google Authorization Class
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
                        reject(new Error("Extension context invalidated, please reload the extension"));
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
// Global Variables
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
// Resume Upload Handler
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
// Page Load Handler
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
// Receive Job Description & Job Info
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
// Chat Functionality
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

// ============================
// Clear Chat History Functionality
// ============================
document.getElementById("clear-chat-btn").addEventListener("click", () => {
  const chatBox = document.getElementById("chat-box");
  chatHistory = []; // Clear chat history array
  chatBox.innerHTML = ""; // Clear chat display area
  console.log("✅ Chat history cleared");
});

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
      user_feedback: text
    };

    const res = await fetch(`${getServerURL()}/generate_and_modify_email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    // 处理新的响应格式
    let subject = '';
    let body = '';
    let message = '';

    if (result.status === "Success" && result.email) {
      // 新的FastAPI格式
      subject = result.email.subject || '';
      body = result.email.body || '';
    } else {
      // 向后兼容旧格式
      subject = result.subject || '';
      body = result.body || '';
    }
    
    message = result.message || '';

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
// Generate Email
// ============================
document.getElementById("generate-btn").addEventListener("click", async () => {
  const userInput = document.getElementById("user-input").value;
  const responseBox = document.querySelector(".placeholder");
  const sendEmailBtn = document.getElementById("send-email-from-file-btn");

  console.log("📧 [前端] 点击了生成邮件按钮");
  console.log("📧 [前端] 当前状态检查:", {
    hasJobDescription: !!currentJobDescription,
    jobDescriptionLength: currentJobDescription?.length || 0,
    hasResume: !!resumeContent,
    resumeLength: resumeContent?.length || 0,
    userInput: userInput,
    serverUrl: getServerURL(),
    currentGeneratedData: window.generatedEmailData
  });

  if (!currentJobDescription || !resumeContent) {
    console.warn("📧 [前端] 缺少必要数据 - job description or resume");
    responseBox.innerText = "❌ Please upload your resume and job description first.";
    return;
  }

  responseBox.innerText = "⏳ Generating email... Please wait.";

  try {
    const payload = {
      job_description: currentJobDescription,
      resume: resumeContent,
      current_subject: window.generatedEmailData?.subject || "",
      current_body: window.generatedEmailData?.body || "",
      user_prompt: userInput || ""
    };

    console.log("📧 [前端] 开始发送请求到:", `${getServerURL()}/generate_email`);
    console.log("📧 [前端] 请求payload:", {
      job_description_length: payload.job_description?.length || 0,
      resume_length: payload.resume?.length || 0,
      current_subject: payload.current_subject,
      current_body_length: payload.current_body?.length || 0,
      user_prompt: payload.user_prompt
    });

    const res = await fetch(`${getServerURL()}/generate_email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify(payload)
    });

    console.log("📧 [前端] 响应状态:", res.status);
    console.log("📧 [前端] 响应headers:", Object.fromEntries(res.headers.entries()));

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    console.log("📧 [前端] 完整响应结果:", result);

    // 处理新的响应格式
    let subject = '';
    let body = '';
    let message = '';

    if (result.status === "Success" && result.email) {
      // 新的FastAPI格式
      subject = result.email.subject || '';
      body = result.email.body || '';
      console.log("📧 [前端] 使用新格式，subject:", subject?.substring(0, 50));
      console.log("📧 [前端] 使用新格式，body:", body?.substring(0, 100));
    } else {
      // 向后兼容旧格式
      subject = result.subject || '';
      body = result.body || '';
      console.log("📧 [前端] 使用旧格式，subject:", subject?.substring(0, 50));
      console.log("📧 [前端] 使用旧格式，body:", body?.substring(0, 100));
    }
    
    message = result.message || '';

    if (message) console.log("Backend message:", message);
    window.generatedEmailData = { subject, body };

    console.log("📧 [前端] 最终设置的数据:", {
      subject: subject?.substring(0, 50),
      body: body?.substring(0, 100),
      fullSubject: subject,
      fullBody: body
    });

    responseBox.innerText = `📧 Generated Email\n\nSubject: ${subject}\n\n${body}`;
    console.log("📧 [前端] 已更新UI显示内容");
    sendEmailBtn.style.display = 'inline-block';

  } catch (err) {
    console.error("📧 [前端] [ERROR] Failed to fetch email:", err);
    console.error("📧 [前端] [ERROR] Error stack:", err.stack);
    console.error("📧 [前端] [ERROR] Error details:", {
      name: err.name,
      message: err.message,
      stack: err.stack
    });
    responseBox.innerText = "❌ Failed to generate email. Please try again.";
  }
});

// ============================
// Send Email
// ============================
document.getElementById("send-email-from-file-btn").addEventListener("click", async () => {
  const responseBox = document.querySelector(".placeholder");

  if (!window.generatedEmailData || !window.generatedEmailData.subject || !window.generatedEmailData.body) {
    responseBox.innerText = "❌ Please generate an email first.";
    return;
  }

  try {
    responseBox.innerText = "🔐 Getting Google authorization...";

    if (!chrome || !chrome.runtime || !chrome.runtime.id) {
      throw new Error("Extension context invalidated, please reload the extension");
    }

    const accessToken = await window.googleAuth.getAccessToken();
    responseBox.innerText = "📧 Sending email...";

    const toEmail = document.getElementById("recipient-email").value || "recruiter@company.com";

    // 调用后端API，传递token和结构化的邮件数据
    const res = await fetch(`${getServerURL()}/send-email`, {
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
    if (error.message.includes('context invalidated') || error.message.includes('Extension context invalidated')) {
      responseBox.innerText = "❌ Extension context invalidated, please reload this extension in Chrome extension management page";
    } else {
      responseBox.innerText = `❌ Failed to send email: ${error.message}`;
    }
  }
});

// ============================
// Get recipient email button functionality
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
    const res = await fetch(`${getServerURL()}/find_recruiter_email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-From-Extension": "true"
      },
      body: JSON.stringify({ 
        company_name: companyName, 
        job_title: jobTitle,
        job_description: currentJobDescription
      })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    console.log("🔍 [前端] 搜索邮箱响应:", result);

    if (result.status === "Success" && result.result) {
      const searchData = result.result;
      
      if (searchData.found_email) {
        // Email address found
        emailInput.value = searchData.found_email;
        status.innerText = "✅ Email found and filled.";
      } else if (searchData.relevant_urls && searchData.relevant_urls.length > 0) {
        // No email found, but found relevant URLs
        status.innerHTML = "⚠️ No email found, but found relevant URLs:<br>" + 
          searchData.relevant_urls.map(item => `<a href="${item.url}" target="_blank">${item.title}</a>`).join('<br>');
        emailInput.placeholder = "Enter recipient email manually";
      } else {
        // No email or URLs found
        status.innerText = "⚠️ No recruiter email found. You can manually enter it below.";
        emailInput.placeholder = "Enter recipient email manually";
      }
    } else {
      // Search failed or unexpected response
      status.innerText = "⚠️ Failed to search for recruiter email. You can manually enter it below.";
      emailInput.placeholder = "Enter recipient email manually";
    }

  } catch (err) {
    console.error("❌ Error fetching recipient email:", err);
    status.innerText = "❌ Failed to get recipient email. Try again later.";
  }
});