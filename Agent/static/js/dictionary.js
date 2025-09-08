document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const content = document.getElementById('dictionary-content');
    const cards = content.getElementsByClassName('dictionary-card');

    searchInput.addEventListener('input', (event) => {
        const searchTerm = event.target.value.toLowerCase();

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const cardText = card.textContent || card.innerText;
            if (cardText.toLowerCase().indexOf(searchTerm) > -1) {
                card.style.display = "";
            } else {
                card.style.display = "none";
            }
        }
    });
});