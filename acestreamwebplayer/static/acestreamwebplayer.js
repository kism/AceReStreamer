function getStreams() {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => controller.abort(), 1000); // 1 second timeout:

  // GET the hello endpoint that the flask app has
  fetch("/api/v1/streams", {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      // Check if the request was successful (status code 200)
      if (response.ok) {
        return response.json(); // We interoperate the response as json and pass it along...
      } else {
        document.getElementById("stream-status").innerHTML = `API FAILURE`; // Set message in element to indicate failure
        document.getElementById("stream-list").innerHTML = `${response.status}`; // Set message in element to message received from flask
        document.getElementById("stream-list").style.color = "#800000"; // Set message in element to message received from flask

        throw new Error(`Error fetching data. Status code: ${response.status}`);
      }
    })
    .then((data) => {
      let msg_str = ""; // Initialize an empty string to hold the message

      ele = document.getElementById("stream-list"); // The div for the stream list
      ele.innerHTML = ""; // Clear the inner HTML of the stream list element

      for (const site of data) {
        console.log(site.site_name); // Log the site data to the console for debugging
        const ul = document.createElement("ul"); // Create a new unordered list element
        ul.textContent = site.site_name; // Set the text content of the list to the site name

        for (const stream of site.stream_list) {
          const li = document.createElement("li"); // Create a new list item element
          li.textContent = `${stream.title} (${stream.url})`; // Set the text content of the list item to the stream title and URL
          console.log(li.textContent); // Log the list item text content to the console for debugging
          ul.appendChild(li); // Append the list item to the unordered list
        }
        ele.appendChild(ul); // Append the unordered list to the stream list element
      }

      document.getElementById("stream-status").style.display = "None"; // Set message in element to indicate success
      document.getElementById("stream-list").innerHTML = msg_str; // Set message in element to message received from flask
    })
    .catch((error) => {
      clearTimeout(timeoutId); //Stop the timeout since we only care about the GET timing out
      if (error.name === "AbortError") {
        console.error("Fetch request timed out");
        document.getElementById("stream-status").innerHTML = `API FAILURE`; // Set message in element to indicate failure
        document.getElementById("stream-list").innerHTML = `Fetch Timeout`; // Set message in element to message received from flask
        document.getElementById("stream-list").style.color = "#800000"; // Set message in element to message received from flask
      } else {
        console.error(`Error: ${error.message}`);
      }
    });
}

//On page load we run this code, running the function getStreams()
getStreams();
//We call every 10 minutes to update the streams
setInterval(getStreams, 10 * 60 * 1000); // 10 minutes in milliseconds
