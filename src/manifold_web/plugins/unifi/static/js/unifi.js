function toggleKabobMenu(id) {
    document.querySelectorAll('.kabob-menu').forEach(menu => menu.classList.add('hidden'));
    const container = document.getElementById(`kabob-${id}`);
    const menu = container.querySelector('.kabob-menu');
    menu.classList.toggle('hidden');
}

document.addEventListener("click", function (event) {
    if (!event.target.classList.contains("kabob-button")) {
        document.querySelectorAll('.kabob-menu').forEach(menu => menu.classList.add('hidden'));
    }
});

function fetchSites(serverId, serverName) {
    fetch(`/unifi/${serverId}/sites`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch sites");
            }
            return response.json();
        })
        .then(data => {
            showSitesModal(serverName, data);
        })
        .catch(err => {
            alert("Error: " + err.message);
        });
}

function showAllSites() {
    fetchSites("all", "All Servers");
}

function submitSyncSites() {
    document.getElementById("sync-sites-form").submit();
}

function submitSyncDevices(serverId = "") {
    const input = document.getElementById("sync-devices-server-id");
    input.value = serverId;
    document.getElementById("sync-devices-form").submit();
}

function openLookupModal() {
    document.getElementById("lookup-modal").classList.remove("hidden");
    document.getElementById("lookup-identifier").value = "";
    document.getElementById("lookup-results").textContent = "";
}

function hideLookupModal() {
    document.getElementById("lookup-modal").classList.add("hidden");
}

function submitDeviceLookup(event) {
    event.preventDefault();  // prevent page reload

    const input = document.getElementById("lookup-identifier");
    const identifier = input.value.trim();

    fetch("/unifi/lookup-device", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ identifier: identifier })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }
        return response.json();
    })
    .then(data => {
        const results = document.getElementById("lookup-results");

        if (data.error) {
            results.textContent = "Error: " + data.error;
        } else {
            const result = `
Server: ${data.server}
Site: ${data.site}
Name: ${data.name}
Model: ${data.model}
Serial: ${data.serial}
MACs: ${data.macs.join(", ")}
IPs: ${data.ips.join(", ")}
Last Seen: ${data.last_seen}
Uptime: ${data.uptime}
State: ${data.state}`;
            results.textContent = result;
        }
    })
    .catch(err => {
        document.getElementById("lookup-results").textContent = "Error: " + err.message;
    });
}

function showAddServerModal() {
    // logic to display modal
    const modal = document.getElementById("addServerModal");
    if (modal) {
        modal.style.display = "block";
    }
}