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
    
    // Close modals when clicking outside
    if (event.target.classList.contains('modal')) {
        event.target.classList.add('hidden');
    }
});

// Close modals with Escape key
document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        document.querySelectorAll('.modal').forEach(modal => modal.classList.add('hidden'));
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

function hideSitesModal() {
    document.getElementById("sites-modal").classList.add("hidden");
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
    document.getElementById("addServerModal").classList.remove("hidden");
}

function hideAddServerModal() {
    document.getElementById("addServerModal").classList.add("hidden");
}

// Admin Management Functions
function fetchAdmins(serverId, serverName) {
    fetch(`/unifi/${serverId}/admins`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch admins");
            }
            return response.json();
        })
        .then(data => {
            showAdminsModal(serverName, data, serverId);
        })
        .catch(err => {
            alert("Error: " + err.message);
        });
}

function showAllAdmins() {
    fetch("/unifi/admins")
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch admins");
            }
            return response.json();
        })
        .then(data => {
            showAdminsModal("All Servers", data);
        })
        .catch(err => {
            alert("Error: " + err.message);
        });
}

function showAdminsModal(serverName, admins, serverId = null) {
    const modal = document.getElementById("admins-modal");
    const content = document.getElementById("admins-content");
    
    let html = `<h4>${serverName}</h4>`;
    
    if (admins.length === 0) {
        html += "<p>No admins found.</p>";
    } else {
        html += "<table class='data-table'>";
        html += "<thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></thead><tbody>";
        
        admins.forEach(admin => {
            const adminId = admin._id || admin.id;
            const name = admin.name || admin.username || "Unknown";
            const email = admin.email || "N/A";
            const role = admin.role || admin.super_admin ? "Super Admin" : "Admin";
            
            html += `<tr>
                <td>${name}</td>
                <td>${email}</td>
                <td>${role}</td>
                <td>
                    <button onclick="showAdminInfo('${adminId}', '${serverId || 'all'}')" class="command-button small">Info</button>
                    ${serverId ? `<button onclick="showRemoveAdminModal('${adminId}', '${name}', '${serverId}')" class="command-button small danger">Remove</button>` : ''}
                </td>
            </tr>`;
        });
        
        html += "</tbody></table>";
    }
    
    content.innerHTML = html;
    modal.classList.remove("hidden");
}

function hideAdminsModal() {
    document.getElementById("admins-modal").classList.add("hidden");
}

function showAdminInfo(adminId, serverId) {
    const modal = document.getElementById("admin-info-modal");
    const content = document.getElementById("admin-info-content");
    
    content.innerHTML = "<div class='loading'>Loading admin information...</div>";
    modal.classList.remove("hidden");
    
    const url = serverId === 'all' ? `/unifi/admins` : `/unifi/${serverId}/admins/${adminId}/info`;
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch admin information");
            }
            return response.json();
        })
        .then(data => {
            let html = "<div class='admin-info'>";
            
            if (Array.isArray(data)) {
                // Multiple admins from all servers
                data.forEach(admin => {
                    if (admin._id === adminId || admin.id === adminId) {
                        html += formatAdminInfo(admin);
                    }
                });
            } else {
                // Single admin info
                html += formatAdminInfo(data);
            }
            
            html += "</div>";
            content.innerHTML = html;
        })
        .catch(err => {
            content.innerHTML = "<p class='error'>Error: " + err.message + "</p>";
        });
}

function formatAdminInfo(admin) {
    let html = "<div class='admin-details'>";
    html += `<h4>${admin.name || admin.username || "Unknown"}</h4>`;
    html += `<p><strong>Email:</strong> ${admin.email || "N/A"}</p>`;
    html += `<p><strong>Role:</strong> ${admin.role || (admin.super_admin ? "Super Admin" : "Admin")}</p>`;
    
    if (admin.server_name) {
        html += `<p><strong>Server:</strong> ${admin.server_name} (${admin.server_host})</p>`;
    }
    
    if (admin.sites && admin.sites.length > 0) {
        html += "<p><strong>Sites:</strong></p><ul>";
        admin.sites.forEach(site => {
            html += `<li>${site.name} - ${site.role || "Admin"}</li>`;
        });
        html += "</ul>";
    }
    
    html += "</div>";
    return html;
}

function hideAdminInfoModal() {
    document.getElementById("admin-info-modal").classList.add("hidden");
}

function showRemoveAdminModal(adminId, adminName, serverId) {
    const modal = document.getElementById("remove-admin-modal");
    const details = document.getElementById("remove-admin-details");
    const form = document.getElementById("remove-admin-form");
    
    details.innerHTML = `<p><strong>Admin:</strong> ${adminName}</p><p><strong>Server ID:</strong> ${serverId}</p>`;
    form.dataset.adminId = adminId;
    form.dataset.serverId = serverId;
    
    modal.classList.remove("hidden");
}

function hideRemoveAdminModal() {
    document.getElementById("remove-admin-modal").classList.add("hidden");
    document.getElementById("exclude-sites").value = "";
}

function submitRemoveAdmin(event) {
    event.preventDefault();
    
    const form = event.target;
    const adminId = form.dataset.adminId;
    const serverId = form.dataset.serverId;
    const excludeSites = document.getElementById("exclude-sites").value
        .split(",")
        .map(site => site.trim())
        .filter(site => site.length > 0);
    
    fetch(`/unifi/${serverId}/admins/${adminId}/remove`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ exclude_sites: excludeSites })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to remove admin");
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            alert("Admin removed successfully!");
            hideRemoveAdminModal();
            // Refresh the admins list if it's currently open
            const adminsModal = document.getElementById("admins-modal");
            if (!adminsModal.classList.contains("hidden")) {
                fetchAdmins(serverId, "Server");
            }
        }
    })
    .catch(err => {
        alert("Error: " + err.message);
    });
}

// Tab Navigation Functions
function switchTab(tabName) {
    // Hide all action areas
    document.querySelectorAll('.actions-area').forEach(area => {
        area.classList.add('hidden');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected action area
    document.getElementById(`actions-${tabName}`).classList.remove('hidden');
    
    // Add active class to selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

function refreshServerList() {
    location.reload();
}

function deleteServer(serverId, serverName) {
    if (confirm(`Are you sure you want to delete server "${serverName}"?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/unifi/delete/${serverId}`;
        document.body.appendChild(form);
        form.submit();
    }
}

function showAdminSearch() {
    document.getElementById("admin-search-modal").classList.remove("hidden");
    document.getElementById("search-term").value = "";
    document.getElementById("search-results").innerHTML = "";
}

function hideAdminSearchModal() {
    document.getElementById("admin-search-modal").classList.add("hidden");
}

function submitAdminSearch(event) {
    event.preventDefault();
    
    const searchTerm = document.getElementById("search-term").value.trim();
    const resultsDiv = document.getElementById("search-results");
    
    if (!searchTerm) {
        resultsDiv.innerHTML = "<p class='error'>Please enter a search term.</p>";
        return;
    }
    
    resultsDiv.innerHTML = "<div class='loading'>Searching...</div>";
    
    fetch("/unifi/admins")
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch admins");
            }
            return response.json();
        })
        .then(data => {
            const filteredAdmins = data.filter(admin => {
                const name = admin.name || admin.username || "";
                const email = admin.email || "";
                const searchLower = searchTerm.toLowerCase();
                return name.toLowerCase().includes(searchLower) || 
                       email.toLowerCase().includes(searchLower);
            });
            
            if (filteredAdmins.length === 0) {
                resultsDiv.innerHTML = "<p class='error'>No admins found matching your search.</p>";
            } else {
                let html = `<h4>Search Results for "${searchTerm}" (${filteredAdmins.length} found)</h4>`;
                html += "<table class='data-table'>";
                html += "<thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Server</th><th>Actions</th></tr></thead><tbody>";
                
                filteredAdmins.forEach(admin => {
                    const adminId = admin._id || admin.id;
                    const name = admin.name || admin.username || "Unknown";
                    const email = admin.email || "N/A";
                    const role = admin.role || admin.super_admin ? "Super Admin" : "Admin";
                    const server = admin.server_name || "Unknown";
                    
                    html += `<tr>
                        <td>${name}</td>
                        <td>${email}</td>
                        <td>${role}</td>
                        <td>${server}</td>
                        <td>
                            <button onclick="showAdminInfo('${adminId}', '${admin.server_id || 'all'}')" class="command-button small">Info</button>
                            ${admin.server_id ? `<button onclick="showRemoveAdminModal('${adminId}', '${name}', '${admin.server_id}')" class="command-button small danger">Remove</button>` : ''}
                        </td>
                    </tr>`;
                });
                
                html += "</tbody></table>";
                resultsDiv.innerHTML = html;
            }
        })
        .catch(err => {
            resultsDiv.innerHTML = "<p class='error'>Error: " + err.message + "</p>";
        });
}