let currentJobDescription = "";
let resumeContent = "";



// 简历上传处理
document.getElementById("resume-upload").addEventListener("change", function (event) {
  const file = event.target.files[0];
  const statusEl = document.getElementById("resume-status");

  if (!file) {
    statusEl.innerText = "📎 No resume uploaded";
    return;
  }

  const fileType = file.type;

  // === PDF 文件处理 ===
  if (fileType === "application/pdf") {
    resumeContent = "[Resume content from PDF file goes here]";
    localStorage.setItem("resumeText", resumeContent);
    statusEl.innerText = `📄 Uploaded PDF: ${file.name}`;

  // === TXT 文件处理 ===
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

  // === 不支持的文件类型 ===
  } else {
    statusEl.innerText = "❌ Unsupported file type. Only PDF or TXT allowed.";
  }
});

// 恢复之前保存的简历内容
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
  const sendEmailBtn = document.getElementById("send-email-btn");


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

    responseBox.innerText = `📧 Generated Email:\n\n${result.generated_email || "(No content returned)"}`;
    
    // 显示发送按钮
    sendEmailBtn.style.display = 'inline-block';

  } catch (err) {
    console.error("[ERROR] Failed to fetch email:", err);
    responseBox.innerText = "❌ Failed to generate email. Please try again.";
  }
});

// 发送邮件按钮点击事件
document.getElementById("send-email-btn").addEventListener("click", async () => {
  alert('Attempting to send email using data from email_content.json...');
  const emailContent = responseBox.innerText;
  if (!emailContent || emailContent.includes("Generating email")) {
    responseBox.innerText = "❌ Please generate an email first.";
    return;
  }
  const res = await fetch("http://localhost:5000/send-email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-From-Extension": "true",
    },
    body: JSON.stringify({ emailContent }),
  });
  if (!res.ok) {
    responseBox.innerText = "❌ Failed to send email. Please try again.";
    console.error("[ERROR] Failed to send email:", res.statusText);
    return;
  }
  const result = await res.json();
  if (result.success) {
    responseBox.innerText = "✅ Email sent successfully!";
  }
  else {
    responseBox.innerText = "❌ Failed to send email. Please try again.";
    console.error("[ERROR] Email sending failed:", result.error);
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
