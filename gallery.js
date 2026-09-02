// Search and filter functionality for image gallery

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const tagButtons = document.querySelectorAll('.tag-btn');
    const clearFilterBtn = document.getElementById('clearFilter');
    const imageCards = document.querySelectorAll('.image-card');
    let activeTags = new Set();

    // Search functionality
    searchInput.addEventListener('input', function() {
        filterGallery();
    });

    // Tag filter functionality
    tagButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tag = this.dataset.tag;
            
            if (activeTags.has(tag)) {
                activeTags.delete(tag);
                this.classList.remove('active');
            } else {
                activeTags.add(tag);
                this.classList.add('active');
            }
            
            filterGallery();
        });
    });

    // Clear filters
    clearFilterBtn.addEventListener('click', function() {
        activeTags.clear();
        searchInput.value = '';
        tagButtons.forEach(btn => btn.classList.remove('active'));
        filterGallery();
    });

    // Main filter function
    function filterGallery() {
        const searchTerm = searchInput.value.toLowerCase();
        let visibleCount = 0;

        imageCards.forEach(card => {
            const tags = card.dataset.tags.split(',');
            const title = card.dataset.title;
            const description = card.dataset.description;

            // Check search term
            const matchesSearch = !searchTerm || 
                title.includes(searchTerm) || 
                description.includes(searchTerm) ||
                tags.some(tag => tag.includes(searchTerm));

            // Check tag filters
            const matchesTags = activeTags.size === 0 || 
                tags.some(tag => activeTags.has(tag));

            // Show or hide card
            if (matchesSearch && matchesTags) {
                card.classList.remove('hidden');
                visibleCount++;
            } else {
                card.classList.add('hidden');
            }
        });

        // Show "no results" message if needed
        showNoResults(visibleCount === 0);
    }

    function showNoResults(show) {
        let noResultsDiv = document.querySelector('.no-results');
        
        if (show) {
            if (!noResultsDiv) {
                noResultsDiv = document.createElement('div');
                noResultsDiv.className = 'no-results';
                noResultsDiv.textContent = 'No images found matching your filters.';
                document.querySelector('.gallery').appendChild(noResultsDiv);
            }
        } else {
            if (noResultsDiv) {
                noResultsDiv.remove();
            }
        }
    }
});