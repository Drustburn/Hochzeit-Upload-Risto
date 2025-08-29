document.addEventListener('DOMContentLoaded', function() {
  const uploadArea = document.querySelector('.file-upload-area');
  const fileInput = document.getElementById('fileInput');
  const fileList = document.getElementById('fileList');
  const uploadForm = document.querySelector('form[enctype="multipart/form-data"]');
  
  let selectedFiles = [];
  
  // Configuration loaded from template
  const config = window.uploadConfig || {
    maxFileSize: 32 * 1024 * 1024, // 32MB default
    allowedTypes: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    maxFileSizeMB: 32
  };
  
  // File input change handler
  if (fileInput) {
    fileInput.addEventListener('change', function(e) {
      handleFiles(e.target.files);
    });
  }
  
  // Drag and drop handlers
  if (uploadArea) {
    uploadArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      this.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
      e.preventDefault();
      this.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
      e.preventDefault();
      this.classList.remove('dragover');
      handleFiles(e.dataTransfer.files);
    });
  }
  
  // Handle selected files
  function handleFiles(files) {
    for (let file of files) {
      if (validateFile(file)) {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
          selectedFiles.push(file);
        }
      }
    }
    updateFileList();
    updateFileInput();
  }
  
  // Validate file
  function validateFile(file) {
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (!config.allowedTypes.includes(fileExt)) {
      showMessage('Dateityp nicht erlaubt: ' + file.name, 'error');
      return false;
    }
    
    if (file.size > config.maxFileSize) {
      showMessage('Datei zu groß: ' + file.name + ' (' + formatFileSize(file.size) + ')', 'error');
      return false;
    }
    
    return true;
  }
  
  // Update file list display
  function updateFileList() {
    if (!fileList) return;
    
    fileList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      fileItem.innerHTML = `
        <div class="file-info">
          <div class="file-icon">🖼️</div>
          <div class="file-details">
            <div class="file-name">${escapeHtml(file.name)}</div>
            <div class="file-size">${formatFileSize(file.size)}</div>
          </div>
        </div>
        <button type="button" class="file-remove" onclick="removeFile(${index})" title="Datei entfernen">×</button>
      `;
      fileList.appendChild(fileItem);
    });
  }
  
  // Remove file from selection
  window.removeFile = function(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateFileInput();
  };
  
  // Update hidden file input with selected files
  function updateFileInput() {
    if (!fileInput) return;
    
    const dt = new DataTransfer();
    selectedFiles.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;
  }
  
  // Format file size
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
  }
  
  // Show message
  function showMessage(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert' + (type === 'error' ? '' : ' success');
    alertDiv.textContent = message;
    
    const main = document.querySelector('main');
    if (main) {
      main.insertBefore(alertDiv, main.firstChild);
      setTimeout(() => alertDiv.remove(), 5000);
    }
  }
  
  // Form submission handler
  if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
      if (selectedFiles.length === 0) {
        e.preventDefault();
        showMessage('Bitte wählt mindestens eine Datei aus.', 'error');
        return;
      }
      
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.innerHTML = '💕 Wird hochgeladen...';
        submitBtn.disabled = true;
        
        // Add progress bar
        const progressDiv = document.createElement('div');
        progressDiv.innerHTML = `
          <div class="progress-bar">
            <div class="progress-fill"></div>
          </div>
          <div style="text-align: center; margin-top: 10px; font-size: 0.9rem; color: var(--wedding-accent);">
            Eure Fotos werden hochgeladen... ✨
          </div>
        `;
        submitBtn.parentNode.appendChild(progressDiv);
        
        // Simulate progress (since we can't track real progress easily)
        let progress = 0;
        const progressBar = progressDiv.querySelector('.progress-fill');
        const interval = setInterval(() => {
          progress += Math.random() * 20;
          if (progress > 90) progress = 90;
          progressBar.style.width = progress + '%';
        }, 200);
        
        // Clean up on form completion (this won't run due to redirect, but good practice)
        setTimeout(() => clearInterval(interval), 30000);
      }
    });
  }
});