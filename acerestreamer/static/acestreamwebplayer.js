// globals

let isAttemptingPlay = false;

// region API calls
function getStream(streamId) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  // GET the hello endpoint that the flask app has
  return fetch(`/api/stream/${streamId}`, {
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

function getStreams() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  return fetch("/api/streams/flat", {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      const streamStatus = document.getElementById("stream-status");
      setStatusClass(streamStatus, "bad");
      streamStatus.innerHTML = `Stream list FAILURE ${response.status}`;

      throw new Error(`Error fetching data. Status code: ${response.status}`);
    })
    .then((data) => {
      return data;
    })
    .catch((error) => {
      clearTimeout(timeoutId); //Stop the timeout since we only care about the GET timing out
      if (error.name === "AbortError") {
        console.error("getStreams Fetch request timed out");
        const streamStatus = document.getElementById("stream-status");
        setStatusClass(streamStatus, "bad");
        streamStatus.innerHTML = "Stream list API FAILURE: Fetch Timeout";
      } else {
        console.error(`getStreams Error: ${error.message}`);
      }
      throw error;
    });
}

function getAcePool() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  return fetch("/api/ace_pool", {
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

function makeAcePoolInstanceAvailable(aceId) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  return fetch(`/api/ace_pool/${aceId}`, {
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

// region Stream handling

function loadStream() {
  const video = document.getElementById("video");
  const videoSrc = `/hls/${window.location.hash.substring(1)}`;
  console.log(`Loading stream: ${videoSrc}`);

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
        attemptPlayWithRetry();
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

function loadStreamUrl(streamId, streamName) {
  window.location.hash = streamId; // Set the URL in the hash
  document.getElementById("stream-name").innerText = streamName;
  loadStream();
}

function loadPlayStream(streamID) {
  getStream(streamID)
    .then((streamInfo) => {
      loadStreamUrl(streamID, streamInfo.title);

      // Try to play with retry logic
      attemptPlayWithRetry();
    })
    .catch((error) => {
      console.error("Failed to get stream info:", error);
      loadStreamUrl(streamID, streamID);
      attemptPlayWithRetry();
    });
}

// biome-ignore lint/correctness/noUnusedVariables: HTML uses it
function loadPlayStreamFromHash() {
  const streamId = window.location.hash.substring(1);
  if (streamId) {
    console.log(`Loading stream from hash: ${streamId}`);
    loadPlayStream(streamId);
  } else {
    console.error("No stream ID loaded...");
    setOnPageStreamErrorMessage("No stream ID loaded...");
  }
}

// endregion

// region Video Player

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

function attemptPlayWithRetry(maxAttempts = 3, currentAttempt = 1) {
  const video = document.getElementById("video");
  const playerStatus = document.getElementById("player-status");

  if (isAttemptingPlay) {
    console.log("Already attempting to play the video, skipping this attempt.");
    return;
  }
  isAttemptingPlay = true;

  setTimeout(() => {
    video
      .play()
      .then(() => {
        console.log(`Play attempt ${currentAttempt} initiated`);
        setStatusClass(playerStatus, "neutral");
        playerStatus.innerHTML = `Attempting to play... (${currentAttempt}/${maxAttempts})`;

        // Check if video actually started playing after a brief delay
        setTimeout(() => {
          if (video.paused || video.ended || video.currentTime === 0) {
            setStatusClass(playerStatus, "bad");

            console.log(`Play attempt ${currentAttempt} failed - video not playing`);
            if (currentAttempt < maxAttempts) {
              console.log(`Retrying... (${currentAttempt + 1}/${maxAttempts})`);
              attemptPlayWithRetry(maxAttempts, currentAttempt + 1);
            } else {
              console.error("All play attempts failed");
              setOnPageStreamErrorMessage("Failed to start video playback after multiple attempts");
              isAttemptingPlay = false; // Reset flag when done
            }
          } else {
            playerStatus.innerHTML = "Playing";
            setStatusClass(playerStatus, "good");
            console.log(`Video successfully started playing on attempt ${currentAttempt}`);
            isAttemptingPlay = false; // Reset flag when done
            populateAcePoolTable();
          }
        }, 500); // Check after 500ms
      })
      .catch((error) => {
        console.error(`Play attempt ${currentAttempt} error:`, error);

        if (currentAttempt < maxAttempts) {
          console.log(`Retrying after error... (${currentAttempt + 1}/${maxAttempts})`);
          attemptPlayWithRetry(maxAttempts, currentAttempt + 1);
        } else {
          console.error("All play attempts failed with errors");
          setOnPageStreamErrorMessage("Error playing video after multiple attempts");
          isAttemptingPlay = false; // Reset flag when done
        }
      });
  }, 1000 * currentAttempt); // Increase delay with each attempt
}

// region Ace Pool Table

function populateAcePoolTable() {
  getAcePool()
    .then((acePool) => {
      const table = document.getElementById("ace-info");
      table.innerHTML = ""; // Clear the table before adding new data
      const tr_heading = document.createElement("tr");
      const th_instance_number = document.createElement("th");
      th_instance_number.textContent = "#";
      tr_heading.appendChild(th_instance_number);
      flashBackgroundColor(th_instance_number);

      const th_health = document.createElement("th");
      th_health.textContent = "Health";
      tr_heading.appendChild(th_health);
      flashBackgroundColor(th_health);

      const th_status = document.createElement("th");
      th_status.textContent = "Status";
      tr_heading.appendChild(th_status);
      flashBackgroundColor(th_status);

      const th_playing = document.createElement("th");
      th_playing.textContent = "Currently Playing";
      tr_heading.appendChild(th_playing);
      flashBackgroundColor(th_playing);

      const th_unlock = document.createElement("th");
      th_unlock.textContent = "Unlock";
      tr_heading.appendChild(th_unlock);
      flashBackgroundColor(th_unlock);

      table.appendChild(tr_heading);

      let n = 1;
      for (const instance of acePool) {
        const tr = document.createElement("tr");

        // Instance number cell
        const td_instance_number = document.createElement("td");
        td_instance_number.textContent = `${n}`;
        n++;
        tr.appendChild(td_instance_number);

        // Health cell
        const td_health = document.createElement("td");
        let timeUntilUnlockFormatted = "";
        if (instance.healthy === false) {
          setStatusClass(td_health, "bad");
          td_health.textContent = "Failure";
        } else {
          setStatusClass(td_health, "good");
          td_health.textContent = "Healthy";
        }
        tr.appendChild(td_health);

        // Status cell (Available/Locked In)
        const td_status = document.createElement("td");
        let lockedIn = "Available";
        if (instance.locked_in === true) {
          // Format the time until unlock
          const totalSeconds = instance.time_until_unlock;
          const minutes = Math.floor(totalSeconds / 60);
          const seconds = totalSeconds % 60;
          timeUntilUnlockFormatted = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

          lockedIn = `🔒 Reserved for ${timeUntilUnlockFormatted}`;
        }
        td_status.textContent = lockedIn;
        tr.appendChild(td_status);

        // Now Playing cell
        const td_playing = document.createElement("td");
        if (instance.ace_id !== "") {
          getStream(instance.ace_id)
            .then((streamInfo) => {
              td_playing.textContent = streamInfo.title || "Unknown Stream";
              td_playing.addEventListener("click", () => {
                loadPlayStream(instance.ace_id);
              });
              td_playing.classList.add("link");
            })
            .catch((_error) => {});
        } else {
          td_playing.textContent = "-";
        }
        tr.appendChild(td_playing);

        // Unlock button cell
        const td_unlock = document.createElement("td");
        if (instance.locked_in === true) {
          const unlockButton = document.createElement("button");
          unlockButton.textContent = "Unlock";
          unlockButton.classList.add("unlock-button");
          unlockButton.onclick = () => {
            makeAcePoolInstanceAvailable(instance.ace_id)
              .then(() => {
                console.log(`Ace Pool instance ${instance.ace_id} made available`);
                populateAcePoolTable(); // Refresh the table after unlocking
              })
              .catch((_error) => {});
            populateAcePoolTable();
          };
          td_unlock.appendChild(unlockButton);
        } else {
          td_unlock.textContent = "N/A";
        }
        tr.appendChild(td_unlock);

        table.appendChild(tr);
      }
    })
    .catch((_error) => {});
}

// region Stream Table

function populateStreamTable() {
  getStreams()
    .then((streams) => {
      const table = document.getElementById("stream-table");
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

      const th_source = document.createElement("th");
      th_source.textContent = "Source";
      flashBackgroundColor(th_source);

      tr_heading.appendChild(th_source);
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
        a.onclick = () => loadPlayStream(stream.ace_id);
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
    .catch((_error) => {});
}

// endregion

// region DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  resizePlayerMobile();

  // Init stream status
  const streamStatus = document.getElementById("stream-status");
  setStatusClass(streamStatus, "neutral");
  streamStatus.innerHTML = "Ready to load a stream";

  // Populate tables
  populateAcePoolTable();
  setInterval(populateAcePoolTable, 30000);
  populateStreamTable();
  setInterval(populateStreamTable, 95001);

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
  const streamId = window.location.hash.substring(1);
  if (streamId) {
    console.log(`Loading stream on page load: ${streamId}`);
    getStream(streamId)
      .then((streamInfo) => {
        loadStreamUrl(streamId, streamInfo.title);
      })
      .catch((_error) => {});
  }

  // Check every second if the video is playing, to populate the status
  setInterval(checkIfPlaying, 1000);

  // Set up the load stream button
  loadStreamButton = document.getElementById("load-stream-button");
  loadStreamButton.onclick = () => {
    const streamId = document.getElementById("stream-id-input").value;
    if (streamId) {
      loadPlayStream(streamId);
    }
  };
});
