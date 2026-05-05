// CodeLens — Client-side JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
        });
    });

    // Drag and drop
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        ['dragenter', 'dragover'].forEach(evt => {
            dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('dragover'); });
        });
        ['dragleave', 'drop'].forEach(evt => {
            dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('dragover'); });
        });
        dropZone.addEventListener('drop', e => {
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
        });
        document.getElementById('file-input')?.addEventListener('change', e => {
            if (e.target.files[0]) handleFile(e.target.files[0]);
        });
    }

    function handleFile(file) {
        const info = document.getElementById('file-info');
        if (info) {
            info.style.display = 'block';
            info.innerHTML = `📄 <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`;
        }
    }

    // Analyze button loading state
    const form = document.getElementById('review-form');
    if (form) {
        form.addEventListener('submit', () => {
            const btn = document.getElementById('analyze-btn');
            btn.textContent = '⏳ Analyzing...';
            btn.disabled = true;
        });
    }
});
