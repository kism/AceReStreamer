function doApiCall(apiEndpoint) {
  return fetch(apiEndpoint)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.text();
    })
    .catch((error) => {
      console.error("Error fetching API:", error);
      return `Error: ${error.message}`;
    });
}

function prettyFormatJson(json) {
  try {
    return JSON.stringify(JSON.parse(json), null, 2);
  } catch (e) {
    console.error("Error formatting JSON:", e);
    return json; // Return the original string if parsing fails
  }
}

function populateApiEndpointLinks() {
  const apiEndpoints = document.querySelectorAll("#api-endpoints tr");

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
        const apiEndpoint = pathCell.textContent.trim();
        apiInput.value = apiEndpoint;
      });
      pathCell.classList.add("link");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const apiInput = document.getElementById("api-input");
  const apiSubmit = document.getElementById("do-api-btn");
  const apiOutput = document.getElementById("api-output");

  apiSubmit.addEventListener("click", () => {
    const apiEndpoint = apiInput.value.trim();
    const startTime = performance.now();
    if (apiEndpoint) {
      doApiCall(apiEndpoint).then((response) => {
        apiOutput.innerHTML = `<pre>${prettyFormatJson(response)}</pre>`;
        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);
        document.getElementById("api-response-time").textContent = `Duration: ${duration} ms`;
        console.log(`API call to ${apiEndpoint} took ${duration} ms`);
      });
    } else {
      apiOutput.textContent = "Please enter a valid API endpoint.";
    }
  });

  populateApiEndpointLinks();
});
