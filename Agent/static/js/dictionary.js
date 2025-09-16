document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const cards = content.getElementsByClassName('dictionary-card');
    const searchError = document.getElementById('searchError');
    const noResultsMessage = document.getElementById('noResultsMessage');
    let searchTimeout;

    searchInput.addEventListener('input', (event) => {
        const originalSearchTerm = event.target.value;
        // Sanitize the search term to remove special characters for matching
        const searchTerm = originalSearchTerm.replace(/[^a-zA-Z0-9 ]/g, "").toLowerCase();

        clearTimeout(searchTimeout);

        searchError.classList.remove('visible');
        searchError.textContent = '';
        noResultsMessage.style.display = 'none';

        // Perform validation on the cleaned search term
        if (searchTerm.length > 0 && searchTerm.length < 3) {
            searchTimeout = setTimeout(() => {
                searchError.textContent = 'Pencarian membutuhkan minimal 3 karakter.';
                searchError.classList.add('visible');
            }, 5000);
            
            // Hide all cards for invalid input
            for (let card of cards) {
                card.style.display = "none";
            }
            return;
        }

        let visibleCardsCount = 0;
        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const summary = card.querySelector('summary');
            let cardText = '';

            if (summary) {
                cardText = summary.textContent || summary.innerText;
            } else {
                cardText = card.textContent || card.innerText;
            }

            if (searchTerm.length === 0 || cardText.toLowerCase().indexOf(searchTerm) > -1) {
                card.style.display = "";
                visibleCardsCount++;
            } else {
                card.style.display = "none";
            }
        }

        // If no cards are visible after a valid search, show the 'not found' message
        if (visibleCardsCount === 0 && searchTerm.length >= 3) {
            // Display the user's original, un-sanitized input
            noResultsMessage.textContent = `Hasil pencarian untuk '${originalSearchTerm}' tidak ditemukan.`;
            noResultsMessage.style.display = 'block';
        }
    });
});