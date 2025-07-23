function toggleKabobMenu(id) {
    console.log('toggleKabobMenu called with id:', id);
    document.querySelectorAll('.kabob-menu').forEach(menu => menu.classList.add('hidden'));
    const container = document.getElementById(`kabob-${id}`);
    if (container) {
        const menu = container.querySelector('.kabob-menu');
        if (menu) {
            menu.classList.toggle('hidden');
            console.log('Toggled kabob menu for id:', id);
        } else {
            console.error('Kabob menu not found in container:', id);
        }
    } else {
        console.error('Kabob container not found:', id);
    }
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

function submitSyncAdmins() {
    document.getElementById("sync-admins-form").submit();
}

function submitSyncDevices(serverId = "") {
    document.getElementById("sync-devices-form").submit();
}

function openLookupModal() {
    console.log('openLookupModal called');
    const modal = document.getElementById("lookup-modal");
    if (!modal) {
        console.error('lookup-modal element not found');
        return;
    }
    modal.classList.remove("hidden");
    // Force the modal to be visible
    modal.style.display = 'flex';
    modal.style.zIndex = '2000';
    document.getElementById("lookup-identifier").value = "";
    document.getElementById("lookup-results").textContent = "";
    console.log('Lookup modal should now be visible');
    console.log('Modal classes:', modal.className);
    console.log('Modal style display:', modal.style.display);
}

function hideLookupModal() {
    document.getElementById("lookup-modal").classList.add("hidden");
}

function hideSitesModal() {
    document.getElementById("sites-modal").classList.add("hidden");
}

function showSitesModal(serverName, sites) {
    console.log('showSitesModal called with serverName:', serverName, 'sites:', sites);
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

function submitDeviceLookup(event) {
    event.preventDefault();  // prevent page reload
    console.log('submitDeviceLookup called');

    const input = document.getElementById("lookup-identifier");
    const identifier = input.value.trim();
    console.log('Looking up identifier:', identifier);

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
Site Description: ${data.site_desc || 'N/A'}
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
    console.log('showAddServerModal called');
    document.getElementById("addServerModal").classList.remove("hidden");
}

function hideAddServerModal() {
    console.log('hideAddServerModal called');
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
    console.log('switchTab called with:', tabName);
    
    // Hide all action areas
    document.querySelectorAll('.actions-area').forEach(area => {
        area.classList.add('hidden');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected action area
    const actionArea = document.getElementById(`actions-${tabName}`);
    if (actionArea) {
        actionArea.classList.remove('hidden');
        console.log('Showing action area:', `actions-${tabName}`);
        
        // Load data for the selected tab
        switch(tabName) {
            case 'sites':
                loadAllSites();
                break;
            case 'admins':
                loadAllAdmins();
                break;
            case 'devices':
                loadAllDevices();
                break;
            case 'alerts':
                loadAllAlerts();
                break;
        }
    } else {
        console.error('Action area not found:', `actions-${tabName}`);
    }
    
    // Add active class to selected tab
    const tab = document.getElementById(`tab-${tabName}`);
    if (tab) {
        tab.classList.add('active');
        console.log('Activated tab:', `tab-${tabName}`);
    } else {
        console.error('Tab not found:', `tab-${tabName}`);
    }
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

function loadAllSites() {
    console.log('Loading all sites...');
    const tbody = document.getElementById('sites-table-body');
    tbody.innerHTML = '<tr><td colspan="2" class="loading">Loading sites...</td></tr>';
    
    // Get all servers and fetch their sites
    fetch('/unifi/sites/all')
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch sites");
            }
            return response.json();
        })
        .then(data => {
            tbody.innerHTML = '';
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="2">No sites found.</td></tr>';
            } else {
                data.forEach(site => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${site.desc || site.name || 'N/A'}</td>
                        <td>${site.name || 'N/A'}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        })
        .catch(err => {
            console.error('Error loading sites:', err);
            tbody.innerHTML = '<tr><td colspan="2" class="error">Error loading sites: ' + err.message + '</td></tr>';
        });
}

function loadAllAdmins() {
    console.log('Loading all admins...');
    const tbody = document.getElementById('admins-table-body');
    tbody.innerHTML = '<tr><td colspan="3" class="loading">Loading admins...</td></tr>';
    
    fetch('/unifi/admins')
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch admins");
            }
            return response.json();
        })
        .then(data => {
            tbody.innerHTML = '';
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3">No admins found.</td></tr>';
            } else {
                data.forEach(admin => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${admin.name || 'Unknown'}</td>
                        <td>${admin.email || 'N/A'}</td>
                        <td>${admin.role || 'N/A'}</td>
                    `;
                    row.style.cursor = 'pointer';
                    row.onclick = () => {
                        console.log('Admin row clicked:', admin.name);
                        showAdminDetailModal(admin);
                    };
                    tbody.appendChild(row);
                });
            }
        })
        .catch(err => {
            console.error('Error loading admins:', err);
            tbody.innerHTML = '<tr><td colspan="3" class="error">Error loading admins: ' + err.message + '</td></tr>';
        });
}

function loadAllDevices() {
    console.log('Loading all devices...');
    const tbody = document.getElementById('devices-table-body');
    tbody.innerHTML = '<tr><td colspan="4" class="loading">Loading devices...</td></tr>';
    
    fetch('/unifi/devices/all')
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch devices");
            }
            return response.json();
        })
        .then(data => {
            tbody.innerHTML = '';
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No devices found.</td></tr>';
            } else {
                data.forEach(device => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${device.site_desc || 'Unknown'}</td>
                        <td>${device.name || 'Unknown'}</td>
                        <td>${device.model || 'N/A'}</td>
                        <td>${device.serial || 'N/A'}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        })
        .catch(err => {
            console.error('Error loading devices:', err);
            tbody.innerHTML = '<tr><td colspan="4" class="error">Error loading devices: ' + err.message + '</td></tr>';
        });
}

function loadAllAlerts() {
    console.log('Loading all alerts...');
    const tbody = document.getElementById('alerts-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading alerts...</td></tr>';
    
    fetch('/unifi/alerts/all')
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch alerts");
            }
            return response.json();
        })
        .then(data => {
            tbody.innerHTML = '';
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6">No alerts found.</td></tr>';
            } else {
                data.forEach(alert => {
                    const row = document.createElement('tr');
                    const archivedStatus = alert.archived ? 'Yes' : 'No';
                    const deviceInfo = alert.device_name ? `${alert.device_name} (${alert.device_model || 'N/A'})` : 'N/A';
                    
                    row.innerHTML = `
                        <td>${alert.datetime || 'N/A'}</td>
                        <td>${alert.site_name} - ${alert.site_desc}</td>
                        <td>${deviceInfo}</td>
                        <td>${alert.msg || 'N/A'}</td>
                        <td>${alert.key || 'N/A'}</td>
                        <td>${archivedStatus}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        })
        .catch(err => {
            console.error('Error loading alerts:', err);
            tbody.innerHTML = '<tr><td colspan="6" class="error">Error loading alerts: ' + err.message + '</td></tr>';
        });
}

function submitSyncAdmins() {
    console.log('Submitting sync admins form...');
    document.getElementById("sync-admins-form").submit();
}

function submitSyncAlerts() {
    console.log('Submitting sync alerts form...');
    document.getElementById("sync-alerts-form").submit();
}

// Admin detail modal functions
let currentAdmin = null;
let selectedSites = new Set();

function showAdminDetailModal(admin) {
    console.log('showAdminDetailModal called with:', admin);
    currentAdmin = admin;
    selectedSites.clear();
    
    // Update admin info
    const nameElement = document.getElementById('admin-detail-name');
    const emailElement = document.getElementById('admin-detail-email');
    const roleElement = document.getElementById('admin-role-text');
    const modalElement = document.getElementById('admin-detail-modal');
    const revokeSuperBtn = document.getElementById('revoke-super-admin-btn');
    
    if (!nameElement || !emailElement || !roleElement || !modalElement) {
        console.error('Required modal elements not found:', {
            nameElement: !!nameElement,
            emailElement: !!emailElement,
            roleElement: !!roleElement,
            modalElement: !!modalElement
        });
        return;
    }
    
    nameElement.textContent = admin.name || 'Unknown';
    emailElement.textContent = admin.email || 'N/A';
    
    // Update role display
    const isSuperAdmin = admin.is_super === 'true' || admin.role === 'Super Administrator';
    roleElement.textContent = admin.role || 'Unknown';
    
    // Show/hide revoke super admin button
    if (revokeSuperBtn) {
        if (isSuperAdmin) {
            revokeSuperBtn.style.display = 'inline-block';
        } else {
            revokeSuperBtn.style.display = 'none';
        }
    }
    
    // Load sites data
    loadAdminSites(admin);
    
    // Show modal
    modalElement.classList.remove('hidden');
    console.log('Modal should now be visible');
    console.log('Modal element classes:', modalElement.className);
    console.log('Modal element style:', modalElement.style.display);
    
    // Force the modal to be visible
    modalElement.style.display = 'flex';
    modalElement.style.zIndex = '2000';
    console.log('Modal forced to be visible');
}

function hideAdminDetailModal() {
    document.getElementById('admin-detail-modal').classList.add('hidden');
    currentAdmin = null;
    selectedSites.clear();
}

function loadAdminSites(admin) {
    console.log('loadAdminSites called for admin:', admin.name);
    const tbody = document.getElementById('admin-sites-table-body');
    if (!tbody) {
        console.error('admin-sites-table-body not found');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading sites...</td></tr>';
    
    // Fetch all sites and admin permissions
    Promise.all([
        fetch('/unifi/sites/all').then(r => r.json()),
        fetch('/unifi/admins').then(r => r.json())
    ])
    .then(([sites, admins]) => {
        console.log('Fetched sites:', sites.length, 'admins:', admins.length);
        const adminData = admins.find(a => a.name === admin.name);
        console.log('Found admin data:', adminData);
        
        tbody.innerHTML = '';
        
        const isSuperAdmin = admin.is_super === 'true' || admin.role === 'Super Administrator';
        
        sites.forEach(site => {
            const row = document.createElement('tr');
            const hasAccess = adminData && adminData.site_permissions && 
                             adminData.site_permissions.some(p => p.site_name === site.name);
            const currentRole = hasAccess ? 'Admin' : 'None';
            
            // Disable checkboxes for super admins
            const checkboxDisabled = isSuperAdmin ? 'disabled' : '';
            const checkboxClass = isSuperAdmin ? 'site-checkbox disabled' : 'site-checkbox';
            
            row.innerHTML = `
                <td>
                    <input type="checkbox" class="${checkboxClass}" data-site="${site.name}" 
                           onchange="toggleSiteSelection('${site.name}')" ${checkboxDisabled}>
                </td>
                <td>${site.name || 'N/A'}</td>
                <td>${site.desc || 'N/A'}</td>
                <td>${site.server || 'N/A'}</td>
                <td>${currentRole}</td>
            `;
            tbody.appendChild(row);
        });
        console.log('Sites table populated with', sites.length, 'rows');
    })
    .catch(err => {
        console.error('Error loading admin sites:', err);
        tbody.innerHTML = '<tr><td colspan="5" class="error">Error loading sites: ' + err.message + '</td></tr>';
    });
}

function toggleSiteSelection(siteName) {
    if (selectedSites.has(siteName)) {
        selectedSites.delete(siteName);
    } else {
        selectedSites.add(siteName);
    }
    updateSelectAllCheckbox();
}

function toggleAllSites() {
    const selectAllCheckbox = document.getElementById('select-all-sites');
    const siteCheckboxes = document.querySelectorAll('.site-checkbox');
    
    siteCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        if (selectAllCheckbox.checked) {
            selectedSites.add(checkbox.dataset.site);
        } else {
            selectedSites.delete(checkbox.dataset.site);
        }
    });
}

function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-sites');
    const siteCheckboxes = document.querySelectorAll('.site-checkbox');
    const checkedCount = siteCheckboxes.length;
    const selectedCount = selectedSites.size;
    
    selectAllCheckbox.checked = selectedCount === checkedCount && checkedCount > 0;
    selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < checkedCount;
}

function revokeSelectedSites() {
    if (selectedSites.size === 0) {
        alert('Please select at least one site to revoke access from.');
        return;
    }
    
    if (confirm(`Are you sure you want to revoke access to ${selectedSites.size} site(s) for ${currentAdmin.name}?`)) {
        const siteNames = Array.from(selectedSites);
        
        fetch('/unifi/admin/revoke', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                admin_id: currentAdmin.id,
                site_names: siteNames
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                const successCount = Object.values(data.results).filter(Boolean).length;
                alert(`Successfully revoked access from ${successCount} out of ${siteNames.length} sites.`);
                // Refresh the admin data
                loadAdminSites(currentAdmin);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error revoking access: ' + error.message);
        });
    }
}

function addSelectedSites() {
    if (selectedSites.size === 0) {
        alert('Please select at least one site to add access to.');
        return;
    }
    
    const siteNames = Array.from(selectedSites);
    
    fetch('/unifi/admin/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            admin_id: currentAdmin.id,
            site_names: siteNames,
            role: 'admin'  // Default to admin role
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            const successCount = Object.values(data.results).filter(Boolean).length;
            alert(`Successfully added access to ${successCount} out of ${siteNames.length} sites.`);
            // Refresh the admin data
            loadAdminSites(currentAdmin);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding access: ' + error.message);
    });
}

function modifySelectedSites() {
    if (selectedSites.size === 0) {
        alert('Please select at least one site to modify access for.');
        return;
    }
    
    // Show role modification modal
    document.getElementById('role-modify-modal').classList.remove('hidden');
}

function hideRoleModifyModal() {
    document.getElementById('role-modify-modal').classList.add('hidden');
}

function applyRoleChange() {
    const selectedRole = document.querySelector('input[name="new-role"]:checked').value;
    const siteNames = Array.from(selectedSites);
    
    fetch('/unifi/admin/modify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            admin_id: currentAdmin.id,
            site_names: siteNames,
            role: selectedRole
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            const successCount = Object.values(data.results).filter(Boolean).length;
            alert(`Successfully modified role to '${selectedRole}' on ${successCount} out of ${siteNames.length} sites.`);
            // Refresh the admin data
            loadAdminSites(currentAdmin);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error modifying role: ' + error.message);
    });
    
    hideRoleModifyModal();
}

function showRevokeSuperAdminConfirm() {
    if (!currentAdmin) {
        alert('No admin selected');
        return;
    }
    
    const modal = document.getElementById('revoke-super-admin-modal');
    const adminNameElement = document.getElementById('revoke-admin-name');
    
    if (adminNameElement) {
        adminNameElement.textContent = currentAdmin.name || 'Unknown';
    }
    
    modal.classList.remove('hidden');
}

function hideRevokeSuperAdminConfirm() {
    document.getElementById('revoke-super-admin-modal').classList.add('hidden');
}

function confirmRevokeSuperAdmin() {
    if (!currentAdmin) {
        alert('No admin selected');
        return;
    }
    
    console.log('Revoking super admin status from:', currentAdmin.name);
    
    fetch('/unifi/admin/revoke-super', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            admin_id: currentAdmin.id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Super admin status revoked successfully');
            
            // Update the admin's role in the modal
            const roleElement = document.getElementById('admin-role-text');
            if (roleElement) {
                roleElement.textContent = 'Site Administrator'; // Default role after revoking super admin
            }
            
            // Hide the revoke super admin button
            const revokeSuperBtn = document.getElementById('revoke-super-admin-btn');
            if (revokeSuperBtn) {
                revokeSuperBtn.style.display = 'none';
            }
            
            // Re-enable site selection checkboxes
            const checkboxes = document.querySelectorAll('.site-checkbox.disabled');
            checkboxes.forEach(checkbox => {
                checkbox.disabled = false;
                checkbox.classList.remove('disabled');
            });
            
            // Update the select all checkbox
            updateSelectAllCheckbox();
            
            hideRevokeSuperAdminConfirm();
        } else {
            alert('Error: ' + (data.error || 'Failed to revoke super admin status'));
        }
    })
    .catch(err => {
        console.error('Error revoking super admin:', err);
        alert('Error: ' + err.message);
    });
}

