// region Global Variables
let currentlyFetchingM3U8 = "";

// region API/getStreamsFlat
function getStreamsFlat() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  return fetch("/api/streams/flat", {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        console.error(`Error fetching streams sources: ${response.status}`);
      }
    })
    .then((data) => {
      return data;
    })
    .catch((error) => {
      clearTimeout(timeoutId); // Stop the timeout since we only care about the GET timing out
      if (error.name === "AbortError") {
        console.error("getStreamsFlat Fetch request timed out");
      } else {
        console.error(`getStreamsFlat Error: ${error.message}`);
      }
      throw error;
    });
}

// region API/getStream
function getStream(aceContentId) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  // GET the hello endpoint that the flask app has
  return fetch(`/api/stream/${aceContentId}`, {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
    })
    .then((data) => {
      return data;
    })
    .catch((error) => {
      clearTimeout(timeoutId);
      if (error.name === "AbortError") {
        console.error("getStream Fetch request timed out");
      } else {
        console.error(`getStream Error: ${error.message}`);
      }
      throw error;
    });
}

// region API/getAcePool
function getAcePool() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  return fetch("/api/ace-pool", {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
    })
    .then((data) => {
      return data;
    })
    .catch((error) => {
      clearTimeout(timeoutId); // Stop the timeout since we only care about the GET timing out
      if (error.name === "AbortError") {
        console.error("getAcePool Fetch request timed out");
      } else {
        console.error(`getAcePool Error: ${error.message}`);
      }
      throw error;
    });
}

// region API/makeAcePoolInstanceAvailable
function makeAcePoolInstanceAvailable(aceId) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  return fetch(`/api/ace-pool/${aceId}`, {
    method: "DELETE",
    signal: controller.signal,
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        console.error(`Error making Ace Pool instance available: ${response.status}`);
        throw new Error(`Error making Ace Pool instance available: ${response.status}`);
      }
    })
    .then((data) => {
      console.log("Ace Pool instance made available:", data);
      return data;
    })
    .catch((error) => {
      clearTimeout(timeoutId); // Stop the timeout since we only care about the DELETE timing out
      if (error.name === "AbortError") {
        console.error("makeAcePoolInstanceAvailable Fetch request timed out");
      } else {
        console.error(`makeAcePoolInstanceAvailable Error: ${error.message}`);
      }
      throw error;
    });
}

// region Status

function flashBackgroundColor(element, state, duration = 200) {
  let backgroundClass = "status-neutral-background";
  if (state === "good") {
    backgroundClass = "status-good-background";
  } else if (state === "bad") {
    backgroundClass = "status-bad-background";
  }

  element.classList.add(backgroundClass);
  setTimeout(() => {
    element.classList.remove(backgroundClass);
  }, duration);
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

function setOnPageStreamErrorMessage(message) {
  const streamStatus = document.getElementById("stream-status");
  streamStatus.innerHTML = message;
  setStatusClass(streamStatus, "bad");

  flashBackgroundColor(streamStatus, "bad", 500); // Flash the background color to indicate an error
}

function checkIfPlaying() {
  const video = document.getElementById("video");
  const playerStatus = document.getElementById("player-status");

  if (!video.paused && !video.ended && video.currentTime > 0 && video.readyState > 2) {
    playerStatus.innerHTML = "Playing";
    setStatusClass(playerStatus, "good");
  } else {
    playerStatus.innerHTML = "Not playing";
    setStatusClass(playerStatus, "neutral");
  }
}

// region Stream/checkVideoSrcAvailability
async function checkVideoSrcAvailability(videoSrc, maxRetries = 5) {
  currentlyFetchingM3U8 = videoSrc;
  let msg = "";
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      if (currentlyFetchingM3U8 !== videoSrc) {
        console.warn("Stream source check aborted due to new request");
        return false;
      }
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      const response = await fetch(videoSrc, {
        method: "GET",
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        currentlyFetchingM3U8 = "";
        populateAceInfoTables();
        return true;
      }

      msg = `${attempt}/${maxRetries}: Stream source unavailable with status ${response.status}`;
      console.warn(msg);
      setOnPageStreamErrorMessage(msg);
    } catch (error) {
      if (error.name === "AbortError") {
        msg = `Attempt: ${attempt}/${maxRetries}: Getting stream source timed out`;
      } else {
        msg = `Attempt: ${attempt}/${maxRetries}: ${error.message}`;
      }
      console.warn(msg);
      setOnPageStreamErrorMessage(msg);
    }

    // Wait before retrying (except on the last attempt)
    if (attempt < maxRetries) {
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }
  }

  console.error(`Video source unavailable after ${maxRetries} attempts`);
  populateAceInfoTables();
  return false;
}

// region Stream/loadStream
function loadStream() {
  const video = document.getElementById("video");
  const videoSrc = `/hls/${window.location.hash.substring(1)}`;
  console.log(`Loading stream: ${videoSrc}`);

  if (!checkVideoSrcAvailability(videoSrc)) {
    setOnPageStreamErrorMessage("Stream source is not available");
    return;
  }

  video.controls = true;

  const streamDirectUrl = document.getElementById("stream-url");
  streamDirectUrl.innerHTML = `${window.location.origin}${videoSrc}`;

  const streamStatus = document.getElementById("stream-status");
  setStatusClass(streamStatus, "neutral");
  streamStatus.innerHTML = "Stream loaded";

  if (Hls.isSupported()) {
    const hls = new Hls();

    // Add error event listener
    hls.on(Hls.Events.ERROR, (_event, data) => {
      console.error("HLS error:", data);
      let errorMessage = "Stream loading failed";

      if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
        errorMessage = "Network error: Ace doen't have the stream segment";
        attemptPlay();
      } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
        errorMessage = "Media error: Stream not ready";
      } else if (data.type === Hls.ErrorTypes.MUX_ERROR) {
        errorMessage = "Stream parsing error";
      } else if (data.details) {
        errorMessage = `HLS error: ${data.details}`;
      }
      setOnPageStreamErrorMessage(errorMessage);
    });

    // Wait for HLS to be ready before allowing play
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      const streamStatus = document.getElementById("stream-status");
      streamStatus.innerHTML = "Stream ready";
      setStatusClass(streamStatus, "good");
    });

    hls.on(Hls.Events.BUFFER_APPENDED, (_event, _data) => {
      const streamStatus = document.getElementById("stream-status");
      setStatusClass(streamStatus, "good");
      streamStatus.innerHTML = "Healthy";
    });

    hls.loadSource(videoSrc);
    hls.attachMedia(video);
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = videoSrc; // For Safari

    // Add error event listener for Safari
    video.addEventListener("error", (e) => {
      console.error("Video error:", e);
      setOnPageStreamErrorMessage("Stream loading failed");
    });
  } else {
    console.error("This browser does not support HLS playbook.");
    setOnPageStreamErrorMessage("This browser does not support HLS playbook.");
  }

  const chromecastButton = document.getElementById("chromecast-button");
  if (typeof cast !== "undefined" && cast.framework && cast.framework.CastContext) {
    chromecastButton.style.display = "inline-block"; // Show the Chromecast button
    chromecastButton.onclick = () => {
      const hlsUrl = `/hls/${window.location.hash.substring(1)}`;
      castHlsStream(hlsUrl);
    };
  }
}

// region Stream/loadStreamUrl
function loadStreamUrl(aceContentId, streamInfo = null) {
  window.location.hash = aceContentId; // Set the URL in the hash

  const streamNameElement = document.getElementById("stream-name");
  streamNameElement.innerHTML = streamInfo.title || aceContentId;

  populateCurrentStreamInfo(streamInfo.program_title, streamInfo.program_description);

  loadStream();

  if (aceContentId !== streamInfo.title && streamInfo.title !== "") {
    document.title = `${streamInfo.title}`;
  } else {
    document.title = `AceRestreamer`;
  }
}

// region Stream/loadPlayStream
function loadPlayStream(aceContentId) {
  getStream(aceContentId)
    .then((streamInfo) => {
      loadStreamUrl(aceContentId, streamInfo);

      attemptPlay();
    })
    .catch((error) => {
      console.error("Failed to get stream info:", error);
      loadStreamUrl(aceContentId);
      attemptPlay();
    });
}

// region Stream/loadPlayStreamFromHash
// biome-ignore lint/correctness/noUnusedVariables: HTML uses it
function loadPlayStreamFromHash() {
  const aceContentId = window.location.hash.substring(1);
  if (aceContentId) {
    console.log(`Loading stream from hash: ${aceContentId}`);
    loadPlayStream(aceContentId);
  } else {
    console.error("No stream ID loaded...");
    setOnPageStreamErrorMessage("No stream ID loaded...");
  }
}

// region Video/TogglePlayerSize
// biome-ignore lint/correctness/noUnusedVariables: HTML uses it
function togglePlayerSize() {
  const video = document.getElementById("video");
  const playerContainer = document.getElementById("player-container");

  // Check if currently in small size (640px width)
  const isSmallSize = video.style.width === "640px" || video.style.width === "";

  if (isSmallSize) {
    // Switch to large size, but respect display constraints
    const maxHeight = window.innerHeight - 100; // Leave margin for UI elements
    const maxWidth = window.innerWidth - 50; // Leave some side margin
    const aspectRatio = 16 / 9;

    let targetWidth = maxWidth;
    let targetHeight = targetWidth / aspectRatio;

    // If height exceeds max, scale down based on height
    if (targetHeight > maxHeight) {
      targetHeight = maxHeight;
      targetWidth = targetHeight * aspectRatio;
    }

    video.style.width = `${targetWidth}px`;
    video.style.height = `${targetHeight}px`;
    playerContainer.style.width = `${targetWidth}px`;
    playerContainer.style.height = `${targetHeight}px`;
  } else {
    // Switch to small size (640x360)
    video.style.width = "640px";
    video.style.height = "360px";
    playerContainer.style.width = "640px";
    playerContainer.style.height = "360px";
  }

  // Scroll to center the player vertically on the page
  setTimeout(() => {
    const playerRect = playerContainer.getBoundingClientRect();
    const scrollTop = window.pageYOffset + playerRect.top - (window.innerHeight - playerRect.height) / 2;
    window.scrollTo({
      top: Math.max(0, scrollTop),
      behavior: "smooth",
    });
  }, 100); // Small delay to ensure size changes are applied
}

// region Video/resizePlayerMobile
function resizePlayerMobile() {
  const video = document.getElementById("video");
  const playerContainer = document.getElementById("player-container");
  if (window.innerWidth < 768) {
    video.style.width = "100%";
    video.style.height = "100%";
    playerContainer.style.width = "100%";
    playerContainer.style.height = "100%";
  }
}

// region Video/attemptPlay
function attemptPlay() {
  const video = document.getElementById("video");
  video.play();
}

// region Table/populateTables
// biome-ignore lint/correctness/noUnusedVariables: HTML uses it
function populateTables() {
  populateAceInfoTables();
  populateStreamTable();
}

// region Table/populateAceInfoTables
function populateAceInfoTables() {
  getAcePool()
    .then((acePool) => {
      populateAceInfoTable(acePool);
      populateAcePoolTable(acePool.ace_instances);
    })
    .catch((_error) => {
      console.error(`Failed to fetch Ace Pool data: ${_error}`);
    });
}

// region Table/populateAceInfoTable
function populateAceInfoTable(acePool) {
  const aceInfoTable = document.getElementById("ace-info");
  aceInfoTable.innerHTML = ""; // Clear the table before adding new data
  const tr_heading = document.createElement("tr");
  const th_ace_version = document.createElement("th");
  th_ace_version.textContent = "Version";
  tr_heading.appendChild(th_ace_version);
  flashBackgroundColor(th_ace_version);

  const th_ace_instances = document.createElement("th");
  th_ace_instances.textContent = "Streams";
  tr_heading.appendChild(th_ace_instances);
  flashBackgroundColor(th_ace_instances);

  const th_ace_transcode_audio = document.createElement("th");
  th_ace_transcode_audio.textContent = "Transcode Audio";
  tr_heading.appendChild(th_ace_transcode_audio);
  flashBackgroundColor(th_ace_transcode_audio);

  const th_ace_pool_healthy = document.createElement("th");
  th_ace_pool_healthy.textContent = "Health";
  tr_heading.appendChild(th_ace_pool_healthy);
  flashBackgroundColor(th_ace_pool_healthy);

  aceInfoTable.appendChild(tr_heading);

  const tr = document.createElement("tr");
  // Ace version cell
  const td_ace_version = document.createElement("td");
  td_ace_version.textContent = acePool.ace_version;
  tr.appendChild(td_ace_version);

  // Ace instances cell
  const td_ace_instances = document.createElement("td");
  td_ace_instances.textContent = `${acePool.ace_instances.length}/${acePool.max_size}`;
  if (acePool.ace_instances.length >= acePool.max_size) {
    setStatusClass(td_ace_instances, "bad");
  }
  tr.appendChild(td_ace_instances);

  // Ace transcode audio cell
  const td_ace_transcode_audio = document.createElement("td");
  if (acePool.transcode_audio === true) {
    td_ace_transcode_audio.textContent = "Allegedly Enabled";
  } else {
    td_ace_transcode_audio.textContent = "Disabled";
  }
  tr.appendChild(td_ace_transcode_audio);

  // Ace pool health cell
  const td_ace_pool_healthy = document.createElement("td");
  if (acePool.healthy === false) {
    setStatusClass(td_ace_pool_healthy, "bad");
    td_ace_pool_healthy.textContent = "Failure";
  } else {
    setStatusClass(td_ace_pool_healthy, "neutral");
    td_ace_pool_healthy.textContent = "Healthy";
  }
  tr.appendChild(td_ace_pool_healthy);

  aceInfoTable.appendChild(tr);
}

// region Table/populateAcePoolTable
function populateAcePoolTable(aceInstances) {
  const poolTable = document.getElementById("ace-pool-info");
  poolTable.innerHTML = ""; // Clear the table before adding new data

  if (aceInstances.length === 0) {
    poolTable.style.display = "none";
    return;
  }

  poolTable.style.display = "table";

  const tr_heading = document.createElement("tr");
  const th_instance_number = document.createElement("th");
  th_instance_number.textContent = "#";
  tr_heading.appendChild(th_instance_number);
  flashBackgroundColor(th_instance_number);

  const th_status = document.createElement("th");
  th_status.textContent = "Status";
  tr_heading.appendChild(th_status);
  flashBackgroundColor(th_status);

  const th_quality = document.createElement("th");
  th_quality.textContent = "Quality";
  tr_heading.appendChild(th_quality);
  flashBackgroundColor(th_quality);

  const th_playing = document.createElement("th");
  th_playing.textContent = "Currently Playing";
  tr_heading.appendChild(th_playing);
  flashBackgroundColor(th_playing);

  const th_unlock = document.createElement("th");
  th_unlock.textContent = "Make Available";
  tr_heading.appendChild(th_unlock);
  flashBackgroundColor(th_unlock);

  poolTable.appendChild(tr_heading);

  for (const instance of aceInstances) {
    const tr = document.createElement("tr");

    // Instance number cell
    const td_instance_number = document.createElement("td");
    td_instance_number.textContent = `${instance.ace_pid}`;
    tr.appendChild(td_instance_number);

    // Status cell (Available/Locked In)
    const td_status = document.createElement("td");
    let lockedIn = "Available";
    if (instance.locked_in === true) {
      // Format the time until unlock
      const totalSeconds = instance.time_until_unlock;
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      timeUntilUnlockFormatted = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

      lockedIn = `🔒 Locked for ${timeUntilUnlockFormatted}`;
    }
    td_status.textContent = lockedIn;
    tr.appendChild(td_status);

    // Quality, currently playing (sorry for readability, do these together)
    const td_quality = document.createElement("td");

    const td_playing = document.createElement("td");
    if (instance.ace_content_id !== "") {
      getStream(instance.ace_content_id)
        .then((streamInfo) => {
          quality = streamInfo.quality || -1;
          if (quality === -1) {
            setStatusClass(td_quality, "neutral");
          } else if (quality < 20) {
            setStatusClass(td_quality, "bad");
          } else if (quality >= 20 && quality <= 80) {
            setStatusClass(td_quality, "neutral");
          } else if (quality >= 80) {
            setStatusClass(td_quality, "good");
          }
          td_quality.textContent = quality;

          td_playing.textContent = streamInfo.title || "Unknown Stream";
          td_playing.addEventListener("click", () => {
            loadPlayStream(instance.ace_content_id);
          });
          td_playing.classList.add("link");
          td_playing.title = streamInfo.program_title || "No program title";

          // Odd spot for this, but its the easiest way to refresh the current program info
          if (streamInfo.ace_content_id === window.location.hash.substring(1)) {
            populateCurrentStreamInfo(streamInfo.program_title, streamInfo.program_description);
          }
        })
        .catch((_error) => {});
    } else {
      td_playing.textContent = "-";
    }
    tr.appendChild(td_quality);
    tr.appendChild(td_playing);

    // Unlock button cell
    const td_unlock = document.createElement("td");
    const unlockButton = document.createElement("button");
    unlockButton.textContent = "Unlock";
    unlockButton.classList.add("unlock-button");
    unlockButton.onclick = () => {
      currentlyFetchingM3U8 = "";
      makeAcePoolInstanceAvailable(instance.ace_content_id)
        .then(() => {
          console.log(`Ace Pool instance ${instance.ace_content_id} made available`);
          populateAceInfoTables(); // Refresh the table after unlocking
        })
        .catch((_error) => {});
      populateAceInfoTables();
    };
    td_unlock.appendChild(unlockButton);

    tr.appendChild(td_unlock);

    poolTable.appendChild(tr);
  }
}

// region Table/populateStreamTable
function populateStreamTable() {
  const tableId = `stream-table`;

  getStreamsFlat()
    .then((streams) => {
      const table = document.getElementById(tableId);
      table.innerHTML = ""; // Clear the table before adding new data
      const tr_heading = document.createElement("tr");

      const th_quality = document.createElement("th");
      th_quality.textContent = "Quality";
      tr_heading.appendChild(th_quality);
      flashBackgroundColor(th_quality);

      const th_link = document.createElement("th");
      th_link.textContent = "Stream";
      tr_heading.appendChild(th_link);
      flashBackgroundColor(th_link);

      const th_program_title = document.createElement("th");
      th_program_title.textContent = "Program";
      tr_heading.appendChild(th_program_title);
      flashBackgroundColor(th_program_title);

      table.appendChild(tr_heading);

      // Sort the data by quality in descending order
      streams.sort((a, b) => b.quality - a.quality);

      for (const stream of streams) {
        const tr = document.createElement("tr");

        // Quality cell
        const td_quality = document.createElement("td");
        td_quality.textContent = `${stream.quality}`;
        if (stream.quality === -1) {
          setStatusClass(td_quality, "neutral");
          td_quality.textContent = "?";
        } else if (stream.quality < 20) {
          setStatusClass(td_quality, "bad");
        } else if (stream.quality >= 20 && stream.quality <= 80) {
          setStatusClass(td_quality, "neutral");
        } else if (stream.quality >= 80) {
          setStatusClass(td_quality, "good");
        }
        td_quality.classList.add("quality-code");

        // Link cell
        td_link = document.createElement("td");
        const a = document.createElement("a"); // Create a new anchor element
        a.textContent = `${stream.title}`;
        a.onclick = () => loadPlayStream(stream.ace_content_id);
        td_link.appendChild(a); // Append the anchor element to the table data cell

        // Program title cell
        const td_program_title = document.createElement("td");
        if (stream.program_title && stream.program_title !== "") {
          td_program_title.textContent = stream.program_title;
          if (stream.program_description && stream.program_description !== "") {
            td_program_title.title = stream.program_description;
          } else {
            td_program_title.title = "No program description available";
          }
        } else {
          td_program_title.textContent = "-";
        }

        // Append to the row
        tr.appendChild(td_quality);
        tr.appendChild(td_link);
        tr.appendChild(td_program_title);
        table.appendChild(tr);
      }
    })
    .catch((_error) => {});
}

// region Current Stream Info
function populateCurrentStreamInfo(programTitle, programDescription) {
  console.log("Populating current stream info...");

  const streamProgramNameElement = document.getElementById("stream-program-name");
  if (programTitle === null || programTitle === "") {
    streamProgramNameElement.innerHTML = "No program name";
    streamProgramNameElement.classList.add("hidden");
  } else {
    streamProgramNameElement.classList.remove("hidden");
    streamProgramNameElement.innerHTML = programTitle;
  }

  const streamProgramDescriptionElement = document.getElementById("stream-program-description");
  if (programDescription === null || programDescription === "") {
    streamProgramDescriptionElement.classList.add("hidden");
    streamProgramDescriptionElement.innerHTML = "No program description";
  } else {
    streamProgramDescriptionElement.classList.remove("hidden");
    streamProgramDescriptionElement.innerHTML = programDescription;
  }
}

// region DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  resizePlayerMobile();

  // Init stream status
  const streamStatus = document.getElementById("stream-status");
  setStatusClass(streamStatus, "neutral");
  streamStatus.innerHTML = "Ready to load a stream";

  // Populate tables
  populateAceInfoTables();
  setInterval(populateAceInfoTables, 30000);
  populateStreamTable();
  setInterval(populateStreamTable, 95007);

  // Check if Hls is even defined
  if (typeof Hls === "undefined") {
    console.error("Hls.js is not defined. Check if loaded");
    const playerStatus = document.getElementById("player-status");
    setStatusClass(playerStatus, "bad");
    playerStatus.innerHTML = "Hls.js is not defined. Whoever set this up didn't run npm install.";
    setOnPageStreamErrorMessage("Probably working if you use the direct link.");
    return;
  }

  // Check the page hash for a stream ID, load it if present
  const aceContentId = window.location.hash.substring(1);
  if (aceContentId) {
    console.log(`Loading stream on page load: ${aceContentId}`);
    getStream(aceContentId)
      .then((streamInfo) => {
        loadStreamUrl(aceContentId, streamInfo);
      })
      .catch((_error) => {});
  }

  // Check every second if the video is playing, to populate the status
  setInterval(checkIfPlaying, 1000);

  // Set up the load stream button
  loadStreamButton = document.getElementById("load-stream-button");
  loadStreamButton.onclick = () => {
    const aceContentId = document.getElementById("stream-id-input").value;
    if (aceContentId) {
      loadPlayStream(aceContentId);
    }
  };
});
