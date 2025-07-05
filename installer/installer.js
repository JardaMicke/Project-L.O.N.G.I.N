// --- State Management ---
const steps = [
    { id: 'welcome', title: 'Welcome' },
    { id: 'path', title: 'Installation Path' },
    { id: 'source', title: 'Source URL' },
    { id: 'install', title: 'Installation' },
    { id: 'finished', title: 'Finished' },
];

let currentStep = 0;
let installPath = 'C:\\Users\\jamic\\Longin-AI-systems';
let sourceUrl = 'https://github.com/JardaMicke/Project-L.O.N.G.I.N.git';
const logs = [];

// --- UI Rendering ---

/**
 * Adds a message to the log display.
 * @param {string} message The log message to display.
 * @param {'info' | 'error' | 'success'} type The type of log message.
 */
const addLog = (message, type = 'info') => {
    logs.push({ message, type, timestamp: new Date().toLocaleTimeString() });
    renderLogs();
};

/**
 * Renders the current logs to the log output container.
 */
const renderLogs = () => {
    const logContainer = document.getElementById('log-output');
    if (logContainer) {
        logContainer.innerHTML = logs.map(log => {
            const colorClass = {
                info: 'text-gray-400',
                error: 'text-red-500',
                success: 'text-green-400',
            }[log.type];
            return `<p><span class="text-gray-600">${log.timestamp}</span> <span class="${colorClass}">${log.message}</span></p>`;
        }).join('');
        // Auto-scroll to the bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }
};

/**
 * Renders the current step of the installer.
 */
const renderStep = () => {
    const container = document.getElementById('installer-steps');
    if (!container) return;

    const step = steps[currentStep];
    let content = `<h2 class="text-2xl border-b border-green-700 pb-2 mb-4">Step ${currentStep + 1}: ${step.title}</h2>`;

    switch (step.id) {
        case 'welcome':
            content += `<p class="my-4">Welcome to the L.O.N.G.I.N. installer. This wizard will guide you through the setup process.</p>
                        <button class="border border-green-500 px-4 py-2 hover:bg-green-900 transition-colors" onclick="nextStep()">Start Setup</button>`;
            break;
        case 'path':
            content += `<p class="my-4">Select the installation directory for L.O.N.G.I.N.</p>
                        <input class="bg-gray-900 border border-green-500 p-2 w-full my-2 focus:outline-none focus:ring-2 focus:ring-green-500" type="text" id="install-path" value="${installPath}">
                        <button class="border border-green-500 px-4 py-2 hover:bg-green-900 transition-colors" onclick="nextStep()">Next</button>`;
            break;
        case 'source':
            content += `<p class="my-4">Enter the source URL of the repository to install.</p>
                        <input class="bg-gray-900 border border-green-500 p-2 w-full my-2 focus:outline-none focus:ring-2 focus:ring-green-500" type="text" id="source-url" value="${sourceUrl}">
                        <button class="border border-green-500 px-4 py-2 hover:bg-green-900 transition-colors" onclick="nextStep()">Next</button>`;
            break;
        case 'install':
            content += `<p class="my-4">Ready to install to <strong class="text-green-400">${installPath}</strong> from <strong class="text-green-400">${sourceUrl}</strong>.</p>
                        <button id="install-button" class="border border-green-500 px-4 py-2 hover:bg-green-900 transition-colors" onclick="install()">Install Now</button>
                        <div id="log-output" class="mt-4 p-2 border border-gray-700 h-64 overflow-y-scroll bg-gray-900/50"></div>`;
            break;
        case 'finished':
            content += `<p class="my-4 text-xl">Installation finished successfully!</p>
                        <p>You can now close this installer and run the L.O.N.G.I.N. application from the installation directory.</p>`;
            break;
    }
    container.innerHTML = content;
};

// --- Actions and Navigation ---

/**
 * Validates the current step's input and moves to the next step.
 */
const nextStep = () => {
    if (steps[currentStep].id === 'path') {
        const pathInput = document.getElementById('install-path');
        if (pathInput && pathInput.value.trim()) {
            installPath = pathInput.value.trim();
        } else {
            alert('Please provide a valid installation path.');
            return;
        }
    }
    if (steps[currentStep].id === 'source') {
        const sourceInput = document.getElementById('source-url');
        if (sourceInput && sourceInput.value.trim()) {
            sourceUrl = sourceInput.value.trim();
        } else {
            alert('Please provide a valid source URL.');
            return;
        }
    }

    if (currentStep < steps.length - 1) {
        currentStep++;
        renderStep();
    }
};

/**
 * Simulates the installation process, logging each step.
 */
const install = () => {
    const installButton = document.getElementById('install-button');
    if (installButton) {
        installButton.disabled = true;
        installButton.innerText = 'Installing...';
        installButton.classList.add('opacity-50', 'cursor-not-allowed');
    }

    logs.length = 0; // Clear previous logs
    addLog('Starting installation...');

    // Simulate installation process with timeouts
    setTimeout(() => {
        addLog(`Cloning repository from ${sourceUrl}...`);
        setTimeout(() => {
            addLog('Repository cloned successfully.');
            setTimeout(() => {
                addLog('Pulling Docker images (postgres:16, redis:7)...');
                setTimeout(() => {
                    addLog('Docker images pulled successfully.');
                    setTimeout(() => {
                        addLog('Running "docker-compose up -d"...');
                        setTimeout(() => {
                            addLog('Containers for postgres and redis started successfully.');
                            addLog('Installation complete!', 'success');
                            // Move to the final step
                            nextStep();
                        }, 2000);
                    }, 1500);
                }, 3000);
            }, 1000);
        }, 2000);
    }, 500);
};

// --- Initializer ---
window.onload = renderStep;
