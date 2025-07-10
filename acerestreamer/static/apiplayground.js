const xmlFormatter = require("xml-formatter");

function escapeHtmlXML(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function prettyFormat(content) {
  try {
    // Try format as JSON
    return JSON.stringify(JSON.parse(content), null, 2);
  } catch (e) {
    // Try format as XML
    try {
      const formattedXml = xmlFormatter(content, {
        indentation: "  ",
        collapseContent: true,
        lineSeparator: "\n",
      });

      // Escape HTML entities for proper display
      return escapeHtmlXML(formattedXml);
    } catch (_e) {
      return escapeHtmlXML(content); // Return original if both fail
    }
  }
}

function setStatusClass(element, status) {
  // Remove all status classes from the element
  const statusClasses = ["status-good", "status-neutral", "status-bad"];
  for (const cls of statusClasses) {
    element.classList.remove(cls);
  }
  // Add the appropriate status class based on the status parameter
  if (status === "good") {
    element.classList.add("status-good");
  } else if (status === "neutral") {
    element.classList.add("status-neutral");
  } else if (status === "bad") {
    element.classList.add("status-bad");
  }
}

function populateApiEndpointLinks() {
  const apiEndpoints = document.querySelectorAll(".api-table tr");

  if (apiEndpoints.length === 0) {
    console.warn("No API endpoints found in the table.");
    return;
  }
  for (const row of apiEndpoints) {
    const pathCell = row.querySelector("td:nth-child(1)");
    if (!pathCell) {
      console.warn("No path cell found in the row:", row);
    } else {
      pathCell.addEventListener("click", () => {
        const apiInput = document.getElementById("api-input");
        const cellContent = pathCell.innerHTML;
        // If cell contains <br>, only use the first part
        const apiEndpoint = cellContent.includes("<br>")
          ? cellContent.split("<br>")[0].trim()
          : pathCell.textContent.trim();
        apiInput.value = apiEndpoint;
      });
      pathCell.classList.add("link");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const apiInput = document.getElementById("api-input");
  const apiSubmit = document.getElementById("do-api-btn");
  const apiOutputBody = document.getElementById("api-output-body");
  const apiOutputStatus = document.getElementById("api-output-status");

  apiSubmit.addEventListener("click", () => {
    const apiEndpoint = apiInput.value.trim();
    const startTime = performance.now();
    if (apiEndpoint) {
      const cleanEndpoint = apiEndpoint.startsWith("/") ? apiEndpoint : `/${apiEndpoint}`;

      fetch(cleanEndpoint)
        .then((response) => {
          apiOutputStatus.textContent = `${response.status} ${response.statusText}`;
          setStatusClass(apiOutputStatus, response.ok ? "good" : "bad");
          return response.text();
        })
        .then((text) => {
          const formattedText = prettyFormat(text);
          apiOutputBody.innerHTML = `<pre>${formattedText}</pre>`;
        });

      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);
      document.getElementById("api-response-time").textContent = `Duration: ${duration} ms`;
      console.log(`API call to ${cleanEndpoint} took ${duration} ms`);
    } else {
      apiOutputStatus.textContent = "Please enter a valid API endpoint.";
      apiOutputBody.innerHTML = "";
    }
  });
  populateApiEndpointLinks();
});
