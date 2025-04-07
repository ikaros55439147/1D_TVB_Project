// Toggle Login Modal
function toggleLogin() {
    const modal = document.getElementById('loginModal');
    if (modal.style.display === 'block') {
      modal.style.display = 'none';
    } else {
      modal.style.display = 'flex';
    }
  }
  
  // Close Modal on Click Outside
  window.onclick = function (event) {
    const modal = document.getElementById('loginModal');
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  };