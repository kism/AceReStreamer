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
      const table = document.getElementById("stream-table");
      table.innerHTML = ""; // Clear the table before adding new data
      const tr_heading = document.createElement("tr");

      const th_quality = document.createElement("th");
      th_quality.textContent = "Quality";
      tr_heading.appendChild(th_quality);

      const th_link = document.createElement("th");
      th_link.textContent = "Stream";
      tr_heading.appendChild(th_link);

      const th_source = document.createElement("th");
      th_source.textContent = "Source";
      tr_heading.appendChild(th_source);

      table.appendChild(tr_heading);

      for (const site of data) {
        for (const stream of site.stream_list) {
          const tr = document.createElement("tr");

          // Quality cell
          const td_quality = document.createElement("td");
          const code = document.createElement("code");
          code.textContent = `${stream.quality}`;
          if (stream.quality === -1) {
          } else if (stream.quality < 20) {
            code.style.color = "#FF0000";
          } else if (stream.quality >= 20 && stream.quality <= 80) {
            code.style.color = "#FFA500";
          } else if (stream.quality <= 80) {
            code.style.color = "#00FF00";
          }
          td_quality.appendChild(code);

          // Link cell
          td_link = document.createElement("td");
          const a = document.createElement("a"); // Create a new anchor element
          a.textContent = `${stream.title}`;
          a.onclick = () => loadStreamUrl(stream.ace_id, stream.title); // Set the onclick event to load the stream URL
          td_link.appendChild(a); // Append the anchor element to the table data cell

          // Source Cell
          td_source = document.createElement("td");
          td_source.textContent = `${site.site_name}`;

          // Append to the row
          tr.appendChild(td_quality);
          tr.appendChild(td_link);
          tr.appendChild(td_source);
          table.appendChild(tr);
        }
      }
      ele.appendChild(table); // Append the table to the stream list element

      document.getElementById("stream-status").innerText = "No stream loaded"; // Set message in element to indicate success
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

function setOnPageErrorMessage(message) {
  element = document.getElementById("stream-status");
  element.innerHTML = message; // Set the inner HTML of the element to the error message
  element.style.display = "block"; // Make the element visible
  element.style.color = "#FF0000"; // Set the text color to a dark red
  //on a timeout, set the background color of the stream status to red
  document.getElementById("stream-status").style.backgroundColor = "#331111"; // Set the background color to red
  // wait 5 seconds
  setTimeout(() => {
    document.getElementById("stream-status").style.backgroundColor = ""; // Reset the background color
  }, 100);
}

function loadStream() {
  const video = document.getElementById("video");
  const videoSrc = `/hls/${window.location.hash.substring(1)}`;
  console.log(`Loading stream: ${videoSrc}`);
  document.getElementById("stream-status").style.color = "none"; // Show the status element

  if (Hls.isSupported()) {
    var hls = new Hls();

    // Add error event listener
    hls.on(Hls.Events.ERROR, function (event, data) {
      console.error("HLS error:", data);
      let errorMessage = "Stream loading failed";

      if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
        errorMessage = "Network error: Unable to load stream";
      } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
        errorMessage = "Media error: Stream format issue";
      } else if (data.type === Hls.ErrorTypes.MUX_ERROR) {
        errorMessage = "Stream parsing error";
      }
      setOnPageErrorMessage(errorMessage);
    });

    hls.loadSource(videoSrc);
    hls.attachMedia(video);
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = videoSrc; // For Safari

    // Add error event listener for Safari
    video.addEventListener("error", function (e) {
      console.error("Video error:", e);
      setOnPageErrorMessage("Stream loading failed");
    });
  } else {
    console.error("This browser does not support HLS playbook.");
    setOnPageErrorMessage("This browser does not support HLS playbook.");
    return;
  }

  directURL = document.getElementById("direct-url");
  directURL.innerHTML = `${window.location.origin}${videoSrc}`;

  //start playing the video
  video.play().catch((error) => {
    console.error("Error playing video:", error);
    document.getElementById("stream-status").innerHTML = `Error playing video: ${error.message}`; // Set message in element to indicate error
  });
}

function loadStreamUrl(streamId, streamName) {
  window.location.hash = streamId; // Set the URL in the hash
  document.getElementById("stream-name").innerText = streamName;
  loadStream();
}

function checkIfPlaying() {
  const video = document.getElementById("video");
  if (!video.paused && !video.ended && video.currentTime > 0 && video.readyState > 2) {
    document.getElementById("stream-status").style.display = "none"; // Hide the status element if the video is playing
  }
}

// Wrap DOM-dependent code in DOMContentLoaded event
document.addEventListener("DOMContentLoaded", function () {
  getStreams();
  //setInterval(getStreams, 10 * 60 * 1000); // 10 minutes in milliseconds
  setInterval(getStreams, 60 * 100); // 10 seconds in milliseconds

  window.addEventListener("loadStream", loadStream);

  let streamId = window.location.hash.substring(1);
  console.log(`Stream ID from URL: ${streamId}`);
  if (streamId) {
    loadStreamUrl(streamId, streamId);
  }

  setInterval(checkIfPlaying, 1000); // Check every second if the video is playing

  manualInput = document.getElementById("stream-manual-input");
  inputField = document.createElement("input"); // Create an input field
  inputField.type = "text"; // Set the input type to text
  inputField.id = "stream-id-input"; // Set the ID for the input field
  inputField.placeholder = "Enter Ace Stream ID"; // Set a placeholder for the input field
  manualInput.appendChild(inputField); // Append the input field to the manual input element
  manualInput.appendChild(document.createElement("code")); // Add a line break for spacing
  manualInput.appendChild(document.createElement("button")); // Create a button element
  manualInput.lastChild.innerText = "Load"; // Set the button text
  manualInput.lastChild.onclick = () => {
    const streamId = document.getElementById("stream-id-input").value; // Get the value from the input field
    if (streamId) {
      loadStreamUrl(streamId, streamId); // Load the stream with the entered ID
    } else {
      alert("Please enter a valid Ace Stream ID."); // Alert if no ID is entered
    }
  };
});
