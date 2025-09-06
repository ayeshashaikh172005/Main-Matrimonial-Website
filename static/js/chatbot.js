document.addEventListener("DOMContentLoaded", () => {
    const chatBody = document.querySelector(".chat-body");
    const messageInput = document.querySelector(".message-input");
    const sendMessage = document.getElementById("send-message");
    const fileInput = document.getElementById("file-input");
    const fileUploadWrapper = document.querySelector(".file-upload-wrapper");
    const fileCancelButton = document.getElementById("file-cancel");
    const fileUploadBtn = document.getElementById("file-upload");
    const chatForm = document.querySelector(".chat-form");
    const chatbotToggler = document.getElementById("chatbot-toggler");
    const closeChatbot = document.getElementById("close-chatbot");

    const userData = { message: null, file: null };
    const initialInputHeight = messageInput.scrollHeight;

    // Create message element
    const createMessageElement = (content, ...classes) => {
        const div = document.createElement("div");
        div.classList.add("message", ...classes);
        div.innerHTML = content;
        return div;
    };

    // Add message to chat
    const addMessage = (text, sender = "bot") => {
        const div = createMessageElement(`<div class="message-text">${text}</div>`, `${sender}-message`);
        chatBody.appendChild(div);
        chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });
        return div;
    };

    // Generate bot response
    const generateBotResponse = async (userMessageDiv) => {
        const messageElement = userMessageDiv.querySelector(".message-text");
        try {
            const response = await fetch("http://127.0.0.1:5000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userData.message })
            });
            const data = await response.json();
            messageElement.innerText = data.reply;
        } catch (error) {
            console.error(error);
            messageElement.innerText = "Oops! Something went wrong";
            messageElement.style.color = "#ff0000";
        } finally {
            userData.message = "";
            userData.file = null;
            userMessageDiv.classList.remove("thinking");
            chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });
        }
    };

    // Handle sending message
    const handleOutgoingMessage = (e) => {
        e.preventDefault();
        if (!messageInput.value.trim()) return;

        userData.message = messageInput.value.trim();
        messageInput.value = "";
        messageInput.dispatchEvent(new Event("input"));
        fileUploadWrapper.classList.remove("file-uploaded");

        // User message
        addMessage(userData.message, "user");

        // Bot typing animation
        const thinkingContent = `
            <div class="message-text">
                <div class="thinking-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        const botMessageDiv = createMessageElement(thinkingContent, "bot-message", "thinking");
        chatBody.appendChild(botMessageDiv);
        chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });

        // Generate bot response
        generateBotResponse(botMessageDiv);
    };

    // Dynamic input height
    messageInput.addEventListener("input", () => {
        messageInput.style.height = `${initialInputHeight}px`;
        messageInput.style.height = `${messageInput.scrollHeight}px`;
    });

    // Send on Enter
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && messageInput.value.trim()) {
            handleOutgoingMessage(e);
        }
    });

    // File upload button
    fileUploadBtn.addEventListener("click", () => fileInput.click());

    // File input change
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            fileUploadWrapper.querySelector("img").src = e.target.result;
            fileUploadWrapper.classList.add("file-uploaded");
            userData.file = { data: e.target.result.split(",")[1], mime_type: file.type };
        };
        reader.readAsDataURL(file);
    });

    // Cancel file
    fileCancelButton.addEventListener("click", () => {
        userData.file = null;
        fileUploadWrapper.classList.remove("file-uploaded");
    });

    // Toggle chatbot
    chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));
    closeChatbot.addEventListener("click", () => document.body.classList.remove("show-chatbot"));

    // Send button and form submit
    sendMessage.addEventListener("click", handleOutgoingMessage);
    chatForm.addEventListener("submit", handleOutgoingMessage);
});
