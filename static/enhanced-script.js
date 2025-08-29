// Enhanced Voice AI Assistant v2.0 - Complete Implementation
let ws;
let sessionId = null;
let conversationHistory = [];

// UI references - Updated for new interface
const recordButton = document.getElementById("record-button");
const buttonIcon = document.getElementById("button-icon");
const statusText = document.getElementById("status-text");
const statusSubtext = document.getElementById("status-subtext");
const transcriptContainer = document.getElementById("transcript-container");
const userTranscriptText = document.getElementById("user-transcript-text");
const responseContainer = document.getElementById("response-container");
const llmResponseText = document.getElementById("llm-response-text");
const personaSelect = document.getElementById("persona");
const historyContainer = document.getElementById("history-container");
const clearHistoryBtn = document.getElementById("clear-history-btn");
const audioStatus = document.getElementById("audio-status");

// State management
let recognition = null;
let audioBuffer = "";
let finalText = "";
let isRecognitionActive = false;
let manualStop = false;
let recognitionTimeout = null;
let currentUserMessage = "";
let currentBotMessage = "";
let sessionStats = { totalMessages: 0, currentPersona: "default" };

function wsUrl(path) {
  const isSecure = window.location.protocol === "https:";
  return `${isSecure ? "wss" : "ws"}://${window.location.host}${path}`;
}

// ---- Button State Management ----
function updateButtonState(state) {
  // Clear all state classes
  recordButton.classList.remove("recording", "processing", "speaking");
  
  switch (state) {
    case "idle":
      buttonIcon.textContent = "🎤";
      statusText.textContent = "Ready to Listen";
      statusSubtext.textContent = "Click the microphone to start recording";
      break;
      
    case "recording":
      recordButton.classList.add("recording");
      buttonIcon.textContent = "⏹️";
      statusText.textContent = "Recording...";
      statusSubtext.textContent = "Speak now, click to stop";
      break;
      
    case "processing":
      recordButton.classList.add("processing");
      buttonIcon.textContent = "⏳";
      statusText.textContent = "Processing...";
      statusSubtext.textContent = "AI is thinking about your request";
      break;
      
    case "responding":
      recordButton.classList.add("speaking");
      buttonIcon.textContent = "🔊";
      statusText.textContent = "AI Speaking";
      statusSubtext.textContent = "Listen to the response";
      break;
      
    case "error":
      buttonIcon.textContent = "❌";
      statusText.textContent = "Error Occurred";
      statusSubtext.textContent = "Please try again";
      break;
  }
}

// ---- History Management ----
function addToHistory(userMessage, botMessage, persona) {
  const timestamp = new Date().toLocaleTimeString();
  const historyItem = {
    id: Date.now(),
    user: userMessage,
    bot: botMessage,
    persona: persona,
    timestamp: timestamp,
    messageNumber: conversationHistory.length + 1
  };
  
  conversationHistory.push(historyItem);
  sessionStats.totalMessages++;
  updateHistoryDisplay();
  saveHistoryToLocalStorage();
  console.log("📜 Added to history:", historyItem);
}

function updateHistoryDisplay() {
  if (conversationHistory.length === 0) {
    historyContainer.innerHTML = "No conversations yet. Configure your API keys and start talking!";
    return;
  }
  
  historyContainer.innerHTML = conversationHistory.map(item => `
    <div class="history-item">
      <div class="history-user">#${item.messageNumber} You: ${item.user}</div>
      <div class="history-bot">${item.bot}</div>
      <div class="history-meta">Persona: ${item.persona} • ${item.timestamp}</div>
    </div>
  `).join('');
  
  historyContainer.scrollTop = historyContainer.scrollHeight;
}

function clearHistory() {
  conversationHistory = [];
  sessionStats.totalMessages = 0;
  updateHistoryDisplay();
  localStorage.removeItem('voiceAgent_history');
  console.log("📜 History cleared");
}

function saveHistoryToLocalStorage() {
  try {
    const saveData = {
      conversations: conversationHistory,
      stats: sessionStats,
      lastUpdated: new Date().toISOString()
    };
    localStorage.setItem('voiceAgent_history', JSON.stringify(saveData));
  } catch (error) {
    console.warn("Could not save history:", error);
  }
}

function loadHistoryFromLocalStorage() {
  try {
    const saved = localStorage.getItem('voiceAgent_history');
    if (saved) {
      const data = JSON.parse(saved);
      conversationHistory = data.conversations || [];
      sessionStats = data.stats || { totalMessages: 0, currentPersona: "default" };
      updateHistoryDisplay();
      console.log("📜 Loaded history:", conversationHistory.length, "conversations");
    }
  } catch (error) {
    console.warn("Could not load history:", error);
    conversationHistory = [];
  }
}

// ---- Audio Status Management ----
function showAudioStatus(message, type = "info") {
  audioStatus.textContent = message;
  audioStatus.classList.remove("hidden");
  
  audioStatus.classList.remove("speaking");
  
  if (type === "speaking") {
    audioStatus.classList.add("speaking");
  }
}

function hideAudioStatus() {
  audioStatus.classList.add("hidden");
  audioStatus.classList.remove("speaking");
}

// ---- Browser TTS ----
function speakTextWithBrowserTTS(text, persona = "default") {
  if (!('speechSynthesis' in window)) {
    showAudioStatus("❌ Browser TTS not supported", "error");
    return false;
  }

  try {
    speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = speechSynthesis.getVoices();
    
    const personaConfigs = {
      "friendly_teacher": {
        rate: 0.85, pitch: 1.1, volume: 0.9,
        displayName: "Friendly Teacher"
      },
      "tech_support": {
        rate: 0.95, pitch: 0.9, volume: 0.9,
        displayName: "Tech Support"
      },
      "storyteller": {
        rate: 0.8, pitch: 1.2, volume: 0.9,
        displayName: "Storyteller"
      },
      "default": {
        rate: 0.9, pitch: 1.0, volume: 0.9,
        displayName: "Assistant"
      }
    };

    const config = personaConfigs[persona] || personaConfigs["default"];
    
    utterance.rate = config.rate;
    utterance.pitch = config.pitch;
    utterance.volume = config.volume;
    
    utterance.onstart = () => {
      console.log(`🔊 TTS started (${persona})`);
      updateButtonState("responding");
      showAudioStatus(`🔊 ${config.displayName} is speaking...`, "speaking");
    };
    
    utterance.onend = () => {
      console.log("🔊 TTS completed");
      updateButtonState("idle");
      showAudioStatus(`✅ ${config.displayName} finished speaking`);
      setTimeout(() => hideAudioStatus(), 3000);
    };
    
    utterance.onerror = (event) => {
      console.error("❌ TTS error:", event.error);
      updateButtonState("error");
      showAudioStatus(`❌ Voice error: ${event.error}`);
      setTimeout(() => updateButtonState("idle"), 3000);
    };
    
    speechSynthesis.speak(utterance);
    return true;
    
  } catch (error) {
    console.error("❌ TTS failed:", error);
    updateButtonState("error");
    showAudioStatus("❌ Voice playback failed");
    setTimeout(() => updateButtonState("idle"), 3000);
    return false;
  }
}

// ---- API Configuration Functions ----
function updateApiStatus() {
  const geminiStatus = document.getElementById('gemini-status');
  const weatherStatus = document.getElementById('weather-status');
  const searchStatus = document.getElementById('search-status');
  
  if (geminiStatus) geminiStatus.classList.toggle('active', hasApiKey('gemini'));
  if (weatherStatus) weatherStatus.classList.toggle('active', hasApiKey('openweather'));
  if (searchStatus) searchStatus.classList.toggle('active', hasApiKey('tavily'));
}

function hasApiKey(service) {
  const stored = localStorage.getItem(`api_key_${service}`);
  return stored && stored.length > 10;
}

function openSettings() {
  const settingsPanel = document.getElementById('settings-panel');
  const settingsOverlay = document.querySelector('.settings-overlay');
  
  if (settingsPanel && settingsOverlay) {
    settingsPanel.classList.add('open');
    settingsOverlay.classList.add('visible');
    loadExistingApiKeys();
  }
}

function closeSettings() {
  const settingsPanel = document.getElementById('settings-panel');
  const settingsOverlay = document.querySelector('.settings-overlay');
  
  if (settingsPanel && settingsOverlay) {
    settingsPanel.classList.remove('open');
    settingsOverlay.classList.remove('visible');
  }
}

function loadExistingApiKeys() {
  const geminiKey = localStorage.getItem('api_key_gemini');
  const openweatherKey = localStorage.getItem('api_key_openweather');
  const tavilyKey = localStorage.getItem('api_key_tavily');
  
  const geminiInput = document.getElementById('gemini-key');
  const openweatherInput = document.getElementById('openweather-key');
  const tavilyInput = document.getElementById('tavily-key');
  
  if (geminiInput && geminiKey) geminiInput.value = geminiKey;
  if (openweatherInput && openweatherKey) openweatherInput.value = openweatherKey;
  if (tavilyInput && tavilyKey) tavilyInput.value = tavilyKey;
  
  updateConfigStatus();
}

function updateConfigStatus() {
  const services = ['gemini', 'openweather', 'tavily'];
  
  services.forEach(service => {
    const statusElement = document.getElementById(`${service}-config-status`);
    const hasKey = hasApiKey(service);
    
    if (statusElement) {
      statusElement.classList.toggle('configured', hasKey);
    }
  });
}

async function saveApiKeys() {
  const geminiKey = document.getElementById('gemini-key')?.value?.trim();
  const openweatherKey = document.getElementById('openweather-key')?.value?.trim();
  const tavilyKey = document.getElementById('tavily-key')?.value?.trim();
  
  const apiKeys = {};
  if (geminiKey) apiKeys.gemini = geminiKey;
  if (openweatherKey) apiKeys.openweather = openweatherKey;
  if (tavilyKey) apiKeys.tavily = tavilyKey;
  
  const saveButton = document.querySelector('.save-settings-btn');
  if (saveButton) {
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';
  }
  
  try {
    const response = await fetch(`/session/${sessionId}/api-keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(apiKeys)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to save API keys: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Save to localStorage for persistence
    Object.entries(apiKeys).forEach(([key, value]) => {
      localStorage.setItem(`api_key_${key}`, value);
    });
    
    showSuccessMessage(`✅ ${result.configured_keys.length} API key(s) configured successfully!`);
    
    updateApiStatus();
    updateConfigStatus();
    
    setTimeout(() => {
      closeSettings();
    }, 2000);
    
    console.log('✅ API keys saved:', result.configured_keys);
    
  } catch (error) {
    console.error('❌ Failed to save API keys:', error);
    showErrorMessage('Failed to save API keys. Please try again.');
  } finally {
    if (saveButton) {
      saveButton.disabled = false;
      saveButton.textContent = '💾 Save Configuration';
    }
  }
}

function showSuccessMessage(message) {
  const successElement = document.getElementById('success-message');
  if (successElement) {
    successElement.textContent = message;
    successElement.classList.remove('hidden');
    
    setTimeout(() => {
      successElement.classList.add('hidden');
    }, 5000);
  }
}

function showErrorMessage(message) {
  console.error(message);
  alert(message);
}

async function checkSessionStatus() {
  if (!sessionId) return;
  
  try {
    const response = await fetch(`/session/${sessionId}/status`);
    if (response.ok) {
      const status = await response.json();
      updateApiStatusFromServer(status.available_features);
    }
  } catch (error) {
    console.warn('Could not check session status:', error);
  }
}

function updateApiStatusFromServer(features) {
  const geminiStatus = document.getElementById('gemini-status');
  const weatherStatus = document.getElementById('weather-status');
  const searchStatus = document.getElementById('search-status');
  
  if (geminiStatus) geminiStatus.classList.toggle('active', features.ai_chat);
  if (weatherStatus) weatherStatus.classList.toggle('active', features.weather);
  if (searchStatus) searchStatus.classList.toggle('active', features.web_search);
}

// ---- System Functions ----
async function loadVoices() {
  return new Promise((resolve) => {
    if (speechSynthesis.getVoices().length > 0) {
      resolve();
      return;
    }
    speechSynthesis.onvoiceschanged = () => resolve();
  });
}

async function testMicrophone() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch (error) {
    console.error("❌ Microphone error:", error);
    return false;
  }
}

function checkBrowserCompatibility() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("❌ Speech Recognition not supported. Please use Google Chrome.");
    return false;
  }
  return true;
}

// ---- Main Initialization ----
async function init() {
  console.log("🚀 Initializing Enhanced Voice Agent v2.0...");
  
  loadHistoryFromLocalStorage();
  
  if (!checkBrowserCompatibility()) return;
  await testMicrophone();
  await loadVoices();
  
  try {
    const resp = await fetch("/session");
    if (!resp.ok) throw new Error(`Session creation failed: ${resp.status}`);
    
    const data = await resp.json();
    sessionId = data.session_id;
    console.log("✅ Session created:", sessionId);

    ws = new WebSocket(wsUrl(`/ws/${sessionId}`));

    ws.onopen = () => {
      console.log("✅ WebSocket connected");
      
      setTimeout(() => {
        if (personaSelect && ws.readyState === WebSocket.OPEN) {
          const initialPersona = personaSelect.value;
          ws.send(JSON.stringify({ type: "persona", persona: initialPersona }));
          console.log("📤 Initial persona sent:", initialPersona);
          sessionStats.currentPersona = initialPersona;
        }
        
        // Check session status and update API indicators
        checkSessionStatus();
        updateApiStatus();
      }, 1000);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("📥 Server message:", msg.type);

        switch (msg.type) {
          case "ack_transcript":
            updateButtonState("processing");
            break;

          case "final":
            currentUserMessage = msg.text;
            userTranscriptText.textContent = msg.text;
            transcriptContainer.classList.remove("hidden");
            break;

          case "llm_response":
            currentBotMessage = msg.text;
            llmResponseText.textContent = msg.text;
            responseContainer.classList.remove("hidden");
            
            const currentPersona = msg.persona || personaSelect.value || "default";
            
            if (currentUserMessage && currentBotMessage) {
              addToHistory(currentUserMessage, currentBotMessage, currentPersona);
            }
            
            // Update API status if provided
            if (msg.api_keys_status) {
              updateApiStatusFromServer({
                ai_chat: msg.api_keys_status.gemini,
                weather: msg.api_keys_status.openweather,
                web_search: msg.api_keys_status.tavily
              });
            }
            
            audioStatus.classList.remove("hidden");
            speakTextWithBrowserTTS(msg.text, currentPersona);
            
            if (msg.persona) {
              llmResponseText.textContent += `\n\n[Persona: ${msg.persona}]`;
            }
            break;

          case "audio_end":
            audioBuffer = "";
            updateButtonState("idle");
            break;

          case "error":
            console.error("❌ Server error:", msg.message);
            updateButtonState("error");
            showAudioStatus(`❌ ${msg.message}`);
            setTimeout(() => updateButtonState("idle"), 3000);
            break;
        }
      } catch (error) {
        console.error("❌ Error parsing message:", error);
      }
    };

    ws.onclose = (event) => {
      console.log("❌ WebSocket closed:", event.code, event.reason);
      updateButtonState("error");
      setTimeout(() => {
        console.log("🔄 Reconnecting...");
        init();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
      updateButtonState("error");
    };

  } catch (error) {
    console.error("❌ Initialization failed:", error);
    updateButtonState("error");
    alert("Failed to initialize. Please refresh the page.");
  }

  setupSpeechRecognition();
}

// ---- Speech Recognition ----
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    console.log("🎙️ Speech Recognition started");
    isRecognitionActive = true;
    manualStop = false;
    finalText = "";
    transcriptContainer.classList.remove("hidden");
    userTranscriptText.textContent = "(listening... speak now!)";
    updateButtonState("recording");
    
    clearTimeout(recognitionTimeout);
    recognitionTimeout = setTimeout(() => {
      if (isRecognitionActive) {
        try { recognition.stop(); } catch (e) {}
      }
    }, 15000);
  };

  recognition.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      
      if (event.results[i].isFinal) {
        finalText += transcript + " ";
      } else {
        interim += transcript;
      }
    }
    
    const combined = (finalText + " " + interim).trim();
    userTranscriptText.textContent = combined || "(listening... speak now!)";
  };

  recognition.onend = () => {
    console.log("🛑 Speech Recognition ended");
    isRecognitionActive = false;
    clearTimeout(recognitionTimeout);
    
    const text = finalText.trim();
    
    if (text && text.length >= 2) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        currentUserMessage = text;
        ws.send(JSON.stringify({ type: "user_transcript", text }));
        updateButtonState("processing");
      } else {
        userTranscriptText.textContent = "Connection error. Please try again.";
        updateButtonState("error");
        setTimeout(() => updateButtonState("idle"), 3000);
      }
    } else {
      if (!manualStop) {
        userTranscriptText.textContent = "I didn't catch that. Please try again.";
        updateButtonState("error");
        setTimeout(() => updateButtonState("idle"), 3000);
      } else {
        updateButtonState("idle");
      }
    }
    
    manualStop = false;
  };

  recognition.onerror = (event) => {
    console.error("❌ Speech Recognition error:", event.error);
    isRecognitionActive = false;
    clearTimeout(recognitionTimeout);
    
    const errorMessages = {
      "no-speech": "No speech detected. Please try again.",
      "network": "Network error. Check your connection.",
      "not-allowed": "Microphone access denied. Please allow microphone access.",
    };
    
    const errorMsg = errorMessages[event.error] || `Speech error: ${event.error}`;
    userTranscriptText.textContent = errorMsg;
    transcriptContainer.classList.remove("hidden");
    updateButtonState("error");
    setTimeout(() => updateButtonState("idle"), 3000);
  };
}

function resetUI() {
  userTranscriptText.textContent = "";
  llmResponseText.textContent = "";
  transcriptContainer.classList.add("hidden");
  responseContainer.classList.add("hidden");
  audioBuffer = "";
  finalText = "";
  currentUserMessage = "";
  currentBotMessage = "";
  
  if (isRecognitionActive && recognition) {
    try {
      manualStop = true;
      recognition.stop();
    } catch (e) {}
  }
  
  isRecognitionActive = false;
  speechSynthesis.cancel();
  hideAudioStatus();
  updateButtonState("idle");
}

// ---- Event Listeners ----
recordButton.addEventListener("click", async () => {
  console.log("🎙️ Record button clicked, isActive:", isRecognitionActive);
  
  if (!recognition) {
    alert("Speech Recognition not available. Please use Chrome.");
    return;
  }
  
  if (isRecognitionActive) {
    console.log("⏹️ Stopping current recording");
    try {
      manualStop = true;
      recognition.stop();
    } catch (e) {}
    return;
  }
  
  resetUI();
  updateButtonState("recording");
  
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
    recognition.start();
  } catch (err) {
    console.error("❌ Microphone permission error:", err);
    updateButtonState("error");
    userTranscriptText.textContent = "Microphone permission denied.";
    transcriptContainer.classList.remove("hidden");
    setTimeout(() => updateButtonState("idle"), 3000);
  }
});

personaSelect.addEventListener("change", (e) => {
  const persona = e.target.value;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "persona", persona }));
  }
});

clearHistoryBtn.addEventListener("click", () => {
  if (confirm("Clear all conversation history? This cannot be undone.")) {
    clearHistory();
  }
});

// ---- Settings Panel Event Listeners ----
document.addEventListener('DOMContentLoaded', () => {
  // Settings button
  const settingsButton = document.querySelector('.settings-button');
  if (settingsButton) {
    settingsButton.addEventListener('click', openSettings);
  }
  
  // Close settings button
  const closeSettingsButton = document.querySelector('.close-settings');
  if (closeSettingsButton) {
    closeSettingsButton.addEventListener('click', closeSettings);
  }
  
  // Save settings button
  const saveSettingsButton = document.querySelector('.save-settings-btn');
  if (saveSettingsButton) {
    saveSettingsButton.addEventListener('click', saveApiKeys);
  }
  
  // Configure links
  const configureLinks = document.querySelectorAll('.configure-link');
  configureLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      openSettings();
    });
  });
  
  // Settings overlay
  const settingsOverlay = document.querySelector('.settings-overlay');
  if (settingsOverlay) {
    settingsOverlay.addEventListener('click', closeSettings);
  }
  
  // Initial status update
  updateApiStatus();
});

// ---- Keyboard Shortcuts ----
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    speechSynthesis.cancel();
    hideAudioStatus();
    closeSettings();
    if (isRecognitionActive && recognition) {
      try {
        manualStop = true;
        recognition.stop();
      } catch (e) {}
    }
    updateButtonState("idle");
  }
  
  if (event.key === " " && event.target === document.body && !isRecognitionActive) {
    event.preventDefault();
    recordButton.click();
  }
  
  if (event.key === "r" && !isRecognitionActive) {
    event.preventDefault();
    recordButton.click();
  }
});

// ---- Initialize ----
window.addEventListener("load", init);

console.log("📄 Enhanced Voice Agent v2.0 System Loaded Successfully! 🚀");
