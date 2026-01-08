let currentPrediction = null;

function previewImage(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      document.getElementById("previewImg").src = e.target.result;
      document.getElementById("imagePreview").style.display = "block";
      document.getElementById("uploadPrompt").style.display = "none";
    };
    reader.readAsDataURL(file);
  }
}

async function predict() {
  const input = document.getElementById("imageInput");
  if (!input.files.length) {
    alert("Please upload an image");
    return;
  }

  const formData = new FormData();
  formData.append("image", input.files[0]);

  const resultDiv = document.getElementById("result");
  resultDiv.classList.remove("hidden");
  resultDiv.innerHTML = `
    <div style="text-align: center; padding: 20px;">
      <div class="spinner"></div>
      <p>⏳ Analyzing plant image...</p>
    </div>
  `;

  try {
    const res = await fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    
    // Store current prediction for "Add to History"
    currentPrediction = {
      ...data,
      image: document.getElementById("previewImg").src,
      timestamp: new Date().toLocaleString()
    };

    renderResult(data);
  } catch (error) {
    console.error(error);
    resultDiv.innerHTML = `<p style="color:red">Error: ${error.message}</p>`;
  }
}

function renderResult(data) {
  const resultDiv = document.getElementById("result");
  
  // Choose language-specific data
  const isTe = currentLanguage === 'te';
  const plantName = isTe ? (data.plant_te || data.plant) : data.plant;
  const description = isTe ? (data.details_te?.description || data.details.description) : data.details.description;
  const benefits = isTe ? (data.details_te?.benefits || data.details.benefits) : data.details.benefits;
  
  const benefitsHtml = Array.isArray(benefits) 
    ? benefits.map(benefit => `<li>${benefit}</li>`).join('')
    : "<li>No benefits listed.</li>";

  // Display result with potential low-confidence warning
  let confidenceWarning = "";
  if (data.confidence < 70) {
    if (isTe) {
      confidenceWarning = `
        <div class="low-confidence-warning">
          ⚠️ <strong>తక్కువ విశ్వాసం:</strong> ఈ ఫలితం గురించి AIకి పూర్తిగా ఖచ్చితంగా లేదు.
          ఉత్తమ ఖచ్చితత్వం కోసం, మొక్క బాగా వెలుతురులో మరియు ఫ్రేమ్ మధ్యలో ఉండేలా చూసుకోండి.
        </div>
      `;
    } else {
      confidenceWarning = `
        <div class="low-confidence-warning">
          ⚠️ <strong>Low Confidence:</strong> The AI is not entirely sure about this result. 
          For best accuracy, ensure the plant is well-lit and centered in the frame.
        </div>
      `;
    }
  }

  const labelSciName = isTe ? "శాస్త్రీయ నామం:" : "Scientific Name:";
  const labelDesc = isTe ? "వివరణ:" : "Description:";
  const labelBenefits = isTe ? "ఔషధ ప్రయోజనాలు:" : "Medicinal Benefits:";
  const btnHistory = isTe ? "⭐ చరిత్రకు జోడించు" : "⭐ Add to History";
  const btnNew = isTe ? "📷 కొత్త చిత్రాన్ని అప్‌లోడ్ చేయండి" : "📷 Upload New Image";
  const btnDelete = isTe ? "🗑️ ఫలితాన్ని క్లియర్ చేయండి" : "🗑️ Clear Result";
  const matchText = isTe ? "సరిపోలిక" : "Match";

  resultDiv.innerHTML = `
    ${confidenceWarning}
    <div class="result-header">
      <h2>🌿 ${plantName || 'Unknown'}</h2>
      <span class="confidence-badge">${data.confidence || 0}% ${matchText}</span>
    </div>
    
    <div class="result-body">
      <div class="info-group">
        <h3>${labelSciName}</h3>
        <p class="scientific-name"><em>${data.details.scientific_name || 'N/A'}</em></p>
      </div>
      
      <div class="info-group">
        <h3>${labelDesc}</h3>
        <p class="description">${description || ''}</p>
      </div>
      
      <div class="benefits-section">
        <h3>${labelBenefits}</h3>
        <ul>
          ${benefitsHtml}
        </ul>
      </div>

      <div class="action-buttons">
        <button class="btn-history" onclick="addToHistory()">${btnHistory}</button>
        <button class="btn-new" onclick="uploadNew()">${btnNew}</button>
        <button class="btn-delete" onclick="deleteImage()">${btnDelete}</button>
      </div>
    </div>
  `;
}

function deleteImage() {
  if (confirm("Clear current result and reset?")) {
    resetState();
  }
}

function uploadNew() {
  resetState();
  document.getElementById("imageInput").click();
}

function resetState() {
  document.getElementById("imageInput").value = "";
  document.getElementById("imagePreview").style.display = "none";
  document.getElementById("uploadPrompt").style.display = "block";
  document.getElementById("result").classList.add("hidden");
  currentPrediction = null;
}

function addToHistory() {
  if (!currentPrediction) return;

  const history = JSON.parse(localStorage.getItem("plantHistory") || "[]");
  
  // Check if this exact prediction (by timestamp or plant name) was just added
  const isDuplicate = history.some(item => 
    item.plant === currentPrediction.plant && 
    item.timestamp === currentPrediction.timestamp
  );

  if (isDuplicate) {
    alert("This discovery is already in your history!");
    return;
  }

  history.unshift(currentPrediction);
  localStorage.setItem("plantHistory", JSON.stringify(history));
  alert(`${currentPrediction.plant} added to history!`);
}

function showView(view) {
  const views = {
    identify: document.getElementById('identifyView'),
    history: document.getElementById('historyView'),
    model: document.getElementById('modelView')
  };
  
  // Update nav buttons active state
  document.querySelectorAll('.sidebar nav button').forEach(btn => btn.classList.remove('active'));
  
  // Hide all views first
  Object.values(views).forEach(el => el.classList.add('hidden'));
  
  // Show requested view
  if (view === 'identify') {
    document.getElementById('navIdentify').classList.add('active');
    views.identify.classList.remove('hidden');
  } else if (view === 'history') {
    document.getElementById('navHistory').classList.add('active');
    views.history.classList.remove('hidden');
    loadHistory();
  } else if (view === 'model') {
    document.getElementById('navModel').classList.add('active');
    views.model.classList.remove('hidden');
  }
}

function loadHistory() {
  const historyList = document.getElementById("historyList");
  const history = JSON.parse(localStorage.getItem("plantHistory") || "[]");

  if (history.length === 0) {
    historyList.innerHTML = '<p class="no-history">No history yet. Identify some plants!</p>';
    return;
  }

  historyList.innerHTML = history.map((item, index) => `
    <div class="history-item card">
      <img src="${item.image}" alt="${item.plant}">
      <div class="history-info">
        <h3>${item.plant}</h3>
        <p class="scientific"><em>${item.details.scientific_name}</em></p>
        <p class="time">${item.timestamp}</p>
        <button class="btn-delete-small" onclick="deleteHistoryItem(${index})">Delete</button>
      </div>
    </div>
  `).join('');
}

function deleteHistoryItem(index) {
  if (confirm("Delete this item from history?")) {
    const history = JSON.parse(localStorage.getItem("plantHistory") || "[]");
    history.splice(index, 1);
    localStorage.setItem("plantHistory", JSON.stringify(history));
    loadHistory();
  }
}

// --- CHATBOT FUNCTIONALITY ---
let currentLanguage = 'en'; // Default language

function setLanguage(lang) {
  console.log("Switching language to:", lang);
  currentLanguage = lang;
  
  // Update UI buttons
  document.getElementById('langEn').classList.toggle('active', lang === 'en');
  document.getElementById('langTe').classList.toggle('active', lang === 'te');
  
  // Update placeholder based on language
  const input = document.getElementById("chatInput");
  if (lang === 'te') {
    input.placeholder = "జ్వరం, చర్మం మొదలైన వాటి గురించి అడగండి...";
  } else {
    input.placeholder = "Ask about fever, skin, etc...";
  }
  
  // Update all existing bot messages to the selected language
  const messages = document.querySelectorAll('.message.bot');
  messages.forEach(msg => {
    const wrapper = msg.closest('.message-wrapper');
    const enText = wrapper.getAttribute('data-en');
    const teText = wrapper.getAttribute('data-te');
    
    if (enText && teText) {
      const textToDisplay = (lang === 'te' && teText) ? teText : enText;
      let formattedText = textToDisplay
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
      msg.innerHTML = formattedText;
    }
  });

  // Also refresh the identification result if it's visible
  const resultDiv = document.getElementById("result");
  if (!resultDiv.classList.contains("hidden") && currentPrediction) {
    renderResult(currentPrediction);
  }
}

function toggleChat() {
  const chatbot = document.getElementById("chatbot");
  chatbot.classList.toggle("minimized");
  const toggleBtn = chatbot.querySelector(".chat-toggle");
  toggleBtn.textContent = chatbot.classList.contains("minimized") ? "+" : "−";
}

function handleChatKey(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
}

async function sendMessage() {
  const input = document.getElementById("chatInput");
  const text = input.value.trim();
  if (!text) return;

  // Add user message
  addMessage(text, "user");
  input.value = "";

  // Show typing indicator
  const typingId = "typing-" + Date.now();
  const thinkingEn = "Thinking...";
  const thinkingTe = "ఆలోచిస్తున్నాను...";
  addMessage(thinkingEn, "bot", typingId, thinkingTe);

  try {
    const data = await getBotResponse(text);
    
    // Remove typing indicator and add bot response
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    
    // Add bot message with both English and Telugu content for voice
    addMessage(data.response, "bot", null, data.response_te);
  } catch (error) {
    console.error("Chat error:", error);
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    addMessage("Sorry, I encountered an error. Please try again.", "bot");
  }
}

function addMessage(text, sender, id = null, textTe = null) {
  const messagesDiv = document.getElementById("chatMessages");
  const msgWrapper = document.createElement("div");
  msgWrapper.className = `message-wrapper ${sender}`;
  if (id) msgWrapper.id = id;
  
  // Store both languages for switching later
  if (sender === "bot" && textTe) {
    msgWrapper.setAttribute('data-en', text);
    msgWrapper.setAttribute('data-te', textTe);
  }

  const msgEl = document.createElement("div");
  msgEl.className = `message ${sender}`;
  
  // Decide which text to show initially
  const initialText = (sender === "bot" && currentLanguage === 'te' && textTe) ? textTe : text;
  
  // Basic markdown to HTML conversion for bold and newlines
  let formattedText = initialText
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
    
  msgEl.innerHTML = formattedText;
  msgWrapper.appendChild(msgEl);

  // Add speaker buttons only for bot messages (and not for typing indicator)
  if (sender === "bot" && !id) {
    const btnContainer = document.createElement("div");
    btnContainer.className = "voice-btn-container";

    // English Voice Button
    const speakBtnEn = document.createElement("button");
    speakBtnEn.className = "voice-btn en";
    speakBtnEn.innerHTML = "EN 🔊";
    speakBtnEn.title = "Listen in English";
    speakBtnEn.onclick = () => toggleSpeech(text, speakBtnEn, "en-US");
    btnContainer.appendChild(speakBtnEn);

    // Telugu Voice Button
    if (textTe) {
      const speakBtnTe = document.createElement("button");
      speakBtnTe.className = "voice-btn te";
      speakBtnTe.innerHTML = "TE 🔊";
      speakBtnTe.title = "Listen in Telugu";
      speakBtnTe.onclick = () => toggleSpeech(textTe, speakBtnTe, "te-IN");
      btnContainer.appendChild(speakBtnTe);
      
      // Auto-speak if current language is Telugu and it's a new message
      if (currentLanguage === 'te') {
        // Optional: auto-play Telugu voice when it arrives
        // toggleSpeech(textTe, speakBtnTe, "te-IN");
      }
    }

    msgWrapper.appendChild(btnContainer);
  }

  messagesDiv.appendChild(msgWrapper);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

let currentButton = null;

function toggleSpeech(text, button, lang = "en-US") {
  const synth = window.speechSynthesis;

  // If already speaking or paused
  if (synth.speaking || synth.paused) {
    // If it's the same button
    if (currentButton === button) {
      if (synth.paused) {
        synth.resume();
        button.innerHTML = button.innerHTML.replace(/[🔊▶️]/, "⏸️");
      } else {
        synth.pause();
        button.innerHTML = button.innerHTML.replace(/[🔊⏸️]/, "▶️");
      }
      return;
    } else {
      // If a different button is clicked, stop current and start new
      synth.cancel();
      if (currentButton) {
        currentButton.innerHTML = currentButton.innerHTML.replace(/[⏸️▶️]/, "🔊");
      }
    }
  }

  // Start new speech
  // Remove markdown, emojis, underscores, and extra whitespace for cleaner speech
  let cleanText = text
    .replace(/\*\*/g, "")
    .replace(/🌿/g, "")
    .replace(/_/g, " ") // Replace underscores with spaces so voice doesn't say "underscore"
    .replace(/<br>/g, " ")
    .replace(/<strong>/g, "")
    .replace(/<\/strong>/g, "")
    .replace(/\s+/g, " ")
    .trim();

  // For Telugu, remove only common non-Telugu symbols but keep letters/numbers in case of fallback
  if (lang === "te-IN") {
    // Just remove the specific emojis and markdown that we know don't speak well
    cleanText = cleanText.replace(/[🌿\*]/g, "");
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = lang;
  utterance.rate = 0.9; // Slightly slower for better clarity
  utterance.pitch = 1.0;
  
  utterance.onstart = () => {
    button.innerHTML = button.innerHTML.replace("🔊", "⏸️");
    currentButton = button;
  };

  utterance.onend = () => {
    button.innerHTML = button.innerHTML.replace(/[⏸️▶️]/, "🔊");
    currentButton = null;
  };

  utterance.onerror = (event) => {
    console.error("SpeechSynthesisUtterance error:", event);
    button.innerHTML = button.innerHTML.replace(/[⏸️▶️]/, "🔊");
    currentButton = null;
    synth.cancel();
  };

  const speakWithVoice = () => {
    const voices = synth.getVoices();
    let selectedVoice = null;

    if (lang === "te-IN") {
      // Try multiple ways to find a Telugu voice
      selectedVoice = voices.find(v => 
        v.lang === "te-IN" || 
        v.lang.startsWith("te") || 
        v.name.toLowerCase().includes("telugu")
      );
    } else {
      // Preferred English voices
      selectedVoice = voices.find(v => 
        (v.name.includes("Female") || 
         v.name.includes("Google UK English Female") || 
         v.name.includes("Microsoft Zira") || 
         v.name.includes("Samantha")) && 
        v.lang.startsWith("en")
      );
      if (!selectedVoice) {
        selectedVoice = voices.find(v => v.lang.startsWith("en"));
      }
    }
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    // Crucial: cancel any existing speech before starting new one
    synth.cancel();
    
    // Some browsers need a tiny delay after cancel
    setTimeout(() => {
      synth.speak(utterance);
    }, 50);
  };

  // If voices are already loaded, speak immediately
  if (synth.getVoices().length > 0) {
    speakWithVoice();
  } else {
    // Wait for voices to be loaded
    const voicesChangedHandler = () => {
      speakWithVoice();
      synth.removeEventListener('voiceschanged', voicesChangedHandler);
    };
    synth.addEventListener('voiceschanged', voicesChangedHandler);
    
    // Fallback if voiceschanged never fires
    setTimeout(() => {
      if (synth.getVoices().length === 0) {
        speakWithVoice();
      }
    }, 1000);
  }
}

async function getBotResponse(query) {
  try {
    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ query: query })
    });

    if (!res.ok) throw new Error("Chat server error");
    return await res.json();
  } catch (error) {
    console.error("Chat error:", error);
    return {
      response: "I'm having trouble connecting to my knowledge base, but I'm here to help!",
      response_te: "క్షమించండి, సర్వర్‌తో కనెక్ట్ కావడంలో సమస్య ఉంది."
    };
  }
}

function clearHistory() {
  if (confirm("Clear all history?")) {
    localStorage.removeItem("plantHistory");
    loadHistory();
  }
}
