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
        input { display: block; margin: 20px 0; }
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
          will be saved in Home Assistant's media folder.
          Each file must be 20 MB or smaller.
        </p>
        <input id="files" type="file" accept=".heic,.heif,image/heic,image/heif" multiple>
        <button id="upload" type="button">Upload and convert</button>
        <div id="results" role="status" aria-live="polite"></div>
      </main>
    `;

    this.shadowRoot.querySelector("#upload").addEventListener("click", () => {
      this.uploadFiles();
    });
  }

  async uploadFiles() {
    const fileInput = this.shadowRoot.querySelector("#files");
    const button = this.shadowRoot.querySelector("#upload");
    const results = this.shadowRoot.querySelector("#results");
    const files = Array.from(fileInput.files || []);

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
        results.textContent += `Saved ${result.converted} and the original to Home Assistant media.\n`;
      } catch (error) {
        results.textContent += `${file.name}: ${error.message}\n`;
      }
    }
    button.disabled = false;
    fileInput.value = "";
  }
}

customElements.define("ha-media-converter-panel", HaMediaConverterPanel);
