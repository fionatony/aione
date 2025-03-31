// Main JavaScript for Ollama Web Interface

document.addEventListener("DOMContentLoaded", function () {
  // DOM elements
  const modelsList = document.getElementById("models-list");
  const modelInput = document.getElementById("model-input");
  const installModelBtn = document.getElementById("install-model-btn");
  const refreshModelsBtn = document.getElementById("refresh-models-btn");
  const installationProgress = document.getElementById("installation-progress");
  const progressBar = installationProgress.querySelector(".progress-bar");
  const installationStatus = document.getElementById("installation-status");
  const commandInput = document.getElementById("command-input");
  const executeCommandBtn = document.getElementById("execute-command-btn");
  const commandOutput = document.getElementById("command-output");
  const quickCommands = document.querySelectorAll(".quick-command");
  const chatModelSelect = document.getElementById("chat-model-select");
  const chatMessages = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");
  const sendMessageBtn = document.getElementById("send-message-btn");

  // Available models data storage
  let availableModels = {};

  // Initialize
  loadModels();
  loadAvailableModels();
  loadGpuInfo();
  setupEventListeners();
  setupProgressChecker();

  // Load models into the table and chat selector
  function loadModels() {
    fetch("/api/models")
      .then((response) => response.json())
      .then((data) => {
        updateModelsTable(data.models);
        updateChatModelSelect(data.models);
      })
      .catch((error) => {
        console.error("Error loading models:", error);
        modelsList.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error loading models: ${error.message}</td></tr>`;
      });
  }

  // Load available models from models.json
  function loadAvailableModels() {
    fetch("/api/models/available")
      .then((response) => response.json())
      .then((data) => {
        availableModels = data;

        // If model input has a datalist, let's update it
        let datalist = document.getElementById("available-models");
        if (!datalist) {
          datalist = document.createElement("datalist");
          datalist.id = "available-models";
          document.body.appendChild(datalist);
          modelInput.setAttribute("list", "available-models");
        }

        // Clear datalist
        datalist.innerHTML = "";

        // Add all available models as options
        let allModels = [];
        for (const category in availableModels) {
          if (Array.isArray(availableModels[category])) {
            allModels = allModels.concat(availableModels[category]);
          }
        }

        // Remove duplicates
        allModels = [...new Set(allModels)];

        // Sort alphabetically
        allModels.sort();

        // Add to datalist
        allModels.forEach((model) => {
          const option = document.createElement("option");
          option.value = model;
          datalist.appendChild(option);
        });

        // Create or update model categories for suggestion display
        updateModelSuggestions();
      })
      .catch((error) => {
        console.error("Error loading available models:", error);
      });
  }

  // Load GPU information
  function loadGpuInfo() {
    const gpuInfoElement = document.getElementById("gpu-info");
    if (!gpuInfoElement) return;

    gpuInfoElement.innerHTML = `<p>Loading GPU information...</p>`;

    fetch("/api/system/gpu")
      .then((response) => response.json())
      .then((data) => {
        let html = "";

        // Check if there's an error
        if (data.error) {
          html = `<div class="alert alert-warning">Error getting GPU info: ${data.error}</div>`;
        }
        // Check for NVIDIA GPUs
        else if (
          data.nvidia_available &&
          data.nvidia_gpus &&
          data.nvidia_gpus.length > 0
        ) {
          html = `<div class="alert alert-success">NVIDIA GPU hardware detected and available for Ollama</div>`;
          html += `<div class="card mb-3">
                    <div class="card-header bg-success text-white">
                      <strong>NVIDIA GPUs Available: ${data.nvidia_gpus.length}</strong>
                    </div>
                    <ul class="list-group list-group-flush">`;

          data.nvidia_gpus.forEach((gpu, index) => {
            html += `<li class="list-group-item">
                      <div class="d-flex justify-content-between align-items-center">
                        <strong>${gpu.name || "GPU " + (index + 1)}</strong>
                        <span class="badge bg-primary">${
                          gpu.temperature || "N/A"
                        }</span>
                      </div>
                      <div class="mt-2 d-flex justify-content-between">
                        <small>Memory: ${gpu.memory_used || "0MB"} / ${
              gpu.memory_total || "Unknown"
            }</small>
                      </div>
                    </li>`;
          });

          html += `</ul></div>`;
        }
        // Check for AMD GPUs
        else if (
          data.amd_available &&
          data.amd_gpus &&
          data.amd_gpus.length > 0
        ) {
          html = `<div class="alert alert-success">AMD GPU hardware detected and available for Ollama</div>`;
          html += `<div class="card mb-3">
                    <div class="card-header bg-success text-white">
                      <strong>AMD GPUs Available: ${data.amd_gpus.length}</strong>
                    </div>
                    <ul class="list-group list-group-flush">`;

          data.amd_gpus.forEach((gpu, index) => {
            html += `<li class="list-group-item">
                      <div class="d-flex justify-content-between align-items-center">
                        <strong>${gpu.name || "GPU " + (index + 1)}</strong>
                        <span class="badge bg-primary">${
                          gpu.device_id || "N/A"
                        }</span>
                      </div>
                      <div class="mt-2 d-flex justify-content-between">
                        <small>Memory: ${gpu.memory_used || "0MB"} / ${
              gpu.memory_total || "Unknown"
            }</small>
                      </div>
                    </li>`;
          });

          html += `</ul></div>`;
        }
        // When CPU info is available but no GPUs
        else if (data.cpu_info) {
          html = `<div class="alert alert-warning">No GPU detected. Models will run on CPU only.</div>`;

          html += `<div class="card mb-3">
                    <div class="card-header bg-secondary text-white">
                      <strong>CPU Information</strong>
                    </div>
                    <div class="card-body">
                      <p><strong>Model:</strong> ${
                        data.cpu_info.model || "Unknown"
                      }</p>
                      <p><strong>Cores:</strong> ${
                        data.cpu_info.cores || "Unknown"
                      }</p>
                    </div>
                  </div>`;

          html += `<div class="mt-3">
                    <h6>To enable GPU acceleration:</h6>
                    <ol>
                      <li>Ensure you have a compatible NVIDIA GPU installed</li>
                      <li>Install the NVIDIA Container Toolkit on your host machine</li>
                      <li>Run Docker with the <code>--gpus all</code> flag</li>
                    </ol>
                    <a href="https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html" 
                       target="_blank" class="btn btn-sm btn-outline-primary">
                      Learn How to Install NVIDIA Container Toolkit
                    </a>
                  </div>`;
        }
        // Fallback case for any other data format
        else {
          html = `<div class="alert alert-warning">No GPU detected or GPU information unavailable.</div>`;
          html += `<p>To use GPU acceleration:</p>`;
          html += `<ol>
                    <li>Make sure you have compatible GPU hardware</li>
                    <li>Install appropriate drivers</li>
                    <li>Run Docker with GPU flags: <code>docker run --gpus all</code></li>
                  </ol>`;
        }

        gpuInfoElement.innerHTML = html;
      })
      .catch((error) => {
        console.error("Error loading GPU info:", error);
        gpuInfoElement.innerHTML = `<div class="alert alert-danger">Error loading GPU information: ${error.message}</div>`;
      });
  }

  // Format memory size for display
  function formatMemory(bytes) {
    if (bytes < 1024 * 1024 * 1024) {
      return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    } else {
      return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
    }
  }

  // Update the model suggestions UI
  function updateModelSuggestions() {
    const modelSuggestionsContainer =
      document.getElementById("model-suggestions");
    if (!modelSuggestionsContainer) return;

    let html = "";

    // Categories to display (in order)
    const categoriesToDisplay = [
      { key: "popular", label: "Popular Models" },
      { key: "Small Models (3-4B)", label: "Small Models (3-4B)" },
      { key: "Medium Models (7-14B)", label: "Medium Models (7-14B)" },
      { key: "code", label: "Code Models" },
    ];

    categoriesToDisplay.forEach((category) => {
      if (
        availableModels[category.key] &&
        availableModels[category.key].length > 0
      ) {
        html += `<div class="mb-3">
                  <h6>${category.label}:</h6>
                  <div class="d-flex flex-wrap gap-2">`;

        // Display up to 6 models from this category
        availableModels[category.key].slice(0, 12).forEach((model) => {
          html += `<button class="btn btn-sm btn-outline-secondary model-suggestion" 
                    data-model="${model}">${model}</button>`;
        });

        html += "</div></div>";
      }
    });

    // Display a button to show all models in a modal if we implement that later
    html += `<div class="text-end mt-2">
              <button class="btn btn-sm btn-link" id="show-all-models">
                Show all available models
              </button>
            </div>`;

    modelSuggestionsContainer.innerHTML = html;

    // Add event listeners to suggestion buttons
    document.querySelectorAll(".model-suggestion").forEach((button) => {
      button.addEventListener("click", function () {
        modelInput.value = this.getAttribute("data-model");
      });
    });

    // Show all models button event listener - could open a modal in the future
    const showAllButton = document.getElementById("show-all-models");
    if (showAllButton) {
      showAllButton.addEventListener("click", function () {
        showAllModelsModal();
      });
    }
  }

  // Show all models in a modal
  function showAllModelsModal() {
    const modalContent = document.getElementById("all-models-content");
    let html = "";

    // Add search functionality with both local and remote search
    html = `
      <div class="mb-4">
        <div class="input-group">
          <input type="text" class="form-control" id="model-search" 
                 placeholder="Search models..." autocomplete="off">
          <button class="btn btn-outline-secondary" type="button" id="search-ollama">
            <i class="bi bi-search"></i> Search Ollama
          </button>
        </div>
        <div class="form-text">Search locally or on Ollama's website</div>
      </div>
      <div id="search-results" class="d-none">
        <h6 class="mb-3">Search Results</h6>
        <div id="ollama-search-results" class="mb-4"></div>
      </div>
      <div id="models-list-container">
        <h6 class="mb-3">Available Models</h6>
        <div class="d-flex flex-wrap gap-2">
    `;

    // Add all available models as buttons
    let allModels = [];
    for (const category in availableModels) {
      if (Array.isArray(availableModels[category])) {
        allModels = allModels.concat(availableModels[category]);
      }
    }

    // Remove duplicates and sort
    allModels = [...new Set(allModels)].sort();

    // Add model buttons
    allModels.forEach((model) => {
      html += `<button class="btn btn-sm btn-outline-secondary model-suggestion" 
                data-model="${model}">${model}</button>`;
    });

    html += `
        </div>
      </div>
    `;

    modalContent.innerHTML = html;

    // Add event listeners to suggestion buttons in modal
    modalContent.querySelectorAll(".model-suggestion").forEach((button) => {
      button.addEventListener("click", function () {
        const modelName = this.getAttribute("data-model");
        modelInput.value = modelName;
        // Close the modal
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("allModelsModal")
        );
        modal.hide();
      });
    });

    // Add local search functionality
    const searchInput = document.getElementById("model-search");
    if (searchInput) {
      searchInput.addEventListener("input", function () {
        const searchTerm = this.value.toLowerCase();
        const buttons = modalContent.querySelectorAll(".model-suggestion");
        const searchResults = document.getElementById("search-results");

        // Hide search results if search is empty
        if (!searchTerm) {
          searchResults.classList.add("d-none");
          return;
        }

        // Show search results section
        searchResults.classList.remove("d-none");

        // Filter local models
        buttons.forEach((button) => {
          const modelName = button.getAttribute("data-model").toLowerCase();
          if (modelName.includes(searchTerm)) {
            button.style.display = "inline-block";
          } else {
            button.style.display = "none";
          }
        });

        // If search term is long enough, trigger Ollama search
        if (searchTerm.length >= 2) {
          searchOllamaModels(searchTerm);
        }
      });
    }

    // Add Ollama search button functionality
    const searchOllamaBtn = document.getElementById("search-ollama");
    if (searchOllamaBtn) {
      searchOllamaBtn.addEventListener("click", function () {
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
          searchOllamaModels(searchTerm);
        }
      });
    }

    // Show the modal
    const modal = new bootstrap.Modal(
      document.getElementById("allModelsModal")
    );
    modal.show();
  }

  // Search models on Ollama's website
  function searchOllamaModels(searchTerm) {
    const searchResults = document.getElementById("ollama-search-results");
    searchResults.innerHTML =
      '<div class="text-center"><div class="spinner-border spinner-border-sm me-2" role="status"></div>Searching...</div>';

    // Use our backend API to proxy the request
    fetch(`/api/models/search?q=${encodeURIComponent(searchTerm)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          searchResults.innerHTML = `<div class="text-danger">Error: ${data.error}</div>`;
          return;
        }

        // Create an array to store model information
        const modelInfoArray = [];

        try {
          // Parse the HTML content from our backend
          const parser = new DOMParser();
          const doc = parser.parseFromString(data.html, "text/html");

          // Find all model items using the specific structure
          const modelItems = doc.querySelectorAll("li[x-test-model]");

          modelItems.forEach((item) => {
            // Get model name from the h2 element
            const modelNameElement = item.querySelector(
              "h2 span[x-test-search-response-title]"
            );
            if (!modelNameElement) return;

            const modelName = modelNameElement.textContent.trim();

            // Get model description
            const descriptionElement = item.querySelector("p.max-w-lg");
            const description = descriptionElement
              ? descriptionElement.textContent.trim()
              : "";

            // Get all size spans
            const sizeSpans = item.querySelectorAll("span[x-test-size]");

            if (sizeSpans.length > 0) {
              // For each size, create a full model name
              sizeSpans.forEach((span) => {
                const size = span.textContent.trim().toLowerCase();
                const fullModelName = `${modelName}:${size}`;
                modelInfoArray.push({
                  name: fullModelName,
                  description: description,
                });
              });
            } else {
              // If no sizes found, just use the model name
              modelInfoArray.push({
                name: modelName,
                description: description,
              });
            }
          });

          // Deduplicate models by name
          const uniqueModels = Array.from(
            new Set(modelInfoArray.map((model) => model.name))
          ).map((name) => {
            return modelInfoArray.find((model) => model.name === name);
          });

          // Display results
          if (uniqueModels.length > 0) {
            let resultsHtml = '<div class="list-group">';
            uniqueModels.slice(0, 8).forEach((model) => {
              resultsHtml += `
                <button class="list-group-item list-group-item-action model-suggestion" 
                        data-model="${model.name}">
                  <strong>${model.name}</strong>
                  <div class="small text-muted">${model.description}</div>
                </button>
              `;
            });
            resultsHtml += "</div>";
            searchResults.innerHTML = resultsHtml;

            // Add click handlers to the search result buttons
            searchResults
              .querySelectorAll(".model-suggestion")
              .forEach((button) => {
                button.addEventListener("click", function () {
                  const modelName = this.getAttribute("data-model");
                  modelInput.value = modelName;
                  const modal = bootstrap.Modal.getInstance(
                    document.getElementById("allModelsModal")
                  );
                  modal.hide();
                });
              });
          } else {
            searchResults.innerHTML =
              '<div class="text-muted">No models found. Try a different search term.</div>';
          }
        } catch (err) {
          console.error("Error parsing search results:", err);
          searchResults.innerHTML =
            '<div class="text-warning">Unable to parse search results. Try using a more specific search term.</div>';
        }
      })
      .catch((error) => {
        console.error("Error searching Ollama models:", error);
        searchResults.innerHTML =
          '<div class="text-danger">Error searching models. Please try again later.</div>';
      });
  }

  // Update the models table with current data
  function updateModelsTable(models) {
    if (!models || models.length === 0) {
      modelsList.innerHTML = `<tr><td colspan="4" class="text-center">No models installed</td></tr>`;
      return;
    }

    let html = "";
    models.forEach((model) => {
      html += `
                <tr>
                    <td class="model-name">${model.name}</td>
                    <td>${model.size_formatted || "Unknown"}</td>
                    <td>${model.modified_at_formatted || "Unknown"}</td>
                    <td>
                        <button class="btn btn-sm btn-danger delete-model" data-model="${
                          model.name
                        }">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </td>
                </tr>
            `;
    });

    modelsList.innerHTML = html;

    // Attach event listeners to delete buttons
    document.querySelectorAll(".delete-model").forEach((button) => {
      button.addEventListener("click", function () {
        const modelName = this.getAttribute("data-model");
        if (
          confirm(`Are you sure you want to delete the model "${modelName}"?`)
        ) {
          deleteModel(modelName);
        }
      });
    });
  }

  // Update the chat model select dropdown
  function updateChatModelSelect(models) {
    // Clear current options except the first one
    while (chatModelSelect.options.length > 1) {
      chatModelSelect.remove(1);
    }

    // Add models to select
    models.forEach((model) => {
      const option = document.createElement("option");
      option.value = model.name;
      option.textContent = model.name;
      chatModelSelect.appendChild(option);
    });

    // Enable/disable chat based on selection
    updateChatAvailability();
  }

  // Setup all event listeners
  function setupEventListeners() {
    // Model installation
    installModelBtn.addEventListener("click", function () {
      const modelName = modelInput.value.trim();
      if (modelName) {
        installModel(modelName);
      } else {
        alert("Please enter a model name");
      }
    });

    // Allow pressing Enter in model input to install
    modelInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        const modelName = modelInput.value.trim();
        if (modelName) {
          installModel(modelName);
        }
      }
    });

    // Refresh models button
    refreshModelsBtn.addEventListener("click", loadModels);

    // GPU info refresh button
    const refreshGpuBtn = document.getElementById("refresh-gpu-btn");
    if (refreshGpuBtn) {
      refreshGpuBtn.addEventListener("click", loadGpuInfo);
    }

    // Terminal command execution
    executeCommandBtn.addEventListener("click", function () {
      const command = commandInput.value.trim();
      if (command) {
        executeCommand(command);
      } else {
        alert("Please enter a command");
      }
    });

    // Allow pressing Enter in command input to execute
    commandInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        const command = commandInput.value.trim();
        if (command) {
          executeCommand(command);
        }
      }
    });

    // Quick commands
    quickCommands.forEach((button) => {
      button.addEventListener("click", function () {
        const command = this.getAttribute("data-command");
        commandInput.value = command;
        executeCommand(command);
      });
    });

    // Chat model selection
    chatModelSelect.addEventListener("change", updateChatAvailability);

    // Send chat message
    sendMessageBtn.addEventListener("click", sendChatMessage);

    // Allow pressing Enter in chat input to send message
    chatInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (sendMessageBtn.disabled === false) {
          sendChatMessage();
        }
      }
    });
  }

  // Check installation progress periodically
  function setupProgressChecker() {
    let pollInterval = 2000; // Start with 2-second interval
    let consecutiveEmptyResponses = 0;
    let isPollingActive = true;
    let pollTimer = null;

    // Initial check when page loads
    checkProgress();

    function checkProgress() {
      if (!isPollingActive) return;

      fetch("/api/models/progress")
        .then((response) => response.json())
        .then((data) => {
          // Handle installation in progress
          if (data.in_progress) {
            // Reset counter since we have an active installation
            consecutiveEmptyResponses = 0;
            pollInterval = 2000; // Reset to fast polling

            // Show progress UI
            installationProgress.classList.remove("d-none");
            installationStatus.textContent = data.status;

            // Update progress bar if percentage is in the status
            const match = data.progress.match(/(\d+)%/);
            if (match) {
              const percent = match[1];
              progressBar.style.width = `${percent}%`;
              progressBar.setAttribute("aria-valuenow", percent);
              // Add percentage to the progress bar text if > 5%
              if (parseInt(percent) > 5) {
                progressBar.textContent = `${percent}%`;
              } else {
                progressBar.textContent = "";
              }
            }

            // If progress is 100%, automatically refresh models list after 3 seconds
            if (data.progress.startsWith("100%")) {
              setTimeout(loadModels, 3000);
            }
          }
          // Handle when installation UI is shown but install is complete
          else if (!installationProgress.classList.contains("d-none")) {
            // If we were showing progress but now it's complete
            // Check if it was a successful install or a failure
            if (data.progress === "Failed") {
              // Show error
              progressBar.classList.add("bg-danger");
              installationStatus.classList.add("text-danger");
              installationStatus.textContent = `Installation failed: ${data.status}`;

              // Hide progress bar after 10 seconds
              setTimeout(function () {
                installationProgress.classList.add("d-none");
                // Reset classes
                progressBar.classList.remove("bg-danger");
                installationStatus.classList.remove("text-danger");
              }, 10000);
            } else {
              // Hide progress bar after 3 seconds
              setTimeout(function () {
                installationProgress.classList.add("d-none");
                loadModels(); // Refresh models list
              }, 3000);
            }
          }
          // Handle when there's no installation in progress or UI shown
          else {
            // Check if response is empty (no installation activity)
            if (!data.in_progress && !data.progress && !data.status) {
              consecutiveEmptyResponses++;

              // After 5 consecutive empty responses, slow down polling
              if (consecutiveEmptyResponses >= 5) {
                pollInterval = 10000; // Switch to 10-second polling
              }

              // After 15 consecutive empty responses, slow down further
              if (consecutiveEmptyResponses >= 15) {
                pollInterval = 30000; // Switch to 30-second polling
              }
            } else {
              // Reset if we got a non-empty response
              consecutiveEmptyResponses = 0;
              pollInterval = 2000; // Reset to fast polling
            }
          }
        })
        .catch((error) => {
          console.error("Error checking progress:", error);
          // On error, slow down polling
          pollInterval = 5000;
        })
        .finally(() => {
          // Schedule next poll with adaptive interval
          clearTimeout(pollTimer);
          pollTimer = setTimeout(checkProgress, pollInterval);
        });
    }

    // Handle tab visibility changes to reduce unnecessary background requests
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        // Page is not visible, pause polling
        clearTimeout(pollTimer);
        isPollingActive = false;
      } else {
        // Page is visible again, resume polling
        isPollingActive = true;
        checkProgress();
      }
    });

    // Provide method to force an immediate check
    window.forceProgressCheck = function () {
      consecutiveEmptyResponses = 0;
      pollInterval = 2000;
      clearTimeout(pollTimer);
      checkProgress();
    };

    // When a user initiates an installation, immediately start polling
    installModelBtn.addEventListener("click", function () {
      if (modelInput.value.trim()) {
        window.forceProgressCheck();
      }
    });
  }

  // Install a model
  function installModel(modelName) {
    // Disable button and show progress
    installModelBtn.disabled = true;
    installationProgress.classList.remove("d-none");

    // Reset the progress UI
    progressBar.style.width = "0%";
    progressBar.textContent = "";
    progressBar.classList.remove("bg-danger");
    installationStatus.classList.remove("text-danger");
    installationStatus.textContent = `Requesting installation of ${modelName}...`;

    // Force immediate progress check
    if (window.forceProgressCheck) {
      window.forceProgressCheck();
    }

    fetch("/api/models/install", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: modelName }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(`Error: ${data.error}`);
          installationProgress.classList.add("d-none");
        } else {
          installationStatus.textContent = data.message;
        }
      })
      .catch((error) => {
        console.error("Error installing model:", error);
        alert(`Error installing model: ${error.message}`);
        installationProgress.classList.add("d-none");
      })
      .finally(() => {
        installModelBtn.disabled = false;
      });
  }

  // Delete a model
  function deleteModel(modelName) {
    fetch("/api/models/delete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: modelName }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(`Error: ${data.error}`);
        } else {
          alert(data.message);
          loadModels(); // Refresh the models list
        }
      })
      .catch((error) => {
        console.error("Error deleting model:", error);
        alert(`Error deleting model: ${error.message}`);
      });
  }

  // Execute a terminal command
  function executeCommand(command) {
    // Disable button and show spinner
    executeCommandBtn.disabled = true;
    commandOutput.value = "Executing command...";

    fetch("/api/terminal/execute", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command: command }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          commandOutput.value = `Error: ${data.error}`;
        } else {
          commandOutput.value = data.output;
        }
      })
      .catch((error) => {
        console.error("Error executing command:", error);
        commandOutput.value = `Error executing command: ${error.message}`;
      })
      .finally(() => {
        executeCommandBtn.disabled = false;
      });
  }

  // Update chat availability based on model selection
  function updateChatAvailability() {
    const selectedModel = chatModelSelect.value;
    if (selectedModel) {
      sendMessageBtn.disabled = false;
      chatInput.placeholder = `Chat with ${selectedModel}...`;
    } else {
      sendMessageBtn.disabled = true;
      chatInput.placeholder = "Select a model first...";
    }
  }

  // Send chat message
  function sendChatMessage() {
    const message = chatInput.value.trim();
    const model = chatModelSelect.value;

    if (!message || !model) {
      return;
    }

    // Disable button
    sendMessageBtn.disabled = true;

    // Add user message to chat
    addChatMessage("user", message);

    // Clear input
    chatInput.value = "";

    // Show thinking indicator
    const thinkingId = addThinkingIndicator();

    fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: model,
        message: message,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        // Remove thinking indicator
        removeThinkingIndicator(thinkingId);

        if (data.error) {
          addChatMessage("model", `Error: ${data.error}`);
        } else {
          addChatMessage("model", data.response);
        }
      })
      .catch((error) => {
        // Remove thinking indicator
        removeThinkingIndicator(thinkingId);

        console.error("Error sending message:", error);
        addChatMessage("model", `Error: ${error.message}`);
      })
      .finally(() => {
        // Re-enable button
        sendMessageBtn.disabled = false;
      });
  }

  // Add message to chat
  function addChatMessage(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${role}-message`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Add thinking indicator
  function addThinkingIndicator() {
    const id = "thinking-" + Date.now();
    const messageDiv = document.createElement("div");
    messageDiv.className = "chat-message model-message";
    messageDiv.id = id;
    messageDiv.innerHTML =
      '<div class="spinner-border spinner-border-sm me-2" role="status"></div> Thinking...';
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return id;
  }

  // Remove thinking indicator
  function removeThinkingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
      element.remove();
    }
  }
});
