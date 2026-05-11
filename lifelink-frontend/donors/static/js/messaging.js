document.addEventListener("DOMContentLoaded", () => {
    const conversationList = document.getElementById("conversation-list");
    const chatBox = document.getElementById("chat-box");
    const messageForm = document.getElementById("message-form");
    const messageInput = document.getElementById("message-input");
    const receiverInput = document.getElementById("receiver-id");
    const statusBox = document.getElementById("message-status");

    let activeReceiverId = null;
    let pollInterval = null;

    function getCSRFToken() {
        const name = "csrftoken=";
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name)) {
                return decodeURIComponent(cookie.substring(name.length));
            }
        }
        return "";
    }

    async function fetchJSON(url, options = {}) {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status} ${response.statusText}`);
        }
        return response.json();
    }

    function setStatus(message, type = "info") {
        if (!statusBox) return;
        statusBox.textContent = message;
        statusBox.className = `status ${type}`;
    }

    function clearChat() {
        if (chatBox) {
            chatBox.innerHTML = `<p class="empty-chat">Select a conversation to view messages.</p>`;
        }
    }

    function renderConversations(conversations) {
        if (!conversationList) return;

        if (!conversations || conversations.length === 0) {
            conversationList.innerHTML = `<li class="empty-item">No conversations yet.</li>`;
            return;
        }

        conversationList.innerHTML = conversations.map(convo => `
            <li>
                <button 
                    type="button"
                    class="conversation-item ${String(convo.user_id) === String(activeReceiverId) ? "active" : ""}"
                    data-user-id="${convo.user_id}"
                    data-user-name="${convo.name || 'User'}"
                >
                    <span class="name">${convo.name || "User"}</span>
                    <span class="preview">${convo.last_message || "No messages yet"}</span>
                </button>
            </li>
        `).join("");

        document.querySelectorAll(".conversation-item").forEach(button => {
            button.addEventListener("click", () => {
                const userId = button.dataset.userId;
                const userName = button.dataset.userName;
                activeReceiverId = userId;
                receiverInput.value = userId;
                loadMessages(userId, userName);
                highlightActiveConversation(userId);
                startPolling(userId, userName);
            });
        });
    }

    function highlightActiveConversation(userId) {
        document.querySelectorAll(".conversation-item").forEach(button => {
            button.classList.toggle("active", button.dataset.userId === String(userId));
        });
    }

    function renderMessages(messages, userName = "User") {
        if (!chatBox) return;

        if (!messages || messages.length === 0) {
            chatBox.innerHTML = `<p class="empty-chat">No messages with ${userName} yet.</p>`;
            return;
        }

        chatBox.innerHTML = messages.map(msg => `
            <div class="message-row ${msg.is_sender ? "sent" : "received"}">
                <div class="message-bubble">
                    <p>${escapeHTML(msg.content)}</p>
                    <small>${msg.timestamp || ""}</small>
                </div>
            </div>
        `).join("");

        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function escapeHTML(text) {
        const div = document.createElement("div");
        div.textContent = text || "";
        return div.innerHTML;
    }

    async function loadConversations() {
        try {
            setStatus("Loading conversations...", "info");
            const data = await fetchJSON("/messages/conversations/");
            renderConversations(data.conversations || []);
            setStatus("", "info");
        } catch (error) {
            console.error(error);
            setStatus("Could not load conversations.", "error");
        }
    }

    async function loadMessages(userId, userName = "User") {
        try {
            setStatus(`Loading messages with ${userName}...`, "info");
            const data = await fetchJSON(`/messages/thread/${userId}/`);
            renderMessages(data.messages || [], userName);
            setStatus("", "info");
        } catch (error) {
            console.error(error);
            setStatus("Could not load messages.", "error");
        }
    }

    async function sendMessage(event) {
        event.preventDefault();

        const content = messageInput.value.trim();
        const receiverId = receiverInput.value;

        if (!receiverId) {
            setStatus("Select a conversation first.", "warning");
            return;
        }

        if (!content) {
            setStatus("Message cannot be empty.", "warning");
            return;
        }

        try {
            setStatus("Sending message...", "info");

            const response = await fetch("/messages/send/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    receiver_id: receiverId,
                    content: content
                })
            });

            if (!response.ok) {
                throw new Error(`Send failed: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                messageInput.value = "";
                await loadMessages(receiverId);
                await loadConversations();
                setStatus("Message sent.", "success");
            } else {
                setStatus(data.error || "Failed to send message.", "error");
            }
        } catch (error) {
            console.error(error);
            setStatus("Could not connect to backend for messaging.", "error");
        }
    }

    function startPolling(userId, userName) {
        stopPolling();
        pollInterval = setInterval(() => {
            loadMessages(userId, userName);
        }, 5000);
    }

    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    if (messageForm) {
        messageForm.addEventListener("submit", sendMessage);
    }

    clearChat();
    loadConversations();

    function loadConversations() {
    renderConversations(sampleConversations);
}

function loadMessages(userId, userName = "User") {
    renderMessages(sampleMessages[userId] || [], userName);
}
async function api(path, method = "GET", body = null) {
    const options = {
        method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`/proxy/${path}`, options);

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`API error ${response.status}: ${text}`);
    }

    return response.json();
}
});
