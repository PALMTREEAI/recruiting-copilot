// Recruiting Co-Pilot Frontend
// Simple chat interface for asking questions about the pipeline

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const refreshBtn = document.getElementById('refreshBtn');
const chatHistory = document.getElementById('chatHistory');

let isLoading = false;

// Send message on button click
sendBtn.addEventListener('click', sendMessage);

// Send message on Enter key
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !isLoading) {
        sendMessage();
    }
});

// Refresh data
refreshBtn.addEventListener('click', refreshData);

async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    chatInput.value = '';
    sendBtn.disabled = true;
    refreshBtn.disabled = true;
    isLoading = true;
    
    // Show loading indicator
    const loadingId = addLoadingIndicator();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        removeMessage(loadingId);
        
        // Add assistant response
        addMessageToChat(data.response, 'assistant');
        
    } catch (error) {
        console.error('Error:', error);
        removeMessage(loadingId);
        addMessageToChat('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        sendBtn.disabled = false;
        refreshBtn.disabled = false;
        isLoading = false;
        chatInput.focus();
    }
}

async function refreshData() {
    refreshBtn.disabled = true;
    const originalText = refreshBtn.textContent;
    refreshBtn.textContent = 'Refreshing...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/refresh`, {
            method: 'POST',
        });
        
        if (!response.ok) {
            throw new Error('Failed to refresh data');
        }
        
        addMessageToChat('✓ Pipeline data refreshed from Ashby', 'assistant');
        
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('Failed to refresh data. Please try again.', 'assistant');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = originalText;
    }
}

function addMessageToChat(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const messageP = document.createElement('p');
    messageP.textContent = message;
    
    messageDiv.appendChild(messageP);
    chatHistory.appendChild(messageDiv);
    
    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    return messageDiv;
}

function addLoadingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'loading-indicator';
    
    const messageP = document.createElement('p');
    messageP.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
    
    messageDiv.appendChild(messageP);
    chatHistory.appendChild(messageDiv);
    
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    return messageDiv;
}

function removeMessage(element) {
    if (element && element.parentNode) {
        element.remove();
    }
}
