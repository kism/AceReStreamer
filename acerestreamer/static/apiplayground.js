
function doApiCall(apiEndpoint) {
    return fetch(apiEndpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .catch(error => {
            console.error('Error fetching API:', error);
            return `Error: ${error.message}`;
        });
}


function prettyFormatJson(json) {
    try {
        return JSON.stringify(JSON.parse(json), null, 2);
    } catch (e) {
        console.error('Error formatting JSON:', e);
        return json; // Return the original string if parsing fails
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const apiInput = document.getElementById("api-input");
    const apiSubmit = document.getElementById("do-api-btn");
    const apiOutput = document.getElementById("api-output");

    apiSubmit.addEventListener("click", function () {
        const apiEndpoint = apiInput.value.trim();
        if (apiEndpoint) {
            doApiCall(apiEndpoint).then(response => {
                apiOutput.innerHTML = `<pre>${prettyFormatJson(response)}</pre>`;
            });
        } else {
            apiOutput.textContent = "Please enter a valid API endpoint.";
        }
    });
});
