document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    });
  });

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", function (e) {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = "⏳ Processing...";
        submitBtn.disabled = true;

        setTimeout(() => {
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }, 5000);
      }
    });
  });

  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";
      setTimeout(() => {
        alert.remove();
      }, 300);
    }, 5000);
  });

  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("click", function (e) {
      if (e.target === this) {
        this.style.transform = "scale(0.98)";
        setTimeout(() => {
          this.style.transform = "scale(1)";
        }, 150);
      }
    });
  });

  document.querySelectorAll(".progress-fill").forEach((progressBar) => {
    const progress = progressBar.getAttribute("data-progress") || "0";
    const width = progress + "%";
    progressBar.style.width = "0%";
    setTimeout(() => {
      progressBar.style.width = width;
    }, 500);
  });

  document.querySelectorAll(".list-item").forEach((item) => {
    item.addEventListener("mouseenter", function () {
      this.style.transform = "translateX(5px)";
    });

    item.addEventListener("mouseleave", function () {
      this.style.transform = "translateX(0)";
    });
  });

  document.querySelectorAll("input[required]").forEach((input) => {
    input.addEventListener("invalid", function (e) {
      e.preventDefault();
      this.classList.add("error");

      this.addEventListener(
        "input",
        function () {
          this.classList.remove("error");
        },
        { once: true }
      );
    });
  });

  document
    .querySelectorAll(".form-group input, .form-group select")
    .forEach((input) => {
      const label = input.parentElement.querySelector("label");
      if (label) {
        input.addEventListener("focus", function () {
          label.style.color = "#667eea";
          label.style.transform = "translateY(-2px)";
        });

        input.addEventListener("blur", function () {
          label.style.color = "#555";
          label.style.transform = "translateY(0)";
        });
      }
    });

  document.querySelectorAll(".btn").forEach((button) => {
    button.addEventListener("click", function (e) {
      const ripple = document.createElement("div");
      ripple.style.position = "absolute";
      ripple.style.borderRadius = "50%";
      ripple.style.background = "rgba(255, 255, 255, 0.6)";
      ripple.style.transform = "scale(0)";
      ripple.style.animation = "ripple 0.6s linear";
      ripple.style.pointerEvents = "none";

      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = e.clientX - rect.left - size / 2 + "px";
      ripple.style.top = e.clientY - rect.top - size / 2 + "px";

      button.style.position = "relative";
      button.style.overflow = "hidden";
      button.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });

  const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

  document.addEventListener("keydown", function (e) {
    if (e.key === "Tab") {
      document.body.classList.add("keyboard-navigation");
    }
  });

  document.addEventListener("mousedown", function () {
    document.body.classList.remove("keyboard-navigation");
  });

  if ("IntersectionObserver" in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.remove("lazy");
          imageObserver.unobserve(img);
        }
      });
    });

    document.querySelectorAll("img[data-src]").forEach((img) => {
      imageObserver.observe(img);
    });
  }
});

const style = document.createElement("style");
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .error {
        border-color: #dc3545 !important;
        box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1) !important;
    }
    
    .keyboard-navigation :focus {
        outline: 2px solid #667eea !important;
        outline-offset: 2px !important;
    }
    
    .lazy {
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .lazy.loaded {
        opacity: 1;
    }
`;
document.head.appendChild(style);
