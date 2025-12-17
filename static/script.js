document.addEventListener('DOMContentLoaded', () => {
    const stage1 = document.getElementById('stage-1');
    const stage2 = document.getElementById('stage-2');
    const stage3 = document.getElementById('stage-3');

    const btnCheck = document.getElementById('btn-check');
    const btnSubmit = document.getElementById('btn-submit');
    
    const phoneInput = document.getElementById('phone');
    const emailInput = document.getElementById('email');
    
    const phoneError = document.getElementById('phone-error');
    const emailError = document.getElementById('email-error');
    
    const greeting = document.getElementById('greeting');
    const finalMessage = document.getElementById('final-message');

    let currentPhone = '';

    // Helper to transition stages
    function showStage(hideStage, showStageElement) {
        hideStage.classList.remove('active');
        // Wait for animation or just swap
        setTimeout(() => {
            hideStage.style.display = 'none';
            showStageElement.style.display = 'block';
            // Force reflow
            void showStageElement.offsetWidth;
            showStageElement.classList.add('active');
        }, 300); // match css transition
    }

    btnCheck.addEventListener('click', async () => {
        const phone = phoneInput.value.trim();
        phoneError.textContent = '';
        
        if (!phone) {
            phoneError.textContent = 'Por favor, escribe un número.';
            return;
        }

        try {
            btnCheck.disabled = true;
            btnCheck.textContent = 'Buscando...';
            
            const response = await fetch('/api/check_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone })
            });

            const data = await response.json();

            if (response.ok && data.found) {
                currentPhone = phone;
                greeting.textContent = data.message;
                showStage(stage1, stage2);
                setTimeout(() => emailInput.focus(), 400);
            } else {
                phoneError.textContent = data.message || 'Error al buscar el número.';
            }
        } catch (error) {
            console.error(error);
            phoneError.textContent = 'Error de conexión.';
        } finally {
            btnCheck.disabled = false;
            btnCheck.textContent = 'Continuar';
        }
    });

    btnSubmit.addEventListener('click', async () => {
        const email = emailInput.value.trim();
        emailError.textContent = '';

        if (!email || !email.includes('@')) {
            emailError.textContent = 'Por favor, escribe un email válido.';
            return;
        }

        try {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Enviando...';

            const response = await fetch('/api/register_email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: currentPhone, email })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                finalMessage.textContent = data.message;
                showStage(stage2, stage3);
            } else {
                emailError.textContent = data.message || 'Error al registrar el email.';
            }
        } catch (error) {
            console.error(error);
            emailError.textContent = 'Error de conexión.';
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.textContent = 'Enviar';
        }
    });

    // Enter key support
    phoneInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') btnCheck.click();
    });
    
    emailInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') btnSubmit.click();
    });
});
