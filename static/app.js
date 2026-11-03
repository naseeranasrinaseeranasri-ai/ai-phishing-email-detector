// Show whether Ollama is running
async function loadStatus() {
  const box = document.getElementById("ollama-status");
  if (!box) return;
  try {
    const resp = await fetch("/status");
    const s = await resp.json();
    const ready = s.running && s.model_installed;
    box.className = "status " + (ready ? "ok" : "bad");
    box.textContent = (ready ? "Ollama ready" : "Ollama problem") +
      " | model: " + s.model + " | " + s.message;
  } catch (err) {
    box.className = "status bad";
    box.textContent = "Could not check Ollama status.";
  }
}

// Show a loading message while the analysis runs
function setupLoading() {
  const form = document.getElementById("analyze-form");
  if (!form) return;
  form.addEventListener("submit", function () {
    const btn = document.getElementById("analyze-btn");
    const msg = document.getElementById("loading");
    btn.disabled = true;
    btn.textContent = "Analyzing...";
    msg.hidden = false;
  });
}

loadStatus();
setupLoading();