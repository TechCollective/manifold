// Autotask Custom Actions
function testAutotaskConnection(integrationId, integrationName) {
    // TODO: Implement Autotask connection test
    alert(`Testing connection for ${integrationName}...`);
}

function syncAutotaskTickets(integrationId, integrationName) {
    // TODO: Implement Autotask ticket sync
    alert(`Syncing tickets for ${integrationName}...`);
}

// Slack Custom Actions
function testSlackConnection(integrationId, integrationName) {
    // TODO: Implement Slack connection test
    alert(`Testing Slack connection for ${integrationName}...`);
}

function listSlackChannels(integrationId, integrationName) {
    // TODO: Implement Slack channel listing
    alert(`Listing channels for ${integrationName}...`);
}

// UniFi Custom Actions
function showUnifiSites(integrationId, integrationName) {
    fetch(`/unifi/${integrationId}/sites`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch sites");
            }
            return response.json();
        })
        .then(data => {
            showSitesModal(integrationName, data);
        })
        .catch(err => {
            alert("Error: " + err.message);
        });
}

function syncUnifiDevices(integrationId, integrationName) {
    // Submit the sync devices form
    document.getElementById("sync-devices-form").submit();
}

function openUnifiLookup(integrationId, integrationName) {
    document.getElementById("lookup-modal").classList.remove("hidden");
    document.getElementById("lookup-identifier").value = "";
    document.getElementById("lookup-results").textContent = "";
}

// Sites Modal Functions (from unifi_modals.html)
function showSitesModal(serverName, sites) {
    document.getElementById("sites-modal-title").textContent = serverName;
    const tbody = document.getElementById("sites-table-body");
    tbody.innerHTML = "";

    if (sites.length === 0) {
        const row = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 3;
        td.textContent = "No sites found.";
        row.appendChild(td);
        tbody.appendChild(row);
    } else {
        for (const site of sites) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${site.name}</td>
                <td>${site.desc || ""}</td>
                <td>${site.role || ""}</td>
            `;
            tbody.appendChild(row);
        }
    }

    document.getElementById("sites-modal").classList.remove("hidden");
}

function hideSitesModal() {
    document.getElementById("sites-modal").classList.add("hidden");
}

// Lookup Modal Functions
function hideLookupModal() {
    document.getElementById("lookup-modal").classList.add("hidden");
}

function submitDeviceLookup(event) {
    event.preventDefault();

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