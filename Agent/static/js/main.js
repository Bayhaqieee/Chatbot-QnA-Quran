document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const topicInput = document.getElementById('topicInput');
    const askButton = document.getElementById('askButton');
    const chatArea = document.getElementById('chat-area');
    const suggestionsWrapper = document.getElementById('prompt-suggestions-wrapper');
    const suggestionsContainer = document.getElementById('prompt-suggestions');
    const aiResponseTemplate = document.getElementById('ai-response-template');

    topicInput.addEventListener('input', () => {
        topicInput.style.height = 'auto';
        topicInput.style.height = `${topicInput.scrollHeight}px`;
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        askQuestion();
    });

    async function askQuestion(questionText = null) {
        const topic = questionText || topicInput.value.trim();
        if (!topic) return;

        topicInput.value = '';
        topicInput.style.height = 'auto';
        suggestionsWrapper.style.display = 'none';
        suggestionsContainer.innerHTML = '';

        displayUserMessage(topic);
        const loaderId = 'loader-' + Date.now();
        displayLoader(loaderId);
        askButton.disabled = true;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });
            
            document.getElementById(loaderId)?.remove();
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || `Server error: ${response.status}`);
            }
            
            const data = await response.json();
            displayAiResponse(data);

        } catch (error) {
            displayErrorMessage(error.message);
        } finally {
            askButton.disabled = false;
        }
    }

    function displayUserMessage(message) {
        const userMessageHtml = `
            <div class="message-wrapper">
                <div class="message-header user-header">You</div>
                <div class="message-content user">${message.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
            </div>`;
        chatArea.insertAdjacentHTML('beforeend', userMessageHtml);
        scrollToBottom();
    }
    
    function displayLoader(id) {
        const loaderHtml = `
            <div class="message-wrapper" id="${id}">
                <div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div>
                <div class="loader-wrapper"><i class="fas fa-spinner fa-spin"></i> Thinking...</div>
            </div>`;
        chatArea.insertAdjacentHTML('beforeend', loaderHtml);
        scrollToBottom();
    }

    function displayErrorMessage(errorMsg) {
        const errorHtml = `
            <div class="message-wrapper">
                <div class="message-header ai-header"><i class="fas fa-robot"></i> AI Team</div>
                <div class="ai-response"><p style="color:#e57373;">Error: ${errorMsg}</p></div>
            </div>`;
        chatArea.insertAdjacentHTML('beforeend', errorHtml);
        scrollToBottom();
    }

    function displayAiResponse(data) {
        const templateNode = aiResponseTemplate.content.cloneNode(true);
        const aiWrapper = templateNode.querySelector('.message-wrapper');

        // Show thinking (Chain of Thought)
        const thoughtContainer = aiWrapper.querySelector('[data-container="chain-of-thought"]');
        if (data.chain_of_thought) {
            thoughtContainer.style.display = 'block';
            thoughtContainer.innerHTML = `
                <details>
                    <summary>Show thinking <i class="fas fa-chevron-down icon"></i></summary>
                    <div class="thinking-dropdown-content">${data.chain_of_thought}</div>
                </details>`;
        }
        
        // Quotes (Sources)
        const sourcesContainer = aiWrapper.querySelector('[data-container="sources-quote"]');
        if (data.sources && data.sources.length > 0) {
            sourcesContainer.style.display = 'block';
            sourcesContainer.innerHTML = `<ul>${data.sources.map(s => `<li>${s}</li>`).join('')}</ul>`;
        }

        // Main Answer
        const answerContainer = aiWrapper.querySelector('[data-container="answer"]');
        answerContainer.innerHTML = data.answer ? `<p>${data.answer.replace(/\n/g, '<br>')}</p>` : `<p>No answer provided.</p>`;
        
        // Web Sources (Perplexity Style)
        const webSourcesContainer = aiWrapper.querySelector('[data-container="web-sources"]');
        if (data.web_sources && data.web_sources.length > 0) {
            webSourcesContainer.style.display = 'block';
            let cardsHtml = `<div class="web-sources-header"><i class="fas fa-globe"></i> Sources</div><div class="web-sources-grid">`;
            cardsHtml += data.web_sources.map(ws => `<a href="${ws.url}" target="_blank" class="web-source-card">${ws.title}</a>`).join('');
            cardsHtml += `</div>`;
            webSourcesContainer.innerHTML = cardsHtml;
        }
        
        chatArea.appendChild(aiWrapper);

        // Follow-up Questions
        if (data.follow_up_questions && data.follow_up_questions.length > 0) {
            suggestionsWrapper.style.display = 'block';
            suggestionsContainer.innerHTML = ''; // Clear previous
            data.follow_up_questions.forEach(q => {
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                card.textContent = q;
                card.onclick = () => askQuestion(q);
                suggestionsContainer.appendChild(card);
            });
        }
        
        scrollToBottom();
    }

    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }
});