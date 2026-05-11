document.addEventListener('DOMContentLoaded', function() {
    const adminTable = document.getElementById('adminUserTable');
    const dashboard = document.querySelector('.dashboard-page[data-admin-actor]');
    const modalElement = document.getElementById('confirmActionModal');
    const confirmButton = document.getElementById('confirmActionBtn');
    const messageElement = document.getElementById('adminActionConfirmMessage');
    const targetElement = document.getElementById('adminActionConfirmTarget');
    const modalDismissButtons = modalElement
        ? Array.from(modalElement.querySelectorAll('[data-bs-dismiss="modal"]'))
        : [];
    const modalInstance = modalElement && typeof bootstrap !== 'undefined' && bootstrap.Modal
        ? bootstrap.Modal.getOrCreateInstance(modalElement)
        : null;

    if (!adminTable || !dashboard) {
        return;
    }

    const confirmationActions = new Set(['ban', 'unban', 'delete', 'archive', 'unarchive', 'promote', 'demote']);
    const actionCopy = {
        ban: { verb: 'ban', confirmClass: 'btn-danger', confirmText: 'Confirm ban' },
        unban: { verb: 'unban', confirmClass: 'btn-success', confirmText: 'Confirm unban' },
        delete: { verb: 'delete', confirmClass: 'btn-danger', confirmText: 'Confirm delete' },
        archive: { verb: 'archive', confirmClass: 'btn-warning', confirmText: 'Confirm archive' },
        unarchive: { verb: 'unarchive', confirmClass: 'btn-primary', confirmText: 'Confirm unarchive' },
        promote: { verb: 'promote', confirmClass: 'btn-primary', confirmText: 'Confirm promotion' },
        demote: { verb: 'demote', confirmClass: 'btn-warning', confirmText: 'Confirm demotion' }
    };
    const defaultActionMethod = 'POST';

    let pendingAction = null;
    let isActionInProgress = false;

    function buildActionUrl(action, username) {
        return `/dashboard/admin/${encodeURIComponent(action)}/${encodeURIComponent(username)}`;
    }

    function getDashboardState() {
        return {
            actorUsername: dashboard.dataset.adminActor || '',
            isSuperAdmin: dashboard.dataset.adminIsSuperAdmin === 'true'
        };
    }

    function getRows() {
        return Array.from(adminTable.querySelectorAll('tr'));
    }

    function getRow(username) {
        return getRows().find(row => row.dataset.username === username) || null;
    }

    function getStatusMeta(statusKey) {
        switch (statusKey) {
            case 'verified':
                return { label: 'Verified', badgeClass: 'bg-success' };
            case 'unverified':
                return { label: 'Unverified', badgeClass: 'bg-warning' };
            case 'banned':
                return { label: 'Banned', badgeClass: 'bg-danger' };
            case 'archived':
                return { label: 'Archived', badgeClass: 'bg-dark' };
            default:
                return { label: 'Unverified', badgeClass: 'bg-warning' };
        }
    }

    function getRoleMeta(role) {
        if (role === 'super_admin') {
            return { label: 'Super Admin', badgeClass: 'bg-primary' };
        }

        if (role === 'admin') {
            return { label: 'Admin', badgeClass: 'bg-danger' };
        }

        return { label: 'User', badgeClass: 'bg-secondary' };
    }

    function refreshTableView() {
        if (typeof updateAdminTable === 'function') {
            updateAdminTable(document.getElementById('adminUserSearch')?.value || '');
        }
    }

    function showNotification(message, type) {
        if (typeof showToast === 'function') {
            showToast(message, type);
            return;
        }

        console.log(type === 'error' ? 'Admin action error:' : 'Admin action success:', message);
    }

    function setTooltip(button, title) {
        if (!button) {
            return;
        }

        button.setAttribute('title', title);
        button.setAttribute('data-bs-original-title', title);

        if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) {
            return;
        }

        const instance = bootstrap.Tooltip.getInstance(button);
        if (instance) {
            instance.dispose();
        }

        if (!button.disabled) {
            bootstrap.Tooltip.getOrCreateInstance(button);
        }
    }

    function getPermissions(row) {
        const { actorUsername, isSuperAdmin } = getDashboardState();
        const username = row.dataset.username || '';
        const role = row.dataset.role || 'user';
        const isSelf = username === actorUsername;

        return {
            canManage: !isSelf && role !== 'super_admin' && (isSuperAdmin || role === 'user'),
            canPromote: isSuperAdmin && !isSelf && role === 'user',
            canDemote: isSuperAdmin && !isSelf && role === 'admin'
        };
    }

    function updateActionButton(button, config) {
        if (!button) {
            return;
        }

        button.dataset.adminAction = config.action;
        button.dataset.adminLabel = config.label;
        button.dataset.adminMethod = config.method || button.dataset.adminMethod || defaultActionMethod;
        button.dataset.actionUrl = config.actionUrl || buildActionUrl(config.action, button.dataset.username || '');
        button.disabled = Boolean(config.disabled);
        button.innerHTML = `<i class="fas ${config.iconClass}"></i>`;

        button.classList.remove('text-danger', 'text-success');
        if (config.textClass) {
            button.classList.add(config.textClass);
        }

        setTooltip(button, config.title);
    }

    function updateRoleBadge(row) {
        const badge = row.querySelector('.admin-role-badge');
        if (!badge) {
            return;
        }

        const roleMeta = getRoleMeta(row.dataset.role || 'user');
        badge.className = `badge ${roleMeta.badgeClass} admin-role-badge`;
        badge.textContent = roleMeta.label;
    }

    function updateStatusBadge(row) {
        const badge = row.querySelector('.admin-status-badge');
        if (!badge) {
            return;
        }

        const statusMeta = getStatusMeta(row.dataset.status || 'unverified');
        badge.className = `badge ${statusMeta.badgeClass} admin-status-badge`;
        badge.textContent = statusMeta.label;
    }

    function updateBannedByCell(row) {
        const cell = row.querySelector('.admin-banned-by-cell');
        if (!cell) {
            return;
        }

        const status = row.dataset.status || 'unverified';
        const bannedBy = row.dataset.bannedBy || '';

        if (status !== 'banned') {
            cell.innerHTML = '<span class="text-muted">-</span>';
            return;
        }

        if (bannedBy) {
            cell.innerHTML = `<code>${bannedBy}</code>`;
            return;
        }

        cell.innerHTML = '<span class="text-muted">Unknown</span>';
    }

    function syncRowUi(row) {
        if (!row) {
            return;
        }

        updateRoleBadge(row);
        updateStatusBadge(row);
        updateBannedByCell(row);

        const permissions = getPermissions(row);
        const status = row.dataset.status || 'unverified';

        updateActionButton(row.querySelector('.admin-promote-btn'), {
            action: 'promote',
            label: 'Promote to Admin',
            title: 'Promote to admin',
            iconClass: 'fa-user-shield',
            actionUrl: buildActionUrl('promote', row.dataset.username || ''),
            disabled: !permissions.canPromote
        });

        updateActionButton(row.querySelector('.admin-demote-btn'), {
            action: 'demote',
            label: 'Demote to User',
            title: 'Demote to user',
            iconClass: 'fa-user-minus',
            actionUrl: buildActionUrl('demote', row.dataset.username || ''),
            disabled: !permissions.canDemote
        });

        updateActionButton(row.querySelector('.admin-archive-btn'), {
            action: status === 'archived' ? 'unarchive' : 'archive',
            label: status === 'archived' ? 'Unarchive User' : 'Archive User',
            title: status === 'archived' ? 'Unarchive user' : 'Archive user',
            iconClass: status === 'archived' ? 'fa-box-open' : 'fa-archive',
            actionUrl: buildActionUrl(status === 'archived' ? 'unarchive' : 'archive', row.dataset.username || ''),
            disabled: !permissions.canManage
        });

        updateActionButton(row.querySelector('.admin-ban-btn'), {
            action: status === 'banned' ? 'unban' : 'ban',
            label: status === 'banned' ? 'Unban User' : 'Ban User',
            title: status === 'banned' ? 'Unban user' : 'Ban user',
            iconClass: status === 'banned' ? 'fa-user-check' : 'fa-ban',
            textClass: status === 'banned' ? 'text-success' : 'text-danger',
            actionUrl: buildActionUrl(status === 'banned' ? 'unban' : 'ban', row.dataset.username || ''),
            disabled: !permissions.canManage
        });

        const warnButton = row.querySelector('[data-admin-action="warn"]');
        const resendButton = row.querySelector('[data-admin-action="resend"]');
        const deleteButton = row.querySelector('.admin-delete-btn');

        if (warnButton) {
            warnButton.disabled = !permissions.canManage;
            setTooltip(warnButton, 'Send warning');
        }

        if (resendButton) {
            resendButton.disabled = !permissions.canManage;
            setTooltip(resendButton, 'Resend verification');
        }

        updateActionButton(deleteButton, {
            action: 'delete',
            label: 'Delete User',
            title: 'Delete user',
            iconClass: 'fa-trash-alt',
            textClass: 'text-danger',
            actionUrl: buildActionUrl('delete', row.dataset.username || ''),
            disabled: !permissions.canManage
        });
    }

    function applyActionResult(action, username) {
        const row = getRow(username);
        if (!row) {
            return;
        }

        const { actorUsername } = getDashboardState();
        const verifiedStatus = row.dataset.verified === 'true' ? 'verified' : 'unverified';

        switch (action) {
            case 'ban':
                row.dataset.status = 'banned';
                row.dataset.bannedBy = actorUsername;
                break;
            case 'unban':
                row.dataset.status = verifiedStatus;
                row.dataset.bannedBy = '';
                break;
            case 'archive':
                row.dataset.status = 'archived';
                row.dataset.bannedBy = '';
                break;
            case 'unarchive':
                row.dataset.status = verifiedStatus;
                row.dataset.bannedBy = '';
                break;
            case 'promote':
                row.dataset.role = 'admin';
                break;
            case 'demote':
                row.dataset.role = 'user';
                break;
            case 'delete':
                row.remove();
                break;
            default:
                break;
        }

        if (action !== 'delete') {
            syncRowUi(row);
        }

        refreshTableView();
    }

    function setPendingAction(details) {
        pendingAction = details;

        if (modalElement) {
            modalElement.dataset.pendingAction = details.action || '';
            modalElement.dataset.pendingUsername = details.username || '';
            modalElement.dataset.pendingUserId = details.userId || '';
            modalElement.dataset.pendingMethod = details.method || '';
            modalElement.dataset.pendingUrl = details.actionUrl || '';
        }

        if (confirmButton) {
            confirmButton.dataset.pendingAction = details.action || '';
            confirmButton.dataset.pendingUsername = details.username || '';
            confirmButton.dataset.pendingUserId = details.userId || '';
            confirmButton.dataset.pendingMethod = details.method || '';
            confirmButton.dataset.pendingUrl = details.actionUrl || '';
        }
    }

    function getPendingAction() {
        if (pendingAction) {
            return pendingAction;
        }

        if (!modalElement && !confirmButton) {
            return null;
        }

        const source = confirmButton || modalElement;
        return {
            action: source?.dataset.pendingAction || modalElement?.dataset.pendingAction || '',
            username: source?.dataset.pendingUsername || modalElement?.dataset.pendingUsername || '',
            userId: source?.dataset.pendingUserId || modalElement?.dataset.pendingUserId || '',
            method: source?.dataset.pendingMethod || modalElement?.dataset.pendingMethod || defaultActionMethod,
            actionUrl: source?.dataset.pendingUrl || modalElement?.dataset.pendingUrl || '',
            triggerButton: null
        };
    }

    function resetModalState() {
        pendingAction = null;
        isActionInProgress = false;

        if (modalElement) {
            delete modalElement.dataset.pendingAction;
            delete modalElement.dataset.pendingUsername;
            delete modalElement.dataset.pendingUserId;
            delete modalElement.dataset.pendingMethod;
            delete modalElement.dataset.pendingUrl;
        }

        if (!confirmButton) {
            return;
        }

        confirmButton.disabled = false;
        confirmButton.classList.remove('btn-danger', 'btn-success', 'btn-warning', 'btn-primary');
        confirmButton.classList.add('btn-danger');
        confirmButton.textContent = 'Confirm';

        delete confirmButton.dataset.pendingAction;
        delete confirmButton.dataset.pendingUsername;
        delete confirmButton.dataset.pendingUserId;
        delete confirmButton.dataset.pendingMethod;
        delete confirmButton.dataset.pendingUrl;

        modalDismissButtons.forEach(button => {
            button.disabled = false;
        });
    }

    function hideConfirmationModal() {
        if (modalInstance) {
            modalInstance.hide();
            return;
        }

        if (modalElement) {
            modalElement.classList.remove('show');
            modalElement.setAttribute('aria-hidden', 'true');
            modalElement.style.display = 'none';
        }

        resetModalState();
    }

    function openConfirmationModal(action, username, label, triggerButton) {
        if (!modalElement || !confirmButton || !messageElement || !targetElement || !modalInstance) {
            executeAction(
                action,
                username,
                triggerButton,
                triggerButton?.dataset.adminMethod || defaultActionMethod,
                triggerButton?.dataset.actionUrl || buildActionUrl(action, username)
            );
            return;
        }

        const copy = actionCopy[action] || {
            verb: (label || action || 'continue').toLowerCase(),
            confirmClass: 'btn-primary',
            confirmText: 'Confirm'
        };

        messageElement.textContent = `Are you sure you want to ${copy.verb} this user?`;
        targetElement.textContent = `Selected account: ${username}. This change will be applied immediately to the selected account.`;

        confirmButton.classList.remove('btn-danger', 'btn-success', 'btn-warning', 'btn-primary');
        confirmButton.classList.add(copy.confirmClass);
        confirmButton.textContent = copy.confirmText;

        const targetRow = getRow(username);
        const userId = triggerButton?.dataset.userId || targetRow?.dataset.userId || '';
        const actionUrl = triggerButton?.dataset.actionUrl || buildActionUrl(action, username);
        const actionMethod = triggerButton?.dataset.adminMethod || defaultActionMethod;

        setPendingAction({
            action,
            username,
            userId,
            actionUrl,
            method: actionMethod,
            triggerButton
        });

        modalInstance.show();
    }

    async function executeAction(action, username, triggerButton, requestMethod = defaultActionMethod, requestUrl = null) {
        if (!action || !username) {
            showNotification('Missing admin action details. Please reopen the confirmation dialog.', 'error');
            return;
        }

        const currentPendingAction = getPendingAction();
        const isPendingModalAction = Boolean(
            currentPendingAction
            && currentPendingAction.action === action
            && currentPendingAction.username === username
        );
        const targetRow = getRow(username);
        const rowButton = triggerButton || targetRow?.querySelector(`[data-admin-action="${action}"]`);
        const actionUrl = requestUrl
            || currentPendingAction?.actionUrl
            || rowButton?.dataset.actionUrl
            || buildActionUrl(action, username);
        const actionMethod = requestMethod
            || currentPendingAction?.method
            || rowButton?.dataset.adminMethod
            || defaultActionMethod;

        if (!actionUrl) {
            showNotification('Missing admin action URL. Please choose the action again.', 'error');
            if (isPendingModalAction) {
                hideConfirmationModal();
            }
            return;
        }

        isActionInProgress = true;
        let shouldReload = false;

        if (isPendingModalAction && confirmButton) {
            confirmButton.disabled = true;
            confirmButton.textContent = 'Working...';
            modalDismissButtons.forEach(button => {
                button.disabled = true;
            });
        }

        if (rowButton) {
            rowButton.disabled = true;
        }

        try {
            const response = await fetch(actionUrl, {
                method: actionMethod,
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const contentType = response.headers.get('content-type') || '';
            let data;

            if (contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = {
                    success: response.ok,
                    message: await response.text()
                };
            }

            if (!response.ok) {
                showNotification(data.message || `Admin action failed with HTTP ${response.status}.`, 'error');
                console.error('Admin action error:', { action, username, status: response.status, response: data });
            } else if (data.success) {
                applyActionResult(action, username);
                showNotification(data.message, 'success');
                shouldReload = isPendingModalAction;
            } else {
                showNotification(data.message || 'Admin action failed.', 'error');
                console.error('Admin action error:', { action, username, response: data });
            }
        } catch (error) {
            showNotification('An error occurred. Please try again.', 'error');
            console.error('Admin action error:', error);
        } finally {
            if (rowButton) {
                const row = rowButton.closest('tr');
                if (row) {
                    syncRowUi(row);
                } else {
                    rowButton.disabled = false;
                }
            }

            if (isPendingModalAction) {
                isActionInProgress = false;
                hideConfirmationModal();
            } else {
                isActionInProgress = false;
            }

            if (shouldReload) {
                window.setTimeout(() => window.location.reload(), 200);
            }
        }
    }

    function handleAdminAction(action, username, label, triggerButton = null) {
        if (confirmationActions.has(action)) {
            openConfirmationModal(action, username, label, triggerButton);
            return;
        }

        executeAction(
            action,
            username,
            triggerButton,
            triggerButton?.dataset.adminMethod || defaultActionMethod,
            triggerButton?.dataset.actionUrl || buildActionUrl(action, username)
        );
    }

    window.handleAdminAction = handleAdminAction;

    adminTable.addEventListener('click', function(event) {
        const button = event.target.closest('.admin-action-btn');
        if (!button || button.disabled) {
            return;
        }

        handleAdminAction(
            button.dataset.adminAction,
            button.dataset.username,
            button.dataset.adminLabel,
            button
        );
    });

    if (modalElement && confirmButton) {
        modalElement.addEventListener('hide.bs.modal', function(event) {
            if (isActionInProgress) {
                event.preventDefault();
            }
        });

        modalElement.addEventListener('hidden.bs.modal', function() {
            resetModalState();
        });

        confirmButton.addEventListener('click', function(event) {
            event.preventDefault();

            if (isActionInProgress) {
                return;
            }

            const actionDetails = getPendingAction();
            if (!actionDetails?.action || !actionDetails?.username) {
                showNotification('No admin action is selected. Please choose an action again.', 'error');
                hideConfirmationModal();
                return;
            }

            pendingAction = actionDetails;

            executeAction(
                actionDetails.action,
                actionDetails.username,
                actionDetails.triggerButton,
                actionDetails.method || defaultActionMethod,
                actionDetails.actionUrl
            );
        });
    }

    getRows().forEach(syncRowUi);
});
