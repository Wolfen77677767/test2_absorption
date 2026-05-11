/**
 * Gas Absorption Solver - Interactive UI Module
 * Handles sidebar navigation, form validation, and interactive features
 */

// ============================================================================
// SIDEBAR TOGGLE
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const wrapper = document.querySelector('.wrapper');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 992) {
                wrapper.classList.toggle('sidebar-open');
                wrapper.classList.remove('sidebar-collapsed');
                sidebarToggle.innerHTML = wrapper.classList.contains('sidebar-open')
                    ? '<i class="fas fa-times"></i>'
                    : '<i class="fas fa-bars"></i>';
            } else {
                wrapper.classList.toggle('sidebar-collapsed');
                sidebarToggle.innerHTML = wrapper.classList.contains('sidebar-collapsed')
                    ? '<i class="fas fa-chevron-right"></i>'
                    : '<i class="fas fa-bars"></i>';
            }
        });
    }
    
    // Close mobile sidebar when a link is clicked
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 992 && wrapper.classList.contains('sidebar-open')) {
                wrapper.classList.remove('sidebar-open');
                sidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
    });

    // Highlight active navigation link
    updateActiveNavLink();
});

// ============================================================================
// ACTIVE NAVIGATION LINK HIGHLIGHTING
// ============================================================================

function updateActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        const isDashboardLink = href === '/dashboard' && currentPath.startsWith('/dashboard');
        const isExactMatch = href === currentPath;

        if (isExactMatch || isDashboardLink) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

function validateAbsorptionForm() {
    const form = document.getElementById('absorptionForm');
    if (!form) return true;

    const y0 = parseFloat(document.getElementById('y0').value);
    const ytarget = parseFloat(document.getElementById('ytarget').value);
    const G = parseFloat(document.getElementById('G').value);
    const L = parseFloat(document.getElementById('L').value);
    const m = parseFloat(document.getElementById('m').value);

    const validationAlert = document.getElementById('validationAlert');
    const validationMessage = document.getElementById('validationMessage');

    let errors = [];

    // Validation rules
    if (isNaN(y0) || y0 < 0 || y0 > 1) {
        errors.push('y₀ must be between 0 and 1');
    }
    if (isNaN(ytarget) || ytarget < 0 || ytarget > 1) {
        errors.push('y_target must be between 0 and 1');
    }
    if (ytarget >= y0) {
        errors.push('y_target must be less than y₀ for absorption to occur');
    }
    if (isNaN(G) || G <= 0) {
        errors.push('Gas flow rate (G\') must be a positive number');
    }
    if (isNaN(L) || L <= 0) {
        errors.push('Liquid flow rate (L\') must be a positive number');
    }
    if (isNaN(m) || m <= 0) {
        errors.push('Equilibrium slope (m) must be a positive number');
    }

    if (errors.length > 0) {
        if (validationAlert) {
            validationMessage.textContent = errors.join(' • ');
            validationAlert.classList.remove('d-none');
        }
        return false;
    } else {
        if (validationAlert) {
            validationAlert.classList.add('d-none');
        }
        return true;
    }
}

// ============================================================================
// REAL-TIME INPUT VALIDATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('absorptionForm');
    if (!form) return;

    const inputs = form.querySelectorAll('input[type="number"], select');
    
    inputs.forEach(input => {
        input.addEventListener('change', validateAbsorptionForm);
        input.addEventListener('blur', function() {
            this.classList.remove('is-invalid');
        });
    });

    // Form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!validateAbsorptionForm()) {
            return;
        }

        // Show loading overlay
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('active');
        }

        // Submit form
        setTimeout(() => {
            form.submit();
        }, 500);
    });
});

// ============================================================================
// RESPONSIVE FORM ADJUSTMENTS
// ============================================================================

window.addEventListener('resize', function() {
    updateFormLayout();
});

function updateFormLayout() {
    const width = window.innerWidth;
    const inputs = document.querySelectorAll('.form-control, .form-select');
    
    inputs.forEach(input => {
        if (width <= 576) {
            input.style.minHeight = '44px'; // Larger touch targets on mobile
        }
    });
}

// Call on page load
document.addEventListener('DOMContentLoaded', updateFormLayout);

// ============================================================================
// TOOLTIP INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltip initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// ============================================================================
// SMOOTH SCROLL FOR ANCHORS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// ============================================================================
// LOADING STATE MANAGEMENT
// ============================================================================

function showLoadingOverlay(message = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        document.querySelector('.spinner-text').textContent = message;
        overlay.classList.add('active');
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

document.addEventListener('keydown', function(e) {
    // Alt + C = Go to Calculate
    if (e.altKey && e.key === 'c') {
        window.location.href = '/calculate';
    }
    // Alt + H = Go to Home
    if (e.altKey && e.key === 'h') {
        window.location.href = '/';
    }
    // Alt + T = Go to Theory
    if (e.altKey && e.key === 't') {
        window.location.href = '/theory';
    }
});

// ============================================================================
// ACCESSIBILITY IMPROVEMENTS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Add aria-labels to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        if (!btn.getAttribute('aria-label')) {
            const text = btn.textContent.trim();
            if (text) {
                btn.setAttribute('aria-label', text);
            }
        }
    });

    // Add role to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        if (!card.getAttribute('role')) {
            card.setAttribute('role', 'article');
        }
    });
});

// ============================================================================
// SEARCH SUGGESTIONS / ADMIN TABLE FILTERING
// ============================================================================

function getAdminRows() {
    return Array.from(document.querySelectorAll('#adminUserTable tr'));
}

let currentAdminFilter = 'all';

function updateAdminTable(query = '', filter = currentAdminFilter) {
    const rows = getAdminRows();
    const normalized = query.trim().toLowerCase();
    let visibleCount = 0;

    rows.forEach(row => {
        const text = row.getAttribute('data-search') || '';
        const status = row.getAttribute('data-status') || 'unverified';
        const role = row.getAttribute('data-role') || 'user';
        const matchesQuery = !normalized || text.includes(normalized);
        let matchesFilter = true;

        switch (filter) {
            case 'verified':
                matchesFilter = status === 'verified';
                break;
            case 'unverified':
                matchesFilter = status === 'unverified';
                break;
            case 'banned':
                matchesFilter = status === 'banned';
                break;
            case 'disabled':
                matchesFilter = status === 'disabled';
                break;
            case 'admin':
                matchesFilter = role === 'admin';
                break;
            case 'active':
                matchesFilter = role === 'user';
                break;
            default:
                matchesFilter = true;
        }

        if (matchesQuery && matchesFilter) {
            row.classList.remove('d-none');
            row.classList.remove('hidden-page');
            visibleCount++;
        } else {
            row.classList.add('d-none');
            row.classList.add('hidden-page');
        }
    });

    updateAdminPagination(visibleCount);
}

function updateAdminPagination(totalRows) {
    const perPage = 8;
    const pagination = document.getElementById('adminPagination');
    const rows = getAdminRows().filter(row => !row.classList.contains('d-none'));
    const pageCount = Math.ceil(rows.length / perPage);

    if (!pagination) return;
    pagination.innerHTML = '';

    if (pageCount <= 1) {
        rows.forEach(row => row.classList.remove('hidden-page'));
        return;
    }

    rows.forEach((row, index) => {
        const pageIndex = Math.floor(index / perPage);
        row.dataset.page = pageIndex;
        row.classList.toggle('hidden-page', pageIndex !== 0);
    });

    for (let page = 0; page < pageCount; page++) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-light';
        button.textContent = (page + 1).toString();
        button.addEventListener('click', () => {
            rows.forEach(row => {
                row.classList.toggle('hidden-page', parseInt(row.dataset.page, 10) !== page);
            });
        });
        pagination.appendChild(button);
    }
}

function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-message ${type}`;
    toast.innerHTML = `
        <span class="toast-icon"><i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i></span>
        <div class="toast-content">${message}</div>
        <button type="button" class="toast-close" aria-label="Close">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, duration);
}

async function handleLegacyAdminAction(action, username, label) {
    const confirmationActions = ['ban', 'unban', 'delete'];
    const message = confirmationActions.includes(action)
        ? `Are you sure you want to ${label.toLowerCase()} for ${username}?` 
        : `Perform ${label.toLowerCase()} for ${username}?`;

    if (confirmationActions.includes(action) && !confirm(message)) {
        return;
    }

    try {
        const response = await fetch(`/dashboard/admin/${action}/${username}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const data = await response.json();
        if (data.success) {
            showToast(data.message, 'success');
            // Optionally reload the page or update the table
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('An error occurred. Please try again.', 'error');
        console.error('Admin action error:', error);
    }
}

if (typeof window !== 'undefined' && !window.handleAdminAction) {
    window.handleAdminAction = handleLegacyAdminAction;
}

function setupAdminSearch() {
    const searchInput = document.getElementById('adminUserSearch');
    const suggestions = document.getElementById('adminSearchSuggestions');
    if (!searchInput || !suggestions) return;

    const rows = getAdminRows();
    const suggestionsData = rows.map(row => {
        const first = row.children[0]?.textContent.trim();
        const last = row.children[1]?.textContent.trim();
        const email = row.children[2]?.textContent.trim();
        return { value: `${first} ${last} – ${email}`, query: `${first} ${last} ${email}`.toLowerCase() };
    });

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim().toLowerCase();
        updateAdminTable(query);
        suggestions.innerHTML = '';

        if (!query) {
            suggestions.classList.add('d-none');
            return;
        }

        const matches = suggestionsData.filter(item => item.query.includes(query)).slice(0, 6);
        if (!matches.length) {
            suggestions.classList.add('d-none');
            return;
        }

        matches.forEach(item => {
            const li = document.createElement('li');
            li.className = 'suggestion-item';
            li.textContent = item.value;
            li.addEventListener('click', () => {
                searchInput.value = item.value.split(' – ')[0];
                updateAdminTable(searchInput.value);
                suggestions.classList.add('d-none');
            });
            suggestions.appendChild(li);
        });
        suggestions.classList.remove('d-none');
    });

    document.addEventListener('click', event => {
        if (!suggestions.contains(event.target) && event.target !== searchInput) {
            suggestions.classList.add('d-none');
        }
    });
}

function setupSignupValidation() {
    const form = document.getElementById('signupForm');
    if (!form) return;

    const submitBtn = document.getElementById('submitBtn');
    const fields = {
        firstName: document.getElementById('first_name'),
        lastName: document.getElementById('last_name'),
        username: document.getElementById('username'),
        email: document.getElementById('email'),
        confirmEmail: document.getElementById('confirm_email'),
        password: document.getElementById('password'),
        confirmPassword: document.getElementById('confirm_password')
    };

    const errors = {
        firstName: document.getElementById('firstNameError'),
        lastName: document.getElementById('lastNameError'),
        username: document.getElementById('usernameError'),
        email: document.getElementById('emailError'),
        confirmEmail: document.getElementById('confirmEmailError'),
        password: document.getElementById('passwordError'),
        confirmPassword: document.getElementById('confirmPasswordError')
    };

    const strengthIndicator = document.getElementById('passwordStrength');
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;

    function validateField(fieldKey, validator) {
        const input = fields[fieldKey];
        const error = errors[fieldKey];
        if (!input) return true;
        const value = input.value.trim();
        let valid = true;

        if (!value) {
            error.textContent = 'This field is required.';
            input.classList.add('is-invalid');
            valid = false;
        } else if (validator && !validator(value)) {
            error.textContent = 'Please provide a valid value.';
            input.classList.add('is-invalid');
            valid = false;
        } else {
            error.textContent = '';
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }

        return valid;
    }

    function validatePasswordFields() {
        const passwordValid = validateField('password', value => passwordRegex.test(value));
        const password = fields.password.value;
        const confirmPassword = fields.confirmPassword.value;

        if (password && confirmPassword && password !== confirmPassword) {
            errors.confirmPassword.textContent = 'Passwords do not match.';
            fields.confirmPassword.classList.add('is-invalid');
            return false;
        }

        return passwordValid && validateField('confirmPassword');
    }

    function validateEmails() {
        const emailValid = validateField('email', value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value));
        const email = fields.email.value;
        const confirmEmail = fields.confirmEmail.value;

        if (email && confirmEmail && email !== confirmEmail) {
            errors.confirmEmail.textContent = 'Emails do not match.';
            fields.confirmEmail.classList.add('is-invalid');
            return false;
        }

        return emailValid && validateField('confirmEmail');
    }

    function updateWeakPasswordMeter() {
        const value = fields.password.value;
        if (!value) {
            strengthIndicator.textContent = '';
            return;
        }
        const score = [/[a-z]/, /[A-Z]/, /\d/, /[!@#$%^&*]/].reduce((count, regex) => count + regex.test(value), 0);
        const strength = score < 3 ? 'Weak' : score < 4 ? 'Medium' : 'Strong';
        strengthIndicator.textContent = `Strength: ${strength}`;
        strengthIndicator.style.color = score < 3 ? '#dc3545' : score < 4 ? '#ffc107' : '#28a745';
    }

    function updateSubmitState() {
        const allValid = [
            validateField('firstName'),
            validateField('lastName'),
            validateField('username'),
            validateEmails(),
            validatePasswordFields()
        ].every(Boolean);
        submitBtn.disabled = !allValid;
        submitBtn.style.opacity = allValid ? '1' : '0.6';
    }

    Object.values(fields).forEach(field => {
        if (!field) return;
        field.addEventListener('input', () => {
            updateWeakPasswordMeter();
            updateSubmitState();
        });
    });

    form.addEventListener('submit', function(event) {
        if (submitBtn.disabled) {
            event.preventDefault();
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    setupAdminSearch();
    setupAdminFilters();
    setupSignupValidation();
    updateAdminTable();
});

function setupAdminFilters() {
    const filterButtons = Array.from(document.querySelectorAll('[data-admin-filter]'));
    if (!filterButtons.length) return;

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const filter = button.dataset.adminFilter;
            currentAdminFilter = filter;

            filterButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.adminFilter === filter));
            updateAdminTable(document.getElementById('adminUserSearch')?.value || '', filter);
        });
    });
}

// ============================================================================
// PERFORMANCE OPTIMIZATION
// ============================================================================

// Debounce function for resize events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================================
// SIGNUP FORM SECURITY RESTRICTIONS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signupForm');
    if (!signupForm) return;

    // Target fields that need restrictions
    const restrictedFields = [
        'input[name="email"]',
        'input[name="confirm_email"]',
        'input[name="password"]',
        'input[name="confirm_password"]'
    ];

    restrictedFields.forEach(selector => {
        const field = signupForm.querySelector(selector);
        if (field) {
            // Prevent right-click context menu
            field.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                return false;
            });

            // Additional event prevention (backup for HTML attributes)
            field.addEventListener('copy', function(e) {
                e.preventDefault();
                return false;
            });

            field.addEventListener('paste', function(e) {
                e.preventDefault();
                return false;
            });

            field.addEventListener('cut', function(e) {
                e.preventDefault();
                return false;
            });

            field.addEventListener('dragstart', function(e) {
                e.preventDefault();
                return false;
            });

            field.addEventListener('drop', function(e) {
                e.preventDefault();
                return false;
            });
        }
    });
});

// ============================================================================
// CHATBOT WIDGET
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const widget = document.getElementById('chatbotWidget');
    const toggle = document.getElementById('chatbotToggle');
    const panel = document.getElementById('chatbotPanel');
    const closeButton = document.getElementById('chatbotClose');
    const form = document.getElementById('chatbotForm');
    const input = document.getElementById('chatbotInput');
    const messages = document.getElementById('chatbotMessages');
    const sendButton = document.getElementById('chatbotSend');

    if (!widget || !toggle || !panel || !form || !input || !messages || !sendButton) {
        return;
    }

    let welcomeRendered = false;

    function scrollToBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(content, type) {
        const message = document.createElement('div');
        message.className = `chatbot-message ${type}`;
        message.textContent = content;
        messages.appendChild(message);
        scrollToBottom();
    }

    function openChatbot() {
        widget.classList.add('open');
        panel.setAttribute('aria-hidden', 'false');
        toggle.setAttribute('aria-expanded', 'true');

        if (!welcomeRendered) {
            addMessage("Welcome! I'm your AI assistant. Ask me anything about the Gas Absorption Solver or how to use the platform.", 'bot');
            welcomeRendered = true;
        }

        input.focus();
    }

    function closeChatbot() {
        widget.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        toggle.setAttribute('aria-expanded', 'false');
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) {
            return;
        }

        addMessage(text, 'user');
        input.value = '';
        sendButton.disabled = true;

        try {
            const response = await fetch('/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            if (!response.ok || !data.response) {
                throw new Error(data.response || 'Unable to get a response right now.');
            }

            addMessage(data.response, data.type === 'error' ? 'error' : 'bot');
        } catch (error) {
            addMessage(error.message || 'Sorry, something went wrong. Please try again.', 'error');
            console.error('Chatbot error:', error);
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    }

    toggle.addEventListener('click', function() {
        if (widget.classList.contains('open')) {
            closeChatbot();
        } else {
            openChatbot();
        }
    });

    if (closeButton) {
        closeButton.addEventListener('click', closeChatbot);
    }

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        sendMessage();
    });

    input.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
});
