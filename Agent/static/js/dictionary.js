document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const cards = content.getElementsByClassName('dictionary-card');

    searchInput.addEventListener('input', (event) => {
        const searchTerm = event.target.value.toLowerCase();

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            // Get the always-visible summary element for searching
            const summary = card.querySelector('summary');
            let cardText = '';

            if (summary) {
                // If it's a collapsible card, search only the summary
                cardText = summary.textContent || summary.innerText;
            } else {
                // Fallback for non-collapsible cards
                cardText = card.textContent || card.innerText;
            }

            if (cardText.toLowerCase().indexOf(searchTerm) > -1) {
                card.style.display = "";
            } else {
                card.style.display = "none";
            }
        }
    });
});