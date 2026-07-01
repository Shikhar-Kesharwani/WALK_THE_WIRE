document.getElementById('resolve-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const domainInput = document.getElementById('domain-input').value.trim();
    if (!domainInput) return;

    const btnText = document.querySelector('#resolve-btn span');
    const btnLoader = document.getElementById('btn-loader');
    const resultsContainer = document.getElementById('results-container');
    const ipDisplay = document.getElementById('ip-display');
    const timeBadge = document.getElementById('time-badge');
    const terminalBody = document.getElementById('terminal-body');

    // UI Reset
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    terminalBody.innerHTML = '';
    ipDisplay.textContent = '--';
    ipDisplay.classList.remove('error');

    try {
        const response = await fetch(`/api/resolve?domain=${encodeURIComponent(domainInput)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Server error');
        }

        // Setup results UI
        resultsContainer.classList.remove('hidden');
        timeBadge.textContent = data.elapsed;

        if (data.ip) {
            ipDisplay.textContent = data.ip;
        } else {
            ipDisplay.textContent = 'NXDOMAIN';
            ipDisplay.classList.add('error');
        }

        // Animate trace lines
        if (data.trace && data.trace.length > 0) {
            data.trace.forEach((line, index) => {
                setTimeout(() => {
                    const div = document.createElement('div');
                    div.className = 'trace-line';
                    
                    // Simple syntax highlighting based on text
                    let content = line.replace(/ /g, '&nbsp;');
                    if (content.includes('[CACHE HIT]') || content.includes('✓ Answer:')) {
                        div.classList.add('highlight-hit');
                    } else if (content.includes('NXDOMAIN') || content.includes('Error:')) {
                        div.classList.add('highlight-error');
                    } else if (content.includes('Referred to') || content.includes('CNAME alias:')) {
                        div.classList.add('highlight-referral');
                    }
                    
                    div.innerHTML = content;
                    terminalBody.appendChild(div);
                    terminalBody.scrollTop = terminalBody.scrollHeight;
                }, index * 100); // 100ms delay per line for animation effect
            });
        }
        
    } catch (err) {
        resultsContainer.classList.remove('hidden');
        ipDisplay.textContent = 'ERROR';
        ipDisplay.classList.add('error');
        timeBadge.textContent = '0.000s';
        
        const div = document.createElement('div');
        div.className = 'trace-line highlight-error';
        div.textContent = `Exception: ${err.message}`;
        terminalBody.appendChild(div);
    } finally {
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
    }
});
