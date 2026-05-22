document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username'); 
    const passwordInput = document.getElementById('password'); 
    const submitBtn = document.getElementById('login-btn');    
    const flashContainer = document.getElementById('flash-container');
    const timerDisplay = document.createElement('div');
    timerDisplay.style.marginTop = '15px';
    timerDisplay.style.fontWeight = 'bold';
    timerDisplay.style.color = '#dc3545'; 
    timerDisplay.style.textAlign = 'center';
    submitBtn.parentNode.insertBefore(timerDisplay, submitBtn.nextSibling);

    checkLockout();

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); 

        flashContainer.innerHTML = "";
        timerDisplay.innerText = "";

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username && !password) {
            flashContainer.innerHTML = `
                <div class="alert alert-danger border-0 bg-danger bg-opacity-10 text-danger mb-4" role="alert">
                    <i class="bi bi-exclamation-circle me-2"></i>Please enter a username and password.
                </div>
            `;
            return;
        }

        if (!username) {
            flashContainer.innerHTML = `
                <div class="alert alert-danger border-0 bg-danger bg-opacity-10 text-danger mb-4" role="alert">
                    <i class="bi bi-exclamation-circle me-2"></i>Please enter a username.
                </div>
            `;
            return;
        }

        if (!password) {
            flashContainer.innerHTML = `
                <div class="alert alert-danger border-0 bg-danger bg-opacity-10 text-danger mb-4" role="alert">
                    <i class="bi bi-exclamation-circle me-2"></i>Please enter a password.
                </div>
            `;
            return;
        }

        const payload = {
            username: username,
            password: password
        };

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {

                localStorage.removeItem('failed_attempts');
                localStorage.removeItem('lockout_until');

                flashContainer.innerHTML = `
                    <div class="alert alert-success border-0 bg-success bg-opacity-10 text-success mb-4" role="alert">
                        <i class="bi bi-check-circle me-2"></i>Login successful. Redirecting...
                    </div>
                `;
                window.location.href = result.redirect_url;
            } else {
                flashContainer.innerHTML = `
                    <div class="alert alert-danger border-0 bg-danger bg-opacity-10 text-danger mb-4" role="alert">
                        <i class="bi bi-exclamation-circle me-2"></i>${result.message}
                    </div>
                `;
                handleFailedAttempt();
            }
        } catch (error) {
            flashContainer.innerHTML = `
                <div class="alert alert-danger border-0 bg-danger bg-opacity-10 text-danger mb-4" role="alert">
                    <i class="bi bi-exclamation-triangle me-2"></i>Network error. Please try again.
                </div>
            `;
        }
    });

    function handleFailedAttempt() {
        let attempts = parseInt(localStorage.getItem('failed_attempts') || '0');
        attempts += 1;
        localStorage.setItem('failed_attempts', attempts);

        if (attempts >= 3) {
            const lockoutUntil = Date.now() + 60000;
            localStorage.setItem('lockout_until', lockoutUntil);
            checkLockout(); 
        }
    }

    function checkLockout() {
        const lockoutTime = localStorage.getItem('lockout_until');

        if (lockoutTime && Date.now() < parseInt(lockoutTime)) {
            lockUI(parseInt(lockoutTime));
        } else if (lockoutTime) {
            localStorage.removeItem('failed_attempts');
            localStorage.removeItem('lockout_until');
        }
    }

    function lockUI(endTime) {
        usernameInput.disabled = true;
        passwordInput.disabled = true;
        submitBtn.disabled = true;
        
        flashContainer.innerHTML = "";

        const interval = setInterval(() => {
            const timeLeft = Math.ceil((endTime - Date.now()) / 1000);
            
            if (timeLeft <= 0) {
                clearInterval(interval);
                usernameInput.disabled = false;
                passwordInput.disabled = false;
                submitBtn.disabled = false;
                timerDisplay.innerText = "";
                
                localStorage.removeItem('failed_attempts');
                localStorage.removeItem('lockout_until');
            } else {
                timerDisplay.innerText = `Too many attempts. System locked for ${timeLeft} seconds.`;
            }
        }, 1000);
        
        const initialTimeLeft = Math.ceil((endTime - Date.now()) / 1000);
        timerDisplay.innerText = `Too many attempts. System locked for ${initialTimeLeft} seconds.`;
    }
});