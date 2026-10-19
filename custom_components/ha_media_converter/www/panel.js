class HaMediaConverterPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.render();
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          box-sizing: border-box;
          max-width: 760px;
          margin: 0 auto;
          padding: 24px;
          color: var(--primary-text-color);
        }
        h1 { font-size: 1.5rem; }
        .card {
          padding: 24px;
          border-radius: 12px;
          background: var(--ha-card-background, var(--card-background-color));
          box-shadow: var(--ha-card-box-shadow, 0 2px 8px #0002);
        }
        .hint { color: var(--secondary-text-color); line-height: 1.5; }
        label { display: block; margin-top: 20px; }
        select, input { display: block; margin: 8px 0 20px; }
        select { max-width: 100%; min-width: 240px; padding: 8px; }
        button {
          padding: 10px 18px;
          border: 0;
          border-radius: 6px;
          color: var(--text-primary-color);
          background: var(--primary-color);
          cursor: pointer;
        }
        button:disabled { opacity: .6; cursor: wait; }
        #results { margin-top: 20px; white-space: pre-line; }
      </style>
      <main class="card">
        <h1>HEIC to JPEG</h1>
        <p class="hint">
          Select HEIC or HEIF photos to upload. The original and a JPEG copy
          will be saved in the selected Home Assistant media folder.
          Choose an existing folder below. Each file must be 20 MB or smaller.
        </p>
        <label for="destination">Save to</label>
        <select id="destination" disabled>
          <option value="">Media folder (root)</option>
        </select>
        <input id="files" type="file" accept=".heic,.heif,image/heic,image/heif" multiple>
        <button id="upload" type="button">Upload and convert</button>
        <div id="results" role="status" aria-live="polite"></div>
      </main>
    `;

    this.shadowRoot.querySelector("#upload").addEventListener("click", () => {
      this.uploadFiles();
    });
    this._destinationsLoaded = false;
    this.loadDestinations();
  }

  async loadDestinations() {
    const selector = this.shadowRoot.querySelector("#destination");
    const results = this.shadowRoot.querySelector("#results");
    const token = this._hass.auth?.data?.access_token;
    if (!token) {
      results.textContent = "Home Assistant authentication is not available. Reload the panel and try again.";
      return;
    }

    try {
      const response = await fetch("/api/ha_media_converter/destinations", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.message || "Unable to load media folders.");
      }
      if (!Array.isArray(result.destinations)) {
        throw new Error("The media folder list is invalid.");
      }

      for (const path of result.destinations) {
        if (typeof path !== "string") {
          throw new Error("The media folder list is invalid.");
        }
        const option = document.createElement("option");
        option.value = path;
        option.textContent = path;
        selector.appendChild(option);
      }
      selector.disabled = false;
      this._destinationsLoaded = true;
    } catch (error) {
      results.textContent = error.message || "Unable to load media folders.";
    }
  }

  async uploadFiles() {
    const fileInput = this.shadowRoot.querySelector("#files");
    const button = this.shadowRoot.querySelector("#upload");
    const destinationSelector = this.shadowRoot.querySelector("#destination");
    const results = this.shadowRoot.querySelector("#results");
    const files = Array.from(fileInput.files || []);

    if (!this._destinationsLoaded) {
      results.textContent = "Media folders are not available. Reload the panel and try again.";
      return;
    }
    if (files.length === 0) {
      results.textContent = "Choose at least one HEIC or HEIF file.";
      return;
    }
    const token = this._hass.auth?.data?.access_token;
    if (!token) {
      results.textContent = "Home Assistant authentication is not available. Reload the panel and try again.";
      return;
    }

    button.disabled = true;
    results.textContent = "";
    for (const file of files) {
      const form = new FormData();
      form.append("destination", destinationSelector.value);
      form.append("file", file, file.name);
      try {
        const response = await fetch("/api/ha_media_converter/upload", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: form,
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.message || "Conversion failed.");
        }
        const destination = result.destination
          ? `Home Assistant media/${result.destination}`
          : "Home Assistant media";
        results.textContent += `Saved ${result.converted} and the original to ${destination}.\n`;
      } catch (error) {
        results.textContent += `${file.name}: ${error.message}\n`;
      }
    }
    button.disabled = false;
    fileInput.value = "";
  }
}

customElements.define("ha-media-converter-panel", HaMediaConverterPanel);
