function printSuccess(message) {
  document.getElementById("login-test").innerHTML = message;
  document.getElementById("login-test").style.color = "#00FF00";
  document.getElementById("login-redirect").style.display = "initial";
}

function printFailure(message) {
  document.getElementById("login-test").innerHTML = message;
  document.getElementById("login-test").style.color = "#FFCCCC";
}

function hideLoginForm() {
  let loginForm = document.getElementById("login-form");
  loginForm.style.display = "none";
}

function checkAuthentication() {
  fetch("/api/authenticate", {
    method: "GET",
  }).then((response) => {
    if (response.ok) {
      printSuccess(`Already authenticated!`);
      hideLoginForm();
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("login-form").onsubmit = async function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Collect form data
    const formData = new FormData(this);

    try {
      // Send form data using Fetch API
      const response = await fetch("/api/authenticate", {
        method: "POST",
        body: formData,
      });

      // Check if the request was successful
      if (response.ok) {
        printSuccess(`Authenticated!`);
        hideLoginForm();
      } else {
        printFailure(`Authentication Failure`);
      }
    } catch (error) {
      // Handle errors (e.g., display an error message)
      printFailure("Form submission failed: " + error.message);
    }
  };
  checkAuthentication();
});
