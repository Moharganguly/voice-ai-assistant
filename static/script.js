// --- Get references to all the HTML elements ---
const mainButton = document.getElementById('main-button');
const chatLog = document.getElementById('chat-log');

let mediaRecorder;
let socket; // This will hold our WebSocket connection
let stream; // This will hold the microphone stream

// --- Check for browser support ---
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Your browser does not support audio recording.');
}

// --- Attach function to the main button click ---
mainButton.addEventListener('click', handleMainButtonClick);

let currentState = 'idle'; // States: 'idle', 'recording'

function handleMainButtonClick() {
    if (currentState === 'idle') {
        startStreaming();
    } else if (currentState === 'recording') {
        stopStreaming();
    }
}

// --- Core Functions ---

function startStreaming() {
    updateUI('recording');
    
    // 1. Get microphone access first.
    navigator.mediaDevices.getUserMedia({ audio: true }).then(micStream => {
        stream = micStream; // Store the stream so we can stop it later
        
        // 2. Once we have the microphone, create the WebSocket connection.
        const wsUrl = `ws://${window.location.host}/ws`;
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log("WebSocket connection established and microphone is ready.");
            
            // 3. Create the MediaRecorder with a more specific audio-only mimeType.
            const options = { mimeType: 'audio/webm; codecs=opus' };
            mediaRecorder = new MediaRecorder(stream, options);

            // 4. This event fires whenever a new chunk of audio is ready.
            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                    // 5. Send the audio chunk over the WebSocket.
                    socket.send(event.data);
                }
            };

            // THIS IS A CRUCIAL FIX: This event fires when the recorder stops.
            // This is the correct place to close the WebSocket and microphone stream.
            mediaRecorder.onstop = () => {
                console.log("MediaRecorder stopped.");
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.close();
                }
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                // The socket's onclose event will handle the final UI update.
            };

            // 6. Start recording.
            mediaRecorder.start(500); // Create a chunk every 500ms
        };

        socket.onclose = (event) => {
            console.log("WebSocket connection closed:", event);
            // This is a safety net. If the socket closes for any reason, reset the UI.
            if (currentState !== 'idle') {
                updateUI('idle');
            }
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            addMessageToLog("Connection error. Please refresh the page.", 'agent-message');
            updateUI('idle');
        };

    }).catch(err => {
        console.error("Error getting microphone access:", err);
        addMessageToLog("Could not start recording. Please allow microphone access.", 'agent-message');
        updateUI('idle');
    });
}

function stopStreaming() {
    // This function is now much simpler and more reliable.
    // It just tells the MediaRecorder to stop.
    // The 'onstop' event handler will take care of closing everything else.
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// --- UI and Helper Functions ---

function addMessageToLog(text, type) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('chat-message', type);
    messageElement.textContent = text;
    chatLog.appendChild(messageElement);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function updateUI(state) {
    currentState = state;
    if (state === 'idle') {
        mainButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" x2="12" y1="19" y2="22"></line></svg>`;
        mainButton.classList.remove('btn-recording');
        mainButton.disabled = false;
    } else if (state === 'recording') {
        mainButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="10" height="10" x="7" y="7" rx="1"></rect></svg>`;
        mainButton.classList.add('btn-recording');
        mainButton.disabled = false;
    }
}

// --- Initial Load ---
addMessageToLog("Click the microphone to start streaming your voice to the server.", 'agent-message');
updateUI('idle');
