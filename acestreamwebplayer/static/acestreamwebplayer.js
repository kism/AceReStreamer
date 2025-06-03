function getHello() {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => controller.abort(), 1000); // 1 second timeout:

  // GET the hello endpoint that the flask app has
  fetch("hello", {
    method: "GET",
    signal: controller.signal,
  })
    .then((response) => {
      // Check if the request was successful (status code 200)
      if (response.ok) {
        return response.json(); // We interoperate the response as json and pass it along...
      } else {
        document.getElementById("MY_COOL_FIELD").innerHTML = `API FAILURE`; // Set message in element to indicate failure
        document.getElementById("MY_COOL_RESULT").innerHTML = `${response.status}`; // Set message in element to message received from flask
        document.getElementById("MY_COOL_RESULT").style.color = "#800000"; // Set message in element to message received from flask

        throw new Error(`Error fetching data. Status code: ${response.status}`);
      }
    })
    .then((data) => {
      const msg = data.msg; // Get the 'msg' field from the JSON data
      document.getElementById("MY_COOL_FIELD").innerHTML = `API SUCCESS`; // Set message in element to indicate success
      document.getElementById("MY_COOL_RESULT").innerHTML = msg; // Set message in element to message received from flask
      document.getElementById("MY_COOL_RESULT").style.color = "#008000"; // Set message in element to message received from flask
    })
    .catch((error) => {
      clearTimeout(timeoutId); //Stop the timeout since we only care about the GET timing out
      if (error.name === "AbortError") {
        console.error("Fetch request timed out");
        document.getElementById("MY_COOL_FIELD").innerHTML = `API FAILURE`; // Set message in element to indicate failure
        document.getElementById("MY_COOL_RESULT").innerHTML = `Fetch Timeout`; // Set message in element to message received from flask
        document.getElementById("MY_COOL_RESULT").style.color = "#800000"; // Set message in element to message received from flask
      } else {
        console.error(`Error: ${error.message}`);
      }
    });
}

//On page load we run this code, running the function getHello()
getHello();
//We call every 5 seconds, using setInterval waits for the timeout even on the first call hence why we call it normally first
setInterval(getHello, 5000);
