const API_BASE_URL = "http://localhost:8000";
let chatStarted = false;
let isSending = false;

function sendMessage() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message || isSending) return;

  input.value = "";
  addUserMessage(message);
  scrollChatToBottom();

  if (!chatStarted) {
    chatStarted = true;
    document.getElementById("inputWrapper").classList.remove("center");
    document.getElementById("inputWrapper").classList.add("bottom");
  }

  closeMenus();
  streamBotResponse(message);
}

function addUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg user";
  msg.innerText = text;
  document.getElementById("chatArea").appendChild(msg);
}

function addBotMessagePlaceholder() {
  const msg = document.createElement("div");
  msg.className = "msg bot";
  msg.innerText = "Amigo is typing...";
  document.getElementById("chatArea").appendChild(msg);
  return msg;
}

function scrollChatToBottom() {
  const chat = document.getElementById("chatArea");
  chat.scrollTop = chat.scrollHeight;
}

async function streamBotResponse(message) {
  isSending = true;
  const botMessage = addBotMessagePlaceholder();
  scrollChatToBottom();

  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      botMessage.innerText = `Error: ${errorText || response.statusText}`;
      return;
    }

    botMessage.innerText = "";
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      if (value) {
        const chunkText = decoder.decode(value, { stream: true });
        botMessage.innerText += chunkText;
        scrollChatToBottom();
      }
      done = readerDone;
    }
  } catch (error) {
    botMessage.innerText = `Error: ${error.message}`;
  } finally {
    isSending = false;
  }
}

function togglePlusMenu(event) {
  event.stopPropagation();
  const menu = document.getElementById("plusMenu");
  if (!menu) return;
  menu.style.display = menu.style.display === "block" ? "none" : "block";
}

function toggleUserMenu(event) {
  event.stopPropagation();
  const menu = document.getElementById("userMenu");
  if (!menu) return;
  menu.style.display = menu.style.display === "block" ? "none" : "block";
}

function closeMenus() {
  const plusMenu = document.getElementById("plusMenu");
  const userMenu = document.getElementById("userMenu");
  if (plusMenu) plusMenu.style.display = "none";
  if (userMenu) userMenu.style.display = "none";
}

document.addEventListener("click", function () {
  closeMenus();
});

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("collapsed");
}

function setTheme() {
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.body.classList.toggle("light", !dark);
}
setTheme();

function toggleTheme() {
  document.body.classList.toggle("light");
}

const inputField = document.getElementById("userInput");
inputField.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
});
