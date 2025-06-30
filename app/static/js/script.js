document.addEventListener("DOMContentLoaded", function () {
    const openLoginBtn = document.getElementById("openLoginBtn");
    const closeLoginBtn = document.getElementById("closeLoginBtn");
    const loginModal = document.getElementById("loginModal");
  
    const openSignupBtn = document.getElementById("openSignupBtn");
    const closeSignupBtn = document.getElementById("closeSignupBtn");
    const signupModal = document.getElementById("signupModal");
  
    // 🔓 Open Login Modal
    if (openLoginBtn && loginModal) {
      openLoginBtn.addEventListener("click", () => {
        loginModal.classList.remove("hidden");
      });
    }
  
    // ❌ Close Login Modal
    if (closeLoginBtn && loginModal) {
      closeLoginBtn.addEventListener("click", () => {
        loginModal.classList.add("hidden");
      });
      loginModal.addEventListener("click", (e) => {
        if (e.target === loginModal) {
          loginModal.classList.add("hidden");
        }
      });
    }
  
    // 🔓 Open Signup Modal
    if (openSignupBtn && signupModal) {
      openSignupBtn.addEventListener("click", () => {
        signupModal.classList.remove("hidden");
      });
    }
  
    // ❌ Close Signup Modal
    if (closeSignupBtn && signupModal) {
      closeSignupBtn.addEventListener("click", () => {
        signupModal.classList.add("hidden");
      });
      signupModal.addEventListener("click", (e) => {
        if (e.target === signupModal) {
          signupModal.classList.add("hidden");
        }
      });
    }
  });
  