document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const noResultsMessage = document.getElementById('noResultsMessage');
    
    // Check if we are on the detail page (has .verse-card) or list page (has .list-card)
    let cards = content.querySelectorAll('.verse-card');
    let isDetailPage = true;
    if (cards.length === 0) {
        cards = content.querySelectorAll('.list-card');
        isDetailPage = false;
    }

    if (!searchInput) return;

    searchInput.addEventListener('input', (event) => {
        const searchTerm = event.target.value.toLowerCase().trim();
        let visibleCount = 0;

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            let cardText = '';

            if (isDetailPage) {
                // On detail page, search translation, latin text, and ayat number
                const ayatNum = card.querySelector('.verse-item').getAttribute('data-ayat-number');
                const translation = card.querySelector('p:last-of-type').textContent;
                const latin = card.querySelector('.latin-text').textContent;
                cardText = `${ayatNum} ${translation} ${latin}`;
            } else {
                // On list page, search surah name, latin name, and number
                cardText = card.textContent || card.innerText;
            }

            if (cardText.toLowerCase().indexOf(searchTerm) > -1) {
                card.style.display = "";
                visibleCount++;
            } else {
                card.style.display = "none";
            }
        }

        if (visibleCount === 0 && searchTerm.length > 0) {
            noResultsMessage.textContent = `No results found for '${event.target.value}'`;
            noResultsMessage.style.display = 'block';
        } else {
            noResultsMessage.style.display = 'none';
        }
    });
});