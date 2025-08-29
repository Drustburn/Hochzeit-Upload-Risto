// QR Code functionality
function toggleQR() {
  const dropdown = document.getElementById('qrDropdown');
  dropdown.classList.toggle('show');
}

// Close QR dropdown when clicking outside
document.addEventListener('click', function(event) {
  const qrContainer = document.querySelector('.qr-container');
  const dropdown = document.getElementById('qrDropdown');
  
  if (qrContainer && dropdown && !qrContainer.contains(event.target)) {
    dropdown.classList.remove('show');
  }
});

// Image Modal Functionality
let currentImageIndex = 0;
let allImages = [];

function initImageModal() {
  const modal = document.getElementById('imageModal');
  if (!modal) return; // Exit if modal doesn't exist on this page
  
  const modalImage = document.getElementById('modalImage');
  const modalClose = document.getElementById('modalClose');
  const modalPrev = document.getElementById('modalPrev');
  const modalNext = document.getElementById('modalNext');
  const modalCounter = document.getElementById('modalCounter');
  const modalImageName = document.getElementById('modalImageName');
  const modalDownload = document.getElementById('modalDownload');

  // Collect all images from the gallery
  const imageCards = document.querySelectorAll('.photo-card');
  allImages = Array.from(imageCards).map(card => {
    const img = card.querySelector('img');
    const link = card.querySelector('a');
    const date = card.querySelector('.photo-date');
    return {
      thumb: img.src,
      full: link.href,
      alt: img.alt,
      name: img.alt,
      date: date ? date.textContent : ''
    };
  });

  // Add click handlers to all photo cards
  imageCards.forEach((card, index) => {
    const link = card.querySelector('a');
    if (link) {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        openModal(index);
      });
    }
  });

  function openModal(index) {
    currentImageIndex = index;
    updateModalContent();
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus management for accessibility
    modalClose.focus();
  }

  function closeModal() {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }

  function updateModalContent() {
    if (allImages.length === 0) return;
    
    const image = allImages[currentImageIndex];
    modalImage.src = image.full;
    modalImage.alt = image.alt;
    modalImageName.textContent = image.name;
    modalCounter.textContent = `${currentImageIndex + 1} von ${allImages.length}`;
    modalDownload.href = image.full;
    modalDownload.download = image.name;

    // Update navigation button states
    modalPrev.style.opacity = currentImageIndex === 0 ? '0.5' : '1';
    modalNext.style.opacity = currentImageIndex === allImages.length - 1 ? '0.5' : '1';
  }

  function showPrevImage() {
    if (currentImageIndex > 0) {
      currentImageIndex--;
      updateModalContent();
    }
  }

  function showNextImage() {
    if (currentImageIndex < allImages.length - 1) {
      currentImageIndex++;
      updateModalContent();
    }
  }

  // Event listeners
  modalClose.addEventListener('click', closeModal);
  modalPrev.addEventListener('click', showPrevImage);
  modalNext.addEventListener('click', showNextImage);

  // Close modal when clicking outside the image
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (modal.classList.contains('show')) {
      switch(e.key) {
        case 'Escape':
          closeModal();
          break;
        case 'ArrowLeft':
          showPrevImage();
          break;
        case 'ArrowRight':
          showNextImage();
          break;
      }
    }
  });

  // Touch/swipe support for mobile
  let touchStartX = 0;
  let touchEndX = 0;

  modal.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
  });

  modal.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  });

  function handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = touchEndX - touchStartX;
    
    if (Math.abs(swipeDistance) > swipeThreshold) {
      if (swipeDistance > 0) {
        showPrevImage(); // Swipe right = previous image
      } else {
        showNextImage(); // Swipe left = next image
      }
    }
  }

  // Preload adjacent images for smoother experience
  function preloadImages() {
    const preloadNext = currentImageIndex < allImages.length - 1 ? currentImageIndex + 1 : null;
    const preloadPrev = currentImageIndex > 0 ? currentImageIndex - 1 : null;
    
    [preloadNext, preloadPrev].forEach(index => {
      if (index !== null) {
        const img = new Image();
        img.src = allImages[index].full;
      }
    });
  }

  // Add image load event listener for preloading
  modalImage.addEventListener('load', preloadImages);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initImageModal();
});