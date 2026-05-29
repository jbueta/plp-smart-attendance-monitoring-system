
document.addEventListener('DOMContentLoaded', function () {

    // ── Toast helper ───────────────────────────────────────────
    const TOAST_DURATION = 4000;

    function escapeToastHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function showToast(message, type = 'success', subtitle = '') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const id = 'toast-' + Date.now();
        const barId = id + '-bar';

        const cfg = {
            success: { icon: 'check-circle-fill',        iconBg: '#22c55e', border: 'rgba(34,197,94,0.35)',   barColor: '#22c55e', title: 'Success' },
            danger:  { icon: 'x-circle-fill',            iconBg: '#ef4444', border: 'rgba(239,68,68,0.35)',   barColor: '#ef4444', title: 'Error'   },
            warning: { icon: 'exclamation-circle-fill',   iconBg: '#f59e0b', border: 'rgba(245,158,11,0.35)', barColor: '#f59e0b', title: 'Warning' },
            info:    { icon: 'info-circle-fill',          iconBg: '#3b82f6', border: 'rgba(59,130,246,0.35)', barColor: '#3b82f6', title: 'Info'    }
        };

        const c   = cfg[type] || cfg.success;
        const sub = escapeToastHtml(subtitle || message);

        const html = `
            <div id="${id}" style="
                position: relative; overflow: hidden;
                display: flex; align-items: flex-start; gap: 14px;
                width: min(520px, calc(100vw - 32px));
                padding: 18px 18px 24px;
                border-radius: 18px;
                background: rgba(8, 32, 20, 0.98);
                border: 1px solid ${c.border};
                box-shadow: 0 24px 60px rgba(0,0,0,0.65);
                backdrop-filter: blur(20px);
                animation: toastSlideIn 0.32s cubic-bezier(0.34,1.56,0.64,1) forwards;
                pointer-events: auto;
            ">
                <div style="
                    width:46px; height:46px; border-radius:50%; flex-shrink:0;
                    background:${c.iconBg};
                    display:flex; align-items:center; justify-content:center;
                    box-shadow: 0 0 0 7px ${c.iconBg}28;
                ">
                    <i class="bi bi-${c.icon}" style="font-size:1.25rem; color:#fff;"></i>
                </div>

                <div style="flex:1; min-width:0;">
                    <div style="font-weight:700; font-size:0.95rem; color:#fff; margin-bottom:3px; letter-spacing:0.01em;">${c.title}</div>
                    <div style="
                        font-size:0.84rem;
                        color:rgba(255,255,255,0.74);
                        line-height:1.45;
                        white-space:pre-wrap;
                        overflow-wrap:anywhere;
                        word-break:break-word;
                    ">${sub}</div>
                </div>

                <button onclick="
                    const el = document.getElementById('${id}');
                    if (!el) return;
                    el.style.animation = 'toastSlideOut 0.22s ease forwards';
                    setTimeout(() => el?.remove(), 230);
                " style="
                    background:none; border:none; cursor:pointer; padding:0; line-height:1; flex-shrink:0;
                    color:rgba(255,255,255,0.35); font-size:0.9rem; transition:color 0.15s;
                " onmouseover="this.style.color='#fff'" onmouseout="this.style.color='rgba(255,255,255,0.35)'">
                    <i class="bi bi-x-lg"></i>
                </button>

                <div id="${barId}" style="
                    position:absolute; bottom:0; left:0; height:3px;
                    width:100%; border-radius:0 0 18px 18px;
                    background:${c.barColor};
                    transition: width ${TOAST_DURATION}ms linear;
                "></div>
            </div>`;

        container.insertAdjacentHTML('beforeend', html);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                const bar = document.getElementById(barId);
                if (bar) bar.style.width = '0%';
            });
        });

        setTimeout(() => {
            const el = document.getElementById(id);
            if (!el) return;
            el.style.animation = 'toastSlideOut 0.22s ease forwards';
            setTimeout(() => el?.remove(), 230);
        }, TOAST_DURATION);
    }

    // ── Confirm dialog helper ──────────────────────────────────
    function showConfirm(title, subtitle = '') {
        return new Promise(resolve => {
            const overlay = document.getElementById('confirmOverlay');
            const titleEl = document.getElementById('confirmTitle');
            const subEl = document.getElementById('confirmSubtitle');
            const okBtn = document.getElementById('confirmOkBtn');
            const cancelBtn = document.getElementById('confirmCancelBtn');

            titleEl.textContent = title;
            subEl.textContent = subtitle;

            overlay.classList.remove('d-none');
            overlay.style.display = 'flex';

            function cleanup(result) {
                overlay.style.display = 'none';
                overlay.classList.add('d-none');
                okBtn.replaceWith(okBtn.cloneNode(true));
                cancelBtn.replaceWith(cancelBtn.cloneNode(true));
                resolve(result);
            }

            document.getElementById('confirmOkBtn').addEventListener('click', () => cleanup(true));
            document.getElementById('confirmCancelBtn').addEventListener('click', () => cleanup(false));
            overlay.addEventListener('click', e => { if (e.target === overlay) cleanup(false); }, { once: true });
        });
    }

    async function parseApiResponseSafe(response) {
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            try { return await response.json(); } catch (_) { return null; }
        }
        try {
            const text = (await response.text() || '').trim();
            if (!text) return null;
            const titleMatch = text.match(/<title>(.*?)<\/title>/i);
            const bodyMatch = text.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
            const extracted = (titleMatch && titleMatch[1]) || (bodyMatch && bodyMatch[1]) || text;
            const plainText = extracted.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
            return plainText ? { error: plainText } : null;
        } catch (_) { return null; }
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    const ITEMS_PER_PAGE = 9;

    // ── Element refs ───────────────────────────────────────────
    const addUserModalEl   = document.getElementById('addUserModal');
    const selectionView    = document.getElementById('addSelectionView');
    const xlsView          = document.getElementById('xlsUploadView');
    const manualView       = document.getElementById('manualAddView');
    const xlsCard          = document.querySelector('.xls-card');
    const manualCard       = document.querySelector('.manual-card');
    const backBtns         = document.querySelectorAll('.btn-back-selection');
    const uploadZone       = document.querySelector('.upload-zone');
    const xlsFileInput     = document.getElementById('xlsFileInput');
    const exportBtn        = document.getElementById('exportStudentsBtn');

    // Manual-add form fields
    const manualIdInput    = document.getElementById('manualAddId');
    const manualNameInput  = document.getElementById('manualAddName');
    const manualCourse     = document.getElementById('manualAddCourse');
    const manualTypeInput  = document.getElementById('manualAddStudentType');
    const submitManualBtn  = document.getElementById('submitManualAddBtn');

    // Activity-log filter elements
    const searchInput         = document.getElementById('searchInput');
    const dateFilter          = document.getElementById('dateFilter');
    const tableCard           = document.getElementById('tableCard');
    const activityTableResponsive = tableCard ? tableCard.querySelector('.table-responsive') : null;
    const noResults           = document.getElementById('noResults');
    const resultCount         = document.getElementById('resultCount');
    const paginationContainer = document.getElementById('paginationContainer');
    const paginationList      = document.getElementById('paginationList');

    // Records filter elements
    const recordsSearch              = document.getElementById('recordsSearchInput');
    const recordsTableCard           = document.getElementById('recordsTableCard');
    const recordsTableResponsive     = recordsTableCard ? recordsTableCard.querySelector('.table-responsive') : null;
    const recordsTableBody           = document.getElementById('recordsTableBody');
    const recordsNoResults           = document.getElementById('recordsNoResults');
    const recordsResultCount         = document.getElementById('recordsResultCount');
    const recordsPaginationContainer = document.getElementById('recordsPaginationContainer');
    const recordsPaginationList      = document.getElementById('recordsPaginationList');

    // Custom Dropdown State Values
    let logStatusFilterValue = '';
    let courseFilterValue = '';
    
    let recordsCourseFilterValue = '';
    let recordsStatusFilterValue = 'all';
    let recordsTypeFilterValue = '';
    let recordsSortFilterValue = 'recent';

    // Edit overlay
    const editOverlay     = document.getElementById('editOverlay');
    const editStudentId   = document.getElementById('editStudentId');
    const editStudentName = document.getElementById('editStudentName');
    const editCourseId    = document.getElementById('editCourseId');
    const saveStudentEdit = document.getElementById('saveStudentEdit');
    const cancelEdit      = document.getElementById('cancelEditStudent');

    let currentPage        = 1;
    let recordsCurrentPage = 1;
    let currentEditRow     = null;
    let uploadPreviewRows  = [];
    let refreshOnUploadModalClose = false;

    // ── Helpers ────────────────────────────────────────────────
    const getActivityRows = () => document.querySelectorAll('.student-row');
    const getRecordRows   = () => document.querySelectorAll('.student-record-row');

    function showView(target) {
        [selectionView, xlsView, manualView].forEach(v => v && v.classList.add('d-none'));
        if (target) {
            target.classList.remove('d-none');
            target.style.animation = 'fadeInModal 0.4s ease forwards';
        }
    }

    // ── Custom Dropdown Binder Helpers ─────────────────────────
    function bindActivityCourseFilters() {
        document.querySelectorAll('.course-filter-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                courseFilterValue = e.target.dataset.value;
                document.getElementById('courseFilterLabel').textContent = e.target.textContent;
                document.querySelectorAll('.course-filter-option').forEach(o => o.classList.remove('active'));
                e.target.classList.add('active');
                applyFilters();
            });
        });
    }

    function bindRecordsCourseFilters() {
        document.querySelectorAll('.records-course-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                recordsCourseFilterValue = e.target.dataset.value;
                document.getElementById('recordsCourseFilterLabel').textContent = e.target.textContent;
                document.querySelectorAll('.records-course-option').forEach(o => o.classList.remove('active'));
                e.target.classList.add('active');
                applyRecordsFilter();
            });
        });
    }

    // Bind static status/sort options
    document.querySelectorAll('.log-status-option').forEach(opt => {
        opt.addEventListener('click', (e) => {
            logStatusFilterValue = e.target.dataset.value;
            document.getElementById('logStatusFilterLabel').textContent = e.target.textContent;
            document.querySelectorAll('.log-status-option').forEach(o => o.classList.remove('active'));
            e.target.classList.add('active');
            applyFilters();
        });
    });

    document.querySelectorAll('.records-status-option').forEach(opt => {
        opt.addEventListener('click', (e) => {
            recordsStatusFilterValue = e.target.dataset.value;
            document.getElementById('recordsStatusFilterLabel').textContent = e.target.textContent;
            document.querySelectorAll('.records-status-option').forEach(o => o.classList.remove('active'));
            e.target.classList.add('active');
            applyRecordsFilter();
        });
    });

    document.querySelectorAll('.records-type-option').forEach(opt => {
        opt.addEventListener('click', (e) => {
            recordsTypeFilterValue = e.target.dataset.value;
            document.getElementById('recordsTypeFilterLabel').textContent = e.target.textContent;
            document.querySelectorAll('.records-type-option').forEach(o => o.classList.remove('active'));
            e.target.classList.add('active');
            applyRecordsFilter();
        });
    });

    document.querySelectorAll('.records-sort-option').forEach(opt => {
        opt.addEventListener('click', (e) => {
            recordsSortFilterValue = e.target.dataset.value;
            document.getElementById('recordsSortFilterLabel').textContent = e.target.textContent;
            document.querySelectorAll('.records-sort-option').forEach(o => o.classList.remove('active'));
            e.target.classList.add('active');
            applyRecordsFilter();
        });
    });

    // ── Course loading ─────────────────────────────────────────
    async function loadCourseFilters() {
        try {
            const res = await fetch('/get_courses');
            const courses = await res.json();

            const courseMenu = document.getElementById('courseFilterMenu');
            if (courseMenu) {
                courseMenu.innerHTML = '<li><button type="button" class="dropdown-item course-filter-option active text-white" data-value="">All Courses</button></li>';
                courses.forEach(c => {
                    const li = document.createElement('li');
                    li.innerHTML = `<button type="button" class="dropdown-item course-filter-option text-white" data-value="${(c.name || '').toLowerCase()}">${c.course_name || c.name || ''}</button>`;
                    courseMenu.appendChild(li);
                });
                bindActivityCourseFilters();
            }

            const recordsCourseMenu = document.getElementById('recordsCourseFilterMenu');
            if (recordsCourseMenu) {
                recordsCourseMenu.innerHTML = '<li><button type="button" class="dropdown-item records-course-option active text-white" data-value="">All Courses</button></li>';
                courses.forEach(c => {
                    const li = document.createElement('li');
                    li.innerHTML = `<button type="button" class="dropdown-item records-course-option text-white" data-value="${(c.name || '').toLowerCase()}">${c.course_name || c.name || ''}</button>`;
                    recordsCourseMenu.appendChild(li);
                });
                bindRecordsCourseFilters();
            }

            const editCourseDropdown = document.getElementById('editCourseId');
            if (editCourseDropdown) {
                editCourseDropdown.innerHTML = '<option value="" disabled>- Select Course -</option>';
                courses.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = String(c.course_id);
                    opt.textContent = c.course_name || c.name || '';
                    opt.dataset.name = c.course_name || c.name || '';
                    opt.className = 'text-dark';
                    editCourseDropdown.appendChild(opt);
                });
            }
        } catch (err) {
            console.error('Failed to load course filters:', err);
        }
    }

    async function loadManualCourses() {
        try {
            const res     = await fetch('/get_courses');
            const courses = await res.json();
            manualCourse.innerHTML = '<option value="" selected disabled>— Select Course —</option>';
            courses.forEach(c => {
                const opt        = document.createElement('option');
                opt.value        = c.course_id;
                opt.textContent  = c.course_name;
                opt.dataset.name = c.course_name;
                opt.className    = 'text-dark';
                manualCourse.appendChild(opt);
            });
        } catch (err) { console.error('Failed to load courses:', err); }
    }

    // ── Manual-add refs (grabbed after HTML is ready) ──────────
    const idFeedback    = document.getElementById('idFeedback');
    const manualAlert   = document.getElementById('manualAddAlert');
    const saveBtnLabel  = document.getElementById('saveBtnLabel');
    const saveBtnSpinner = document.getElementById('saveBtnSpinner');

    function showManualAlert(msg, type = 'danger') {
        if (!manualAlert) return;
        manualAlert.textContent  = msg;
        manualAlert.className    = `rounded-3 px-3 py-2 mb-3 small fw-semibold bg-${type} bg-opacity-25 text-${type === 'danger' ? 'danger' : 'success'} border border-${type === 'danger' ? 'danger' : 'success'}`;
    }

    function hideManualAlert() {
        if (manualAlert) manualAlert.className = 'd-none';
    }

    function setSaveBtnLoading(loading) {
        if (!submitManualBtn) return;
        submitManualBtn.disabled = loading;
        saveBtnLabel?.classList.toggle('d-none', loading);
        saveBtnSpinner?.classList.toggle('d-none', !loading);
    }

    function formatStudentIdValue(value) {
        const digits = String(value || '').replace(/\D/g, '').slice(0, 7);
        if (digits.length <= 2) return digits;
        return `${digits.slice(0, 2)}-${digits.slice(2)}`;
    }

    function applyStudentIdMask() {
        if (!manualIdInput) return;

        const rawValue = manualIdInput.value || '';
        const selectionStart = manualIdInput.selectionStart ?? rawValue.length;
        const digitsBeforeCursor = rawValue
            .slice(0, selectionStart)
            .replace(/\D/g, '')
            .slice(0, 7).length;
        const formatted = formatStudentIdValue(rawValue);

        manualIdInput.value = formatted;

        const nextCursor = digitsBeforeCursor <= 2
            ? digitsBeforeCursor
            : Math.min(formatted.length, digitsBeforeCursor + 1);

        requestAnimationFrame(() => {
            manualIdInput.setSelectionRange(nextCursor, nextCursor);
        });
    }

    // ── Manual-add validation ──────────────────────────────────
    function validateManualForm() {
        const idVal     = (manualIdInput?.value   || '').trim();
        const nameVal   = (manualNameInput?.value || '').trim();
        const courseVal = manualCourse?.value    || '';
        const typeVal   = manualTypeInput?.value || '';

        const idOk     = /^\d{2}-\d{5}$/.test(idVal);
        const nameOk   = nameVal.length > 0;
        const courseOk = courseVal !== '';
        const typeOk   = typeVal !== '';

        if (idFeedback) {
            idFeedback.classList.toggle('d-none', idVal.length === 0 || idOk);
        }

        if (submitManualBtn) {
            submitManualBtn.disabled = !(idOk && nameOk && courseOk && typeOk);
        }
    }

    if (manualIdInput) {
        manualIdInput.addEventListener('input', () => {
            applyStudentIdMask();
            validateManualForm();
        });
    }
    if (manualNameInput) manualNameInput.addEventListener('input', validateManualForm);
    if (manualCourse)    manualCourse.addEventListener('change',   validateManualForm);
    if (manualTypeInput) manualTypeInput.addEventListener('change',   validateManualForm);

    // ── Modal navigation ───────────────────────────────────────
    if (xlsCard)    xlsCard.addEventListener('click',   () => showView(xlsView));
    if (manualCard) manualCard.addEventListener('click', () => { hideManualAlert(); showView(manualView); });
    backBtns.forEach(btn => btn.addEventListener('click', () => { hideManualAlert(); showView(selectionView); }));

    if (addUserModalEl) {
        addUserModalEl.addEventListener('hidden.bs.modal', () => {
            showView(selectionView);
            hideManualAlert();
            if (xlsFileInput) {
                xlsFileInput.value = '';
                const span = uploadZone?.querySelector('span');
                const icon = uploadZone?.querySelector('i');
                if (span) span.textContent = 'Click to upload an Excel or CSV file';
                if (icon) icon.className = 'bi bi-file-earmark-spreadsheet display-4 text-white-50 mb-3';
            }
            if (manualIdInput)    manualIdInput.value = '';
            if (manualNameInput)  manualNameInput.value = '';
            if (manualCourse)     manualCourse.selectedIndex = 0;
            if (manualTypeInput)  manualTypeInput.selectedIndex = 0;
        });
    }

    // ── Manual Add ─────────────────────────────────────────────
    if (submitManualBtn) {
        submitManualBtn.addEventListener('click', async () => {
            const student_id   = (manualIdInput?.value   || '').trim();
            const student_name = (manualNameInput?.value || '').trim();
            const course_id    = manualCourse?.value || '';
            const selectedCourseName = manualCourse?.selectedOptions?.[0]?.textContent?.trim() || '';

            if (!student_id || !student_name || !course_id) {
                showManualAlert('Please fill in all fields before saving.', 'danger');
                return;
            }

            hideManualAlert();
            setSaveBtnLoading(true);

            try {
                const student_type = (manualTypeInput?.value || '').trim();
                const res = await fetch('/add_student_manual', {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body:    JSON.stringify({
                        student_id,
                        student_name,
                        student_type,
                        course_id,
                        status: 'Outside'
                    })
                });

                const result = await parseApiResponseSafe(res);

                if (res.ok && result && result.success) {
                    const resolvedCourseName = (result.course_name || selectedCourseName || '').trim();
                    const tbody = document.getElementById('recordsTableBody');
                    const empty = document.getElementById('recordsEmptyRow');
                    if (empty) empty.remove();

                    if (tbody) {
                        const student_type_class = student_type.toLowerCase() === 'irregular' ? 'warning' : 'success';
                        const tr = document.createElement('tr');
                        tr.className        = 'student-record-row';
                        tr.dataset.id       = student_id.toLowerCase();
                        tr.dataset.name     = student_name.toLowerCase();
                        tr.dataset.course   = resolvedCourseName.toLowerCase();
                        tr.dataset.type     = student_type.toLowerCase();
                        tr.dataset.status   = 'active';
                        tr.innerHTML = `
                            <td class="font-monospace text-white-50 ps-4">${student_id}</td>
                            <td class="fw-bold text-white">${student_name.toUpperCase()}</td>
                            <td class="text-white-50">${resolvedCourseName}</td>
                            <td class="text-center">
                                <span class="badge bg-${student_type_class} bg-opacity-25 border border-${student_type_class} text-${student_type_class} rounded-pill px-3">${student_type}</span>
                            </td>
                            <td class="text-center">
                                <span class="badge bg-success bg-opacity-25 border border-success text-success rounded-pill px-3">Active</span>
                            </td>
                            <td class="text-center align-middle pe-4" style="width:80px;">
                                <div class="dropdown h-100 d-flex align-items-center justify-content-center">
                                    <button class="btn btn-sm btn-outline-light p-0 border-0 d-flex align-items-center justify-content-center fs-4 action-dots"
                                        type="button" data-bs-toggle="dropdown" aria-expanded="false" data-bs-boundary="window"><i class="bi bi-three-dots"></i></button>
                                    <ul class="dropdown-menu dropdown-menu-end shadow-sm student-action-menu">
                                        <li><button type="button" class="dropdown-item edit-student-record text-white"
                                            data-id="${student_id}">Edit</button></li>
                                        <li><button type="button" class="dropdown-item text-danger delete-student-record"
                                            data-id="${student_id}">Delete</button></li>
                                    </ul>
                                </div>
                            </td>`;
                        tbody.appendChild(tr);
                        applyRecordsFilter();
                    }

                    bootstrap.Modal.getInstance(document.getElementById('addUserModal'))?.hide();

                    const recRadio = document.getElementById('viewRecords');
                    if (recRadio) { recRadio.checked = true; recRadio.dispatchEvent(new Event('change')); }

                    showToast(
                        result.reactivated ? 'Student reactivated successfully.' : 'Student added successfully.',
                        'success',
                        result.reactivated
                            ? `${student_name.toUpperCase()} was reactivated.`
                            : `${student_name.toUpperCase()} has been added to records.`
                    );
                    setTimeout(() => location.reload(), 1500);

                } else {
                    showManualAlert((result && result.error) || 'Failed to add student. Please try again.', 'danger');
                }

            } catch (err) {
                console.error('Manual add error:', err);
                showManualAlert('Server error. Please check your connection and try again.', 'danger');
            } finally {
                setSaveBtnLoading(false);
                validateManualForm();
            }
        });
    }

    // ── XLS Export/Upload ──────────────────────────────────────
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            if (!xlsFileInput?.files?.length) {
                showToast('No file selected', 'warning', 'Please choose an Excel or CSV file first.');
                return;
            }

            exportBtn.disabled = true;
            const origLabel = exportBtn.textContent;
            exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Uploading…';

            const formData = new FormData();
            formData.append('file', xlsFileInput.files[0]);

            try {
                const res = await fetch('/upload_students/preview', { method: 'POST', body: formData });
                const result = await parseApiResponseSafe(res);

                if (res.ok && result && result.success) {
                    uploadPreviewRows = result.preview_rows || [];
                    renderUploadPreviewModal(result);
                } else {
                    const message = (result && (result.error || (result.errors && result.errors.join('\n'))))
                        || 'Validation failed. Please check the file format and required columns, then try again.';
                    showToast('Validation failed', 'danger', message);
                }
            } catch (err) {
                console.error(err);
                showToast('Validation failed', 'danger', 'Could not validate the file. Please try again.');
            } finally {
                exportBtn.disabled = false;
                exportBtn.textContent = origLabel || 'VALIDATE FILE';
            }
        });
    }

    function renderUploadPreviewModal(result) {
        const resultModalEl = document.getElementById('uploadResultModal');
        const resultModal = new bootstrap.Modal(resultModalEl);
        const title = document.getElementById('uploadResultTitle');
        const subtitle = document.getElementById('uploadResultSubtitle');
        const content = document.getElementById('uploadResultContent');
        const tipContainer = document.getElementById('uploadResultTipContainer');
        const iconContainer = document.getElementById('uploadResultIconContainer');
        const icon = document.getElementById('uploadResultIcon');
        const footer = document.getElementById('uploadResultFooter');

        iconContainer.style.background = 'rgba(13, 202, 240, 0.15)';
        icon.className = 'bi bi-table text-info fs-4';
        title.textContent = 'Review Student Upload';
        subtitle.textContent = `${uploadPreviewRows.length} valid row(s) ready to upload`;

        const requiredBadges = (result.required_columns || [])
            .map(column => `<span class="badge rounded-pill px-3 py-2 me-1 mb-1" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); color: #fff;">${escapeHtml(column)}</span>`)
            .join('');
        const optionalBadges = (result.optional_columns || [])
            .map(column => `<span class="badge rounded-pill px-3 py-2 me-1 mb-1" style="background: rgba(212,175,55,0.15); border: 1px solid rgba(212,175,55,0.35); color: #f1d582;">${escapeHtml(column)} (OPTIONAL)</span>`)
            .join('');

        const previewRowsHtml = uploadPreviewRows.length
            ? uploadPreviewRows.map((row, index) => `
                <tr>
                    <td class="text-white-50">${escapeHtml(row.row_number)}</td>
                    <td class="text-white">${escapeHtml(row.student_id)}</td>
                    <td class="text-white">${escapeHtml(row.student_name)}</td>
                    <td class="text-white-50">${escapeHtml(row.course_name)}</td>
                    <td class="text-white-50">${escapeHtml(row.status || 'Outside')}</td>
                    <td class="text-white-50">${row.action === 'reactivate' ? 'Reactivate existing student' : 'Create new student'}</td>
                    <td class="text-end">
                        <button type="button" class="btn btn-sm btn-outline-danger delete-preview-row" data-index="${index}">Delete</button>
                    </td>
                </tr>
            `).join('')
            : '<tr><td colspan="7" class="text-center text-white-50 py-4">No rows left to upload.</td></tr>';

        const validationErrors = (result.errors || []).length
            ? `
                <div class="mt-3">
                    <div class="fw-bold text-warning mb-2">Rows skipped during validation</div>
                    <ul class="list-unstyled mb-0" style="font-size: 0.88rem;">
                        ${result.errors.map(error => `<li class="mb-2 text-white-50"><i class="bi bi-exclamation-triangle-fill text-warning me-2"></i>${escapeHtml(error)}</li>`).join('')}
                    </ul>
                </div>
            `
            : '';

        tipContainer.innerHTML = `
            <div class="alert border-0 rounded-4 mb-3 px-4 py-3" style="background: rgba(13, 202, 240, 0.10); border: 1px solid rgba(13,202,240,0.25) !important;">
                <div class="d-flex gap-3 align-items-start">
                    <i class="bi bi-info-circle-fill fs-5 mt-1 text-info"></i>
                    <div>
                        <strong class="d-block mb-2 text-info">Required Upload Structure</strong>
                        <div class="mb-2">${requiredBadges}</div>
                        <div>${optionalBadges}</div>
                    </div>
                </div>
            </div>
        `;

        content.innerHTML = `
            <div class="table-responsive">
                <table class="table table-dark-glass table-sm align-middle mb-0">
                    <thead>
                        <tr>
                            <th>Row</th>
                            <th>Student ID</th>
                            <th>Student Name</th>
                            <th>Course</th>
                            <th>Status</th>
                            <th>Result</th>
                            <th class="text-end">Action</th>
                        </tr>
                    </thead>
                    <tbody>${previewRowsHtml}</tbody>
                </table>
            </div>
            ${validationErrors}
        `;

        footer.innerHTML = `
            <button type="button" class="btn btn-outline-light px-4 rounded-pill" data-bs-dismiss="modal">Back</button>
            <button type="button" class="btn btn-primary-gold px-4 rounded-pill" id="confirmUploadPreviewBtn" ${uploadPreviewRows.length ? '' : 'disabled'}>Upload Selected Rows</button>
        `;

        const addModal = bootstrap.Modal.getInstance(addUserModalEl);
        if (addModal) addModal.hide();
        resultModal.show();
    }

    async function commitPreviewRows() {
        if (!uploadPreviewRows.length) {
            showToast('No rows left to upload.', 'warning');
            return;
        }

        const confirmBtn = document.getElementById('confirmUploadPreviewBtn');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Uploading...';
        }

        try {
            const res = await fetch('/upload_students/commit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rows: uploadPreviewRows })
            });
            const result = await parseApiResponseSafe(res);

            const title = document.getElementById('uploadResultTitle');
            const subtitle = document.getElementById('uploadResultSubtitle');
            const content = document.getElementById('uploadResultContent');
            const tipContainer = document.getElementById('uploadResultTipContainer');
            const iconContainer = document.getElementById('uploadResultIconContainer');
            const icon = document.getElementById('uploadResultIcon');
            const footer = document.getElementById('uploadResultFooter');

            if (res.ok && result && result.success) {
                iconContainer.style.background = 'rgba(25,135,84,0.15)';
                icon.className = 'bi bi-check-circle-fill text-success fs-4';
                const inserted = result.inserted || 0;
                const reactivated = result.reactivated || 0;
                title.textContent = inserted + reactivated > 0 ? 'Upload Successful' : 'Upload Completed With No Changes';
                subtitle.textContent = `${inserted} added, ${reactivated} reactivated`;
                tipContainer.innerHTML = '';
                content.innerHTML = result.errors && result.errors.length
                    ? `<ul class="list-unstyled mb-0">${result.errors.map(error => `<li class="mb-2 text-white-50"><i class="bi bi-exclamation-circle text-warning me-2"></i>${escapeHtml(error)}</li>`).join('')}</ul>`
                    : '<div class="text-center py-2 text-white">All selected rows were processed successfully.</div>';
                footer.innerHTML = '<button type="button" class="btn btn-outline-light px-4 rounded-pill" data-bs-dismiss="modal">Close</button>';
                refreshOnUploadModalClose = true;
            } else {
                iconContainer.style.background = 'rgba(220,53,69,0.15)';
                icon.className = 'bi bi-x-circle-fill text-danger fs-4';
                title.textContent = 'Upload Failed';
                subtitle.textContent = 'Could not save selected rows';
                tipContainer.innerHTML = '';
                content.innerHTML = `<div class="text-danger"><i class="bi bi-exclamation-triangle me-2"></i>${escapeHtml((result && result.error) || 'Unknown upload error')}</div>`;
                footer.innerHTML = `
                    <button type="button" class="btn btn-primary-gold px-4 rounded-pill" id="retryUploadPreviewBtn">Try Again</button>
                    <button type="button" class="btn btn-outline-light px-4 rounded-pill" data-bs-dismiss="modal">Close</button>
                `;
                refreshOnUploadModalClose = false;
            }
        } catch (err) {
            showToast('Upload failed. Please try again.', 'danger');
        } finally {
            const retryConfirmBtn = document.getElementById('confirmUploadPreviewBtn');
            if (retryConfirmBtn) {
                retryConfirmBtn.disabled = false;
                retryConfirmBtn.textContent = 'Upload Selected Rows';
            }
        }
    }

    document.addEventListener('click', function (event) {
        const deletePreviewBtn = event.target.closest('.delete-preview-row');
        if (deletePreviewBtn) {
            const index = Number(deletePreviewBtn.dataset.index);
            if (!Number.isNaN(index)) {
                uploadPreviewRows.splice(index, 1);
                renderUploadPreviewModal({
                    required_columns: ['STUDENT ID', 'STUDENT NAME'],
                    optional_columns: ['COURSE', 'COURSE ID', 'STATUS'],
                    errors: []
                });
            }
            return;
        }

        if (event.target.closest('#confirmUploadPreviewBtn')) {
            commitPreviewRows();
            return;
        }

        if (event.target.closest('#retryUploadPreviewBtn')) {
            commitPreviewRows();
        }
    });

    const uploadResultModalEl = document.getElementById('uploadResultModal');
    if (uploadResultModalEl) {
        uploadResultModalEl.addEventListener('hidden.bs.modal', () => {
            if (refreshOnUploadModalClose) {
                refreshOnUploadModalClose = false;
                location.reload();
            }
        });
    }

    const views = {
        activity: document.getElementById('activity-view'),
        records:  document.getElementById('records-view')
    };

    document.querySelectorAll('.view-toggle').forEach(radio => {
        radio.addEventListener('change', function (e) {
            Object.values(views).forEach(v => v?.classList.remove('active-view'));
            views[e.target.value]?.classList.add('active-view');
            history.replaceState(null, null, '#' + e.target.value);
        });
    });

    function handleHash() {
        const hash  = window.location.hash.replace('#', '');
        const radio = document.getElementById('view' + hash.charAt(0).toUpperCase() + hash.slice(1));
        if (radio) { radio.checked = true; radio.dispatchEvent(new Event('change')); }
    }
    window.addEventListener('hashchange', handleHash);
    handleHash();

    function buildPagination(list, curPage, totalPages, onPageClick) {
        list.innerHTML = '';
        if (totalPages <= 1) return false;

        const mkBtn = (label, cls, disabled, onClick) => {
            const li = document.createElement('li');
            li.className = 'page-item';
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `page-link ${cls}`;
            btn.innerHTML = label;
            if (disabled) btn.disabled = true;
            else btn.addEventListener('click', onClick);
            li.appendChild(btn);
            list.appendChild(li);
            return btn;
        };

        mkBtn('<i class="bi bi-chevron-left me-1"></i>Previous', 'page-prev', curPage === 1,
            () => onPageClick(curPage - 1));

        let start = 1;
        let end = totalPages;
        if (totalPages > 5) {
            start = Math.max(1, curPage - 2);
            end = Math.min(totalPages, start + 4);
            if (end - start < 4) start = Math.max(1, end - 4);
        }

        for (let i = start; i <= end; i++) {
            mkBtn(i, `page-number ${i === curPage ? 'active' : ''}`, false, () => onPageClick(i));
        }

        if (end < totalPages) {
            const li = document.createElement('li');
            li.className = 'page-item';
            const sp = document.createElement('span');
            sp.className = 'page-link page-number-separator';
            sp.textContent = '...';
            li.appendChild(sp);
            list.appendChild(li);
            mkBtn(totalPages, 'page-number', false, () => onPageClick(totalPages));
        }

        mkBtn('Next <i class="bi bi-chevron-right ms-1"></i>', 'page-next', curPage === totalPages,
            () => onPageClick(curPage + 1));

        return true;
    }

    function getActivityVisibleRows() {
        return Array.from(getActivityRows()).filter(row => row.dataset.filterVisible !== 'false');
    }

    function updateActivityDisplay() {
        const visible = getActivityVisibleRows();
        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        getActivityRows().forEach(row => {
            if (row.dataset.filterVisible === 'false') {
                row.style.display = 'none';
                return;
            }
            const idx = visible.indexOf(row);
            row.style.display = (idx >= startIdx && idx < startIdx + ITEMS_PER_PAGE) ? '' : 'none';
        });
    }

    function renderActivityPagination(count) {
        const built = buildPagination(paginationList, currentPage, Math.ceil(count / ITEMS_PER_PAGE),
            page => { currentPage = page; updateActivityDisplay(); renderActivityPagination(count); });
        if (built) {
            paginationContainer.classList.add('show');
            paginationContainer.style.display = 'flex';
        } else {
            paginationContainer.classList.remove('show');
            paginationContainer.style.display = 'none';
        }
    }

    function applyFilters() {
        const search = (searchInput?.value || '').trim().toLowerCase();
        const logStatus = logStatusFilterValue;
        const course = courseFilterValue;
        const date = dateFilter?.value || '';
        let visible = 0;

        getActivityRows().forEach(row => {
            const statusCell = row.querySelector('td:nth-child(6)')?.textContent.toLowerCase() || '';
            const matchStatus = !logStatus || (logStatus === 'inside' && statusCell.includes('inside'));

            const ok = (!search || row.dataset.id.includes(search) || row.dataset.name.includes(search))
                && (!course || row.dataset.course === course)
                && (!date || row.dataset.date === date)
                && matchStatus;
            row.dataset.filterVisible = ok ? 'true' : 'false';
            if (ok) visible += 1;
        });

        currentPage = 1;
        const hasFilters = search || course || date || logStatus;

        if (getActivityRows().length === 0) {
            if (activityTableResponsive) activityTableResponsive.style.display = '';
            noResults.style.display = 'none';
            resultCount.textContent = '';
            paginationContainer.classList.remove('show');
            paginationContainer.style.display = 'none';
            return;
        }

        if (visible === 0 && hasFilters) {
            if (activityTableResponsive) activityTableResponsive.style.display = 'none';
            noResults.style.display = 'block';
            resultCount.textContent = '';
            paginationContainer.classList.remove('show');
            paginationContainer.style.display = 'none';
            return;
        }

        if (activityTableResponsive) activityTableResponsive.style.display = '';
        noResults.style.display = 'none';
        resultCount.textContent = hasFilters
            ? `Showing up to ${Math.min(ITEMS_PER_PAGE, visible)} of ${visible} record${visible !== 1 ? 's' : ''}`
            : '';
        updateActivityDisplay();
        renderActivityPagination(visible);
    }

    searchInput?.addEventListener('input', applyFilters);
    dateFilter?.addEventListener('change', applyFilters);

    function getRecordsVisibleRows() {
        return Array.from(getRecordRows()).filter(row => row.dataset.filterVisible !== 'false');
    }

    function updateRecordsDisplay() {
        const visible = getRecordsVisibleRows();
        const startIdx = (recordsCurrentPage - 1) * ITEMS_PER_PAGE;
        getRecordRows().forEach(row => {
            if (row.dataset.filterVisible === 'false') {
                row.style.display = 'none';
                return;
            }
            const idx = visible.indexOf(row);
            row.style.display = (idx >= startIdx && idx < startIdx + ITEMS_PER_PAGE) ? '' : 'none';
        });
    }

    function renderRecordsPagination(count) {
        const built = buildPagination(recordsPaginationList, recordsCurrentPage, Math.ceil(count / ITEMS_PER_PAGE),
            page => { recordsCurrentPage = page; updateRecordsDisplay(); renderRecordsPagination(count); });
        if (built) {
            recordsPaginationContainer.classList.add('show');
            recordsPaginationContainer.style.display = 'flex';
        } else {
            recordsPaginationContainer.classList.remove('show');
            recordsPaginationContainer.style.display = 'none';
        }
    }

    function sortRecordsRows() {
        if (!recordsTableBody) return;

        const sortValue = recordsSortFilterValue;
        const rows = Array.from(getRecordRows());
        const compareText = (left, right) => left.localeCompare(right, undefined, { sensitivity: 'base' });

        rows.sort((rowA, rowB) => {
            const nameA = rowA.dataset.name || '';
            const nameB = rowB.dataset.name || '';
            const courseA = rowA.dataset.course || '';
            const courseB = rowB.dataset.course || '';
            const orderA = Number(rowA.dataset.addedOrder || 0);
            const orderB = Number(rowB.dataset.addedOrder || 0);

            if (sortValue === 'name-asc') {
                return compareText(nameA, nameB) || (orderB - orderA);
            }
            if (sortValue === 'name-desc') {
                return compareText(nameB, nameA) || (orderB - orderA);
            }
            if (sortValue === 'group') {
                return compareText(courseA, courseB) || compareText(nameA, nameB) || (orderB - orderA);
            }
            return (orderB - orderA) || compareText(nameA, nameB);
        });

        rows.forEach(row => recordsTableBody.appendChild(row));
    }

    function applyRecordsFilter() {
        const val = (recordsSearch?.value || '').trim().toLowerCase();
        const courseVal = recordsCourseFilterValue;
        const statusVal = recordsStatusFilterValue;
        const typeVal = recordsTypeFilterValue;
        let visible = 0;

        getRecordRows().forEach(row => {
            const rowStatus = (row.dataset.status || '').toLowerCase();
            const rowType = (row.dataset.type || '').toLowerCase();
            const matchStatus = statusVal === 'all' || rowStatus === statusVal;
            const matchType = !typeVal || rowType === typeVal;
            const ok = (row.dataset.id.includes(val) || row.dataset.name.includes(val) || row.dataset.course.includes(val))
                && (!courseVal || row.dataset.course === courseVal)
                && matchStatus
                && matchType;
            row.dataset.filterVisible = ok ? 'true' : 'false';
            if (ok) visible += 1;
        });

        sortRecordsRows();
        recordsCurrentPage = 1;
        const hasFilters = val || courseVal || statusVal !== 'active';

        if (getRecordRows().length === 0) {
            if (recordsTableResponsive) recordsTableResponsive.style.display = '';
            recordsNoResults.style.display = 'none';
            recordsResultCount.textContent = '';
            recordsPaginationContainer.classList.remove('show');
            recordsPaginationContainer.style.display = 'none';
            return;
        }

        if (visible === 0) {
            if (recordsTableResponsive) recordsTableResponsive.style.display = 'none';
            recordsNoResults.style.display = 'block';
            recordsResultCount.textContent = '';
            recordsPaginationContainer.classList.remove('show');
            recordsPaginationContainer.style.display = 'none';
            return;
        }

        if (recordsTableResponsive) recordsTableResponsive.style.display = '';
        recordsNoResults.style.display = 'none';
        recordsResultCount.textContent = hasFilters
            ? `Showing up to ${Math.min(ITEMS_PER_PAGE, visible)} of ${visible} record${visible !== 1 ? 's' : ''}`
            : '';
        updateRecordsDisplay();
        renderRecordsPagination(visible);
    }

    recordsSearch?.addEventListener('input', applyRecordsFilter);

    // ── NEW EDIT OVERLAY LOGIC ─────────────────────────────────

    function updateLogsHistory(row) {
        const historyBody = document.getElementById('editLogsHistoryBody');
        if (!historyBody) return;

        const date = row.dataset.date || new Date().toISOString().split('T')[0];
        const timeIn = row.querySelector('td:nth-child(4)')?.textContent.trim() || '--:--';
        const timeOut = row.querySelector('td:nth-child(5)')?.textContent.trim() || '--:--';

        // History populating with current log data and fake older data to demonstrate the scrollable table
        historyBody.innerHTML = `
            <tr>
                <td class="text-white text-center">${date}</td>
                <td class="text-success text-center">${timeIn}</td>
                <td class="text-danger text-center">${timeOut}</td>
            </tr>
            <tr>
                <td class="text-white-50 text-center">2026-04-08</td>
                <td class="text-success text-center">07:25 AM</td>
                <td class="text-danger text-center">05:00 PM</td>
            </tr>
            <tr>
                <td class="text-white-50 text-center">2026-04-07</td>
                <td class="text-success text-center">07:40 AM</td>
                <td class="text-danger text-center">04:15 PM</td>
            </tr>
            <tr>
                <td class="text-white-50 text-center">2026-04-06</td>
                <td class="text-success text-center">08:05 AM</td>
                <td class="text-danger text-center">05:30 PM</td>
            </tr>
            <tr>
                <td class="text-white-50 text-center">2026-04-05</td>
                <td class="text-success text-center">07:50 AM</td>
                <td class="text-danger text-center">04:45 PM</td>
            </tr>
            <tr>
                <td class="text-white-50 text-center">2026-04-04</td>
                <td class="text-success text-center">08:12 AM</td>
                <td class="text-danger text-center">05:10 PM</td>
            </tr>
        `;
    }

    function showEditCard(row, mode = 'edit') {
        currentEditRow = row;

        const idInput = document.getElementById('editStudentId');
        const nameInput = document.getElementById('editStudentName');
        const typeSel = document.getElementById('editStudentType');
        const courseSel = document.getElementById('editCourseId');
        
        const studentId = row.dataset.idOriginal || row.dataset.id || row.querySelector('td:nth-child(1)')?.textContent.trim() || '';
        const studentName = row.dataset.nameOriginal || row.querySelector('td:nth-child(2)')?.textContent.trim() || '';
        const rawType = row.dataset.type || row.querySelector('td:nth-child(4)')?.textContent.trim() || '';
        const studentType = rawType ? rawType.charAt(0).toUpperCase() + rawType.slice(1).toLowerCase() : '';
        const currentCourseId = row.dataset.courseId || '';
        const currentCourseName = row.dataset.courseOriginal || row.querySelector('td:nth-child(3)')?.textContent.trim() || '';

        idInput.value = studentId;
        nameInput.value = studentName;
        typeSel.value = studentType;
        courseSel.value = currentCourseId;
        
        if (!courseSel.value && currentCourseName) {
            const fallback = Array.from(courseSel.options).find(opt => opt.textContent.trim().toLowerCase() === currentCourseName.trim().toLowerCase());
            if (fallback) courseSel.value = fallback.value;
        }

        const title = document.getElementById('editCardTitle');
        const desc = document.getElementById('editCardDesc');
        const isView = mode === 'view';

        const leftCol = document.getElementById('editCardLeftCol');
        const rightCol = document.getElementById('editCardRightCol');
        const logsSection = document.getElementById('viewLogsHistorySection');

        if (isView) {
            title.textContent = 'VIEW RECORD';
            desc.textContent = 'Read-only view of the current student details.';
            saveStudentEdit.style.display = 'none';
            idInput.readOnly = true;
            nameInput.readOnly = true;
            typeSel.disabled = true;
            courseSel.disabled = true;
            
            // FIXED: Restored split layout for view mode
            leftCol.classList.remove('d-none');
            rightCol.className = 'col-md-7';
            logsSection.classList.remove('d-none');
            updateLogsHistory(row);
        } else {
            title.textContent = 'EDIT RECORD';
            desc.textContent = 'Update the current student details.';
            saveStudentEdit.style.display = 'block';
            idInput.readOnly = true; 
            nameInput.readOnly = false;
            typeSel.disabled = false;
            courseSel.disabled = false;

            // FIXED: Expanded right side fully for edit mode
            leftCol.classList.add('d-none');
            rightCol.className = 'col-md-12';
            logsSection.classList.add('d-none');
        }

        editOverlay.classList.remove('d-none');
        document.getElementById('studentEditCard').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideEditCard() {
        currentEditRow = null;
        editOverlay.classList.add('d-none');
        [editStudentId, editStudentName, editStudentType, editCourseId].forEach(input => {
            if (input) input.value = '';
        });
        editStudentType.disabled = false;
        editCourseId.disabled = false;
    }

    saveStudentEdit.addEventListener('click', async () => {
        if (!currentEditRow) return;
        const newId = editStudentId.value.trim();
        const newName = editStudentName.value.trim();
        const newType = editStudentType.value;
        const newCourse = document.getElementById('editCourseId').value;
        if (!newId || !newName || !newType || !newCourse) {
            showToast('Missing fields', 'warning', 'Please fill in all fields before updating.');
            return;
        }

        saveStudentEdit.disabled = true;
        saveStudentEdit.textContent = 'Saving...';

        try {
            const res = await fetch('/update_student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: newId, student_name: newName, student_type: newType, course_id: newCourse })
            });
            const result = await parseApiResponseSafe(res);

            if (res.ok && result && result.success) {
                hideEditCard();
                showToast('Student updated successfully.', 'success', `${newName.toUpperCase()} has been updated.`);
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast('Update failed.', 'danger', (result && result.error) || 'Could not update student.');
            }
        } catch (err) {
            console.error(err);
            showToast('Server error', 'danger', 'Could not reach the server. Please try again.');
        } finally {
            saveStudentEdit.disabled = false;
            saveStudentEdit.textContent = 'Update';
        }
    });

    cancelEdit.addEventListener('click', hideEditCard);
    editOverlay.addEventListener('click', e => { if (e.target === editOverlay) hideEditCard(); });

    async function handleDeleteStudent(row) {
        const name = row.querySelector('td:nth-child(2)')?.textContent.trim() || 'this student';
        const studentId = row.dataset.idOriginal || row.dataset.id || '';

        const confirmed = await showConfirm(
            `Delete "${name}"?`,
            'This is a soft delete, so the student will stay in the database as inactive.'
        );
        if (!confirmed) return;

        try {
            const res = await fetch('/delete_student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: studentId })
            });
            const result = await parseApiResponseSafe(res);
            if (res.ok && result && result.success) {
                if (currentEditRow === row) hideEditCard();
                showToast(
                    result.already_inactive ? 'Student is already inactive.' : 'Student deleted successfully.',
                    result.already_inactive ? 'info' : 'success',
                    result.already_inactive ? `${name} is already inactive.` : `${name} has been marked inactive.`
                );
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast('Delete failed.', 'danger', (result && result.error) || 'Could not delete student.');
            }
        } catch (err) {
            console.error(err);
            showToast('Server error', 'danger', 'Could not reach the server. Please try again.');
        }
    }

    document.addEventListener('click', function (event) {
        const viewBtn = event.target.closest('.view-student');
        if (viewBtn) {
            const row = viewBtn.closest('tr');
            if (row) showEditCard(row, 'view');
            return;
        }

        const editBtn = event.target.closest('.edit-student-record');
        if (editBtn) {
            const row = editBtn.closest('tr');
            if (row) showEditCard(row, 'edit');
            return;
        }

        const deleteBtn = event.target.closest('.delete-student, .delete-student-record');
        if (deleteBtn) {
            const row = deleteBtn.closest('tr');
            if (row) handleDeleteStudent(row);
        }
    });

    loadCourseFilters();
    loadManualCourses();

    setTimeout(() => {
        applyFilters();
        applyRecordsFilter();
    }, 50);
});
</script>
{% endblock %}
