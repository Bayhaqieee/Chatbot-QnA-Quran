document.addEventListener('DOMContentLoaded', () => {

    // --- Logic for murajaah.html (Selection Page) ---
    const qariSelect = document.getElementById('qariSelect');
    const surahListContainer = document.getElementById('surahListContainer');
    const surahSearchInput = document.getElementById('surahSearchInput');

    if (qariSelect && surahListContainer) {
        
        // Function to update all surah links with the selected Qari
        function updateSurahLinks() {
            const selectedQari = qariSelect.value;
            const surahCards = surahListContainer.querySelectorAll('.surah-select-card');
            
            surahCards.forEach(card => {
                const baseUrl = card.href.split('?')[0]; // Get URL without query params
                card.href = `${baseUrl}?qari=${selectedQari}`;
            });
        }

        // Function to filter surahs based on search
        function filterSurahs() {
            const searchTerm = surahSearchInput.value.toLowerCase();
            const surahCards = surahListContainer.querySelectorAll('.surah-select-card');

            surahCards.forEach(card => {
                const namaLatin = card.getAttribute('data-nama-latin');
                const nomor = card.getAttribute('data-nomor');
                
                if (namaLatin.includes(searchTerm) || nomor.includes(searchTerm)) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        }

        // Initial setup
        updateSurahLinks(); // Set default qari param on page load

        // Event Listeners
        qariSelect.addEventListener('change', updateSurahLinks);
        surahSearchInput.addEventListener('input', filterSurahs);
    }


    // --- Logic for murajaah_detail.html (Reading Page) ---
    const audioPlayer = document.getElementById('murajaahAudioPlayer');
    const textContent = document.getElementById('murajaahTextContent');
    let currentPlayingAyat = null;

    if (audioPlayer && textContent) {
        textContent.addEventListener('click', (event) => {
            const ayatSpan = event.target.closest('.ayat-span');
            if (!ayatSpan) return; // Didn't click on an ayat

            const audioSrc = ayatSpan.getAttribute('data-audio-src');
            if (!audioSrc) {
                console.warn('No audio source for this ayat.');
                return; // No audio available
            }

            if (currentPlayingAyat === ayatSpan && !audioPlayer.paused) {
                // --- PAUSE ---
                audioPlayer.pause();
                ayatSpan.classList.remove('playing');
                currentPlayingAyat = null;
            } else {
                // --- PLAY ---
                // Stop and reset previous ayat if one was playing
                if (currentPlayingAyat) {
                    currentPlayingAyat.classList.remove('playing');
                }
                
                // Play new audio
                audioPlayer.src = audioSrc;
                audioPlayer.play();
                ayatSpan.classList.add('playing');
                currentPlayingAyat = ayatSpan;
            }
        });

        // Event listener to remove class when audio finishes
        audioPlayer.addEventListener('ended', () => {
            if (currentPlayingAyat) {
                currentPlayingAyat.classList.remove('playing');
                currentPlayingAyat = null;
            }
        });

        // Event listener to remove class if paused (e.g., from controls)
        audioPlayer.addEventListener('pause', () => {
             if (currentPlayingAyat && audioPlayer.paused) {
                 currentPlayingAyat.classList.remove('playing');
                 currentPlayingAyat = null;
             }
        });
    }
});