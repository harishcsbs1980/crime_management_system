document.addEventListener("DOMContentLoaded", function () {
    // Mobile sidebar toggle
    var toggle = document.getElementById("menuToggle");
    var sidebar = document.getElementById("sidebar");
    if (toggle && sidebar) {
        toggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });
    }

    // Auto-dismiss flash messages
    document.querySelectorAll(".flash").forEach(function (el) {
        var timer = setTimeout(function () { el.remove(); }, 5000);
        var closeBtn = el.querySelector("button");
        if (closeBtn) {
            closeBtn.addEventListener("click", function () {
                clearTimeout(timer);
                el.remove();
            });
        }
    });

    // Simple tab system: elements with [data-tab-target]
    document.querySelectorAll(".tab-link").forEach(function (tab) {
        tab.addEventListener("click", function () {
            var group = tab.closest(".tabs").dataset.group;
            var target = tab.dataset.tabTarget;
            document.querySelectorAll('.tab-link[data-group-ref="' + group + '"]').forEach(function (t) {
                t.classList.remove("active");
            });
            document.querySelectorAll('.tab-panel[data-group-ref="' + group + '"]').forEach(function (p) {
                p.classList.remove("active");
            });
            tab.classList.add("active");
            document.querySelector('.tab-panel[data-tab-id="' + target + '"][data-group-ref="' + group + '"]').classList.add("active");
        });
    });

    // Confirm-before-delete on any [data-confirm] form
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            if (!confirm(form.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});
