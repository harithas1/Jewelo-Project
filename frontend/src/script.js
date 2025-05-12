function toggleDropdown() {
  const dropdown = document.getElementById("profileDropdown");
  dropdown.style.display =
    dropdown.style.display === "block" ? "none" : "block";
}

window.addEventListener("click", function (event) {
  const dropdown = document.getElementById("profileDropdown");
  const profileIcon = document.querySelector(".profile-icon");
  if (!profileIcon.contains(event.target) && !dropdown.contains(event.target)) {
    dropdown.style.display = "none";
  }
});
function handleClick(productId) {
  const token = localStorage.getItem("Jewelo_token");
  const user_id = Number(localStorage.getItem("User_id"));
  if (!token) {
    alert("Please login to add products to your cart.");
    return;
  }
  console.log(user_id + ":" + productId);
  fetch("https://jewelo-project-backend.onrender.com/cart/add", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      product_id: productId,
      user_id: user_id,
      quantity: 1,
    }),
  })
    .then((response) => {
      console.log(response);
      if (!response.ok) {
        throw new Error("Failed to add product to cart");
      }
      return response.json();
    })
    .then((data) => {
      console.log("Product added to cart:", data);
      alert("Product added to cart!");
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Could not add product to cart. Try again.");
    });
}

function goToProduct(productId) {
  window.location.href = `ProductDetails.html?id=${productId}`;
}
function goToOrders() {
  window.location.href = `Orders.html`;
}
function Logout() {
  localStorage.removeItem("Jewelo_token");
  window.location.reload();
  window.location.href = `Index.html`;
}
function updateProfileDropdown() {
  const token = localStorage.getItem("Jewelo_token");
  const profileDropdown = document.getElementById("profileDropdown");

  if (token) {
    profileDropdown.innerHTML = `
      <a href="#" onclick="goToOrders()">
        <span><i class="fa-solid fa-user"></i> Orders</span>
      </a>
      <a href="#" onclick="Logout()">
        <span><i class="fa-solid fa-circle-xmark"></i>Logout</span>
      </a>
    `;
  } else {
    profileDropdown.innerHTML = `
      <a href="/login.html">
        <span><i class="fa-solid fa-right-to-bracket"></i> Login</span>
      </a>
    `;
  }
}

// Call the function to update the profile dropdown when the page loads
window.onload = updateProfileDropdown;
