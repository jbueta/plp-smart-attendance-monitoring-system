/* Event management functionality */

let selectionMode = false;

function toggleSelectionMode() {
    selectionMode = !selectionMode;
    const btn = document.getElementById('select-mode-btn');
    const bulkActions = document.getElementById('bulk-actions');
    const selectionCols = document.querySelectorAll('.selection-col');

    if (selectionMode) {
        btn.innerHTML = '<i class="bi bi-x-lg me-2"></i>Cancel';
        btn.classList.replace('btn-outline-light', 'btn-outline-danger');
        bulkActions.classList.remove('d-none');
        selectionCols.forEach(col => col.classList.remove('d-none'));
    } else {
        btn.innerHTML = '<i class="bi bi-check2-square me-2"></i>Select';
        btn.classList.replace('btn-outline-danger', 'btn-outline-light');
        bulkActions.classList.add('d-none');
        selectionCols.forEach(col => col.classList.add('d-none'));

        // Reset Selections
        document.querySelectorAll('.event-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all').checked = false;
        updateDeleteButton();
    }
}

function toggleSelectAll() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.event-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
    updateDeleteButton();
}

function updateDeleteButton() {
    const checkedCount = document.querySelectorAll('.event-checkbox:checked').length;
    const btn = document.getElementById('delete-selected-btn');
    const countSpan = document.getElementById('selected-count');

    if (countSpan) countSpan.textContent = checkedCount;
    if (btn) btn.disabled = checkedCount === 0;
}
