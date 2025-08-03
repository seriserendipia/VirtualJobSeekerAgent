let currentJobDescription = "";
let resumeContent = "";

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
