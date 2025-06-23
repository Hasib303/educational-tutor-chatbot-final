class ChatApp {
    constructor() {
        this.currentSessionId = null;
        this.isLoading = false;
        this.initializeElements();
        this.bindEvents();
        this.autoResizeTextarea();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.status = document.getElementById('status');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.charCount = document.querySelector('.char-count');
    }

    bindEvents() {
        // Send message events
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input events
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateSendButton();
        });

        // Button events
        this.newChatBtn.addEventListener('click', () => this.startNewChat());
        this.clearBtn.addEventListener('click', () => this.clearChat());

        // Sample question events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('sample-btn')) {
                const question = e.target.dataset.question;
                this.messageInput.value = question;
                this.updateCharCount();
                this.updateSendButton();
                this.sendMessage();
            }
        });
    }

    autoResizeTextarea() {
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count}/1000`;
        
        if (count > 900) {
            this.charCount.style.color = '#e53e3e';
        } else if (count > 800) {
            this.charCount.style.color = '#f56500';
        } else {
            this.charCount.style.color = '#718096';
        }
    }

    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isLoading;
    }

    updateStatus(message, type = 'normal') {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
    }

    showLoading() {
        this.isLoading = true;
        this.loadingOverlay.classList.remove('hidden');
        this.updateSendButton();
        this.updateStatus('Thinking...', 'thinking');
    }

    hideLoading() {
        this.isLoading = false;
        this.loadingOverlay.classList.add('hidden');
        this.updateSendButton();
        this.updateStatus('Ready to help!');
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.updateCharCount();
        this.updateSendButton();

        // Hide welcome message if present
        this.hideWelcomeMessage();

        // Show loading state
        this.showLoading();

        try {
            const response = await this.callChatAPI(message);
            this.addMessage(response.response, 'assistant');
            this.currentSessionId = response.session_id;
        } catch (error) {
            console.error('Chat error:', error);
            let errorMessage = 'Sorry, I encountered an error. Please try again.';
            
            if (error.message === "API_KEY_NOT_CONFIGURED") {
                errorMessage = `🔑 **API Configuration Required**

The OpenRouter API key is not configured. To use this chatbot:

1. **Get your free API key** from https://openrouter.ai
2. **Set the environment variable**: \`OPENROUTER_API_KEY=your_key_here\`
3. **Restart the server**

For local development, you can create a \`.env\` file with your API key.`;
            } else if (error.message.includes('HTTP error')) {
                errorMessage = `❌ **API Error**: ${error.message}`;
            }
            
            this.addMessage(errorMessage, 'assistant', true);
            this.updateStatus(error.message === "API_KEY_NOT_CONFIGURED" ? 'API key required' : 'Error occurred', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async callChatAPI(message) {
        const payload = {
            message: message,
            ...(this.currentSessionId && { session_id: this.currentSessionId })
        };

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            if (response.status === 500 && errorData.detail === "OpenRouter API key not configured") {
                throw new Error("API_KEY_NOT_CONFIGURED");
            }
            throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
        }

        return await response.json();
    }

    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isError) {
            messageContent.style.background = '#fed7d7';
            messageContent.style.color = '#e53e3e';
            messageContent.style.borderColor = '#feb2b2';
        }
        
        // Format message content
        const formattedContent = this.formatMessage(content);
        messageContent.innerHTML = formattedContent;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Basic formatting for better readability
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    hideWelcomeMessage() {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }

    showWelcomeMessage() {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'block';
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    async startNewChat() {
        try {
            this.showLoading();
            const response = await fetch('/chat/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentSessionId = data.session_id;
                this.clearChat();
                this.updateStatus('New chat started!');
                this.messageInput.focus();
            } else {
                throw new Error('Failed to create new chat');
            }
        } catch (error) {
            console.error('New chat error:', error);
            this.updateStatus('Failed to start new chat', 'error');
        } finally {
            this.hideLoading();
        }
    }

    clearChat() {
        // Remove all messages except welcome message
        const messages = this.chatMessages.querySelectorAll('.message');
        messages.forEach(message => message.remove());
        
        // Show welcome message
        this.showWelcomeMessage();
        
        // Reset session
        this.currentSessionId = null;
        this.updateStatus('Chat cleared');
    }

    // Utility method to check API health
    async checkAPIHealth() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                const data = await response.json();
                console.log('API Health:', data);
                return true;
            }
        } catch (error) {
            console.error('API health check failed:', error);
            return false;
        }
        return false;
    }
}

// Initialize the chat app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chatApp = new ChatApp();
    
    // Check API health on startup
    chatApp.checkAPIHealth().then(isHealthy => {
        if (!isHealthy) {
            chatApp.updateStatus('API connection issue', 'error');
        }
    });
    
    // Focus on input field
    chatApp.messageInput.focus();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Page became visible, check if input should be focused
        const messageInput = document.getElementById('messageInput');
        if (messageInput && !messageInput.disabled) {
            messageInput.focus();
        }
    }
});

// Handle window resize for mobile
window.addEventListener('resize', () => {
    // Adjust chat container height on mobile when keyboard appears
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer && window.innerHeight < 600) {
        chatContainer.style.height = `${window.innerHeight - 120}px`;
    } else if (chatContainer) {
        chatContainer.style.height = '100%';
    }
});