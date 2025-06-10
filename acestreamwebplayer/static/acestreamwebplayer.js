function getStreams() {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => controller.abort(), 1000); // 1 second timeout:

  // GET the hello endpoint that the flask app has
  fetch("/api/streams", {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      // Check if the request was successful (status code 200)
      if (response.ok) {
        return response.json(); // We interoperate the response as json and pass it along...
      } else {
        const streamStatus = document.getElementById("stream-status");
        streamStatus.className = "status-bad";
        streamStatus.innerHTML = `API FAILURE ${response.status}`; // Set message in element to indicate failure

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

      let dataFlattened = [];
      for (const site of data) {
        for (const stream of site.stream_list) {
          dataFlattened.push({
            quality: stream.quality,
            title: stream.title,
            ace_id: stream.ace_id,
            site_name: site.site_name,
          });
        }
      }

      // Sort the data by quality in descending order
      dataFlattened.sort((a, b) => b.quality - a.quality);

      for (const stream of dataFlattened) {
        const tr = document.createElement("tr");

        // Quality cell
        const td_quality = document.createElement("td");
        const code = document.createElement("code");
        code.textContent = `${stream.quality}`;
        if (stream.quality === -1) {
          code.className = "status-neutral";
          code.textContent = "?";
        } else if (stream.quality < 20) {
          code.className = "status-bad";
        } else if (stream.quality >= 20 && stream.quality <= 80) {
          code.className = "status-neutral";
        } else if (stream.quality >= 80) {
          code.className = "status-good";
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
        td_source.textContent = `${stream.site_name}`;

        // Append to the row
        tr.appendChild(td_quality);
        tr.appendChild(td_link);
        tr.appendChild(td_source);
        table.appendChild(tr);
      }
    })
    .catch((error) => {
      clearTimeout(timeoutId); //Stop the timeout since we only care about the GET timing out
      if (error.name === "AbortError") {
        console.error("Fetch request timed out");
        const streamStatus = document.getElementById("stream-status");
        streamStatus.className = "status-bad";
        streamStatus.innerHTML = `API FAILURE: Fetch Timeout`;
      } else {
        console.error(`Error: ${error.message}`);
      }
    });
}

function setOnPageErrorMessage(message) {
  const streamStatus = document.getElementById("stream-status");
  streamStatus.innerHTML = message;
  streamStatus.className = "status-bad";
  //on a timeout, set the background color of the stream status to red
  streamStatus.style.backgroundColor = "#331111"; // Set the background color to red
  // wait 5 seconds
  setTimeout(() => {
    streamStatus.style.backgroundColor = ""; // Reset the background color
  }, 200);
}

function loadStream() {
  const video = document.getElementById("video");
  const videoSrc = `/hls/${window.location.hash.substring(1)}`;
  console.log(`Loading stream: ${videoSrc}`);

  const streamDirectUrl = document.getElementById("stream-url");
  streamDirectUrl.innerHTML = `${window.location.origin}${videoSrc}`;

  const streamStatus = document.getElementById("stream-status");
  streamStatus.className = "status-neutral";
  streamStatus.innerHTML = `Stream loaded, paused.`;

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
}

function loadStreamUrl(streamId, streamName) {
  window.location.hash = streamId; // Set the URL in the hash
  document.getElementById("stream-name").innerText = streamName;
  loadStream();
}

function checkIfPlaying() {
  const video = document.getElementById("video");
  if (!video.paused && !video.ended && video.currentTime > 0 && video.readyState > 2) {
    const streamStatus = document.getElementById("stream-status");
    streamStatus.innerHTML = "Playing"; // Hide the status element if the video is playing
    streamStatus.className = "status-good"; // Set the text color to green
  }
}

// Wrap DOM-dependent code in DOMContentLoaded event
document.addEventListener("DOMContentLoaded", function () {
  const streamStatus = document.getElementById("stream-status");
  streamStatus.className = "status-neutral";
  streamStatus.innerHTML = "Ready to load a stream";

  getStreams();
  setInterval(getStreams, 60 * 100); // 10 seconds in milliseconds

  window.addEventListener("loadStream", loadStream);

  let streamId = window.location.hash.substring(1);
  console.log(`Loading stream on page load: ${streamId}`);
  if (streamId) {
    loadStreamUrl(streamId, streamId);
  }

  setInterval(checkIfPlaying, 1000); // Check every second if the video is playing

  loadStreamButton = document.getElementById("load-stream-button");
  loadStreamButton.onclick = () => {
    const streamId = document.getElementById("stream-id-input").value; // Get the value from the input field
    if (streamId) {
      loadStreamUrl(streamId, streamId); // Load the stream with the entered ID
    }
  };
});
