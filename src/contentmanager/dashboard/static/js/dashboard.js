/**
 * AI Content Manager Dashboard
 * Cinema Control Room Interface
 */

// ============================================================================
// State Management
// ============================================================================

const state = {
    currentView: 'dashboard',
    projects: [],
    characters: [],
    backgrounds: [],
    music: [],
    selectedProject: null,
    isLoading: false
};

// ============================================================================
// API Service
// ============================================================================

const API = {
    baseUrl: '/api/video',

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Health check
    async checkHealth() {
        try {
            const response = await fetch('/health');
            return response.ok;
        } catch {
            return false;
        }
    },

    // Projects
    async getProjects(status = null) {
        const params = status ? `?status=${status}` : '';
        return this.request(`/projects${params}`);
    },

    async getProject(id) {
        return this.request(`/projects/${id}`);
    },

    async createProject(data) {
        return this.request('/projects', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async deleteProject(id) {
        return this.request(`/projects/${id}`, { method: 'DELETE' });
    },

    async approveProject(id) {
        return this.request(`/projects/${id}/approve`, { method: 'POST' });
    },

    async rejectProject(id, notes) {
        return this.request(`/projects/${id}/reject`, {
            method: 'POST',
            body: JSON.stringify({ notes })
        });
    },

    async regenerateScript(id) {
        return this.request(`/projects/${id}/regenerate`, { method: 'POST' });
    },

    async renderProject(id) {
        return this.request(`/projects/${id}/render`, { method: 'POST' });
    },

    // Characters
    async getCharacters() {
        return this.request('/characters');
    },

    async createCharacter(name, role) {
        return this.request(`/characters?name=${encodeURIComponent(name)}&role=${encodeURIComponent(role)}`, {
            method: 'POST'
        });
    },

    async uploadCharacterAsset(characterId, pose, file) {
        const formData = new FormData();
        formData.append('file', file);

        return fetch(`${this.baseUrl}/characters/${characterId}/assets?pose=${encodeURIComponent(pose)}`, {
            method: 'POST',
            body: formData
        }).then(r => r.json());
    },

    // Backgrounds
    async getBackgrounds() {
        return this.request('/backgrounds');
    },

    async uploadBackground(name, file, contextStyle = null) {
        const formData = new FormData();
        formData.append('file', file);

        let url = `${this.baseUrl}/backgrounds?name=${encodeURIComponent(name)}`;
        if (contextStyle) url += `&context_style=${contextStyle}`;

        return fetch(url, {
            method: 'POST',
            body: formData
        }).then(r => r.json());
    },

    async deleteBackground(id) {
        return this.request(`/backgrounds/${id}`, { method: 'DELETE' });
    },

    // Music
    async getMusic() {
        return this.request('/music');
    },

    async uploadMusic(name, file, contextStyle = null) {
        const formData = new FormData();
        formData.append('file', file);

        let url = `${this.baseUrl}/music?name=${encodeURIComponent(name)}`;
        if (contextStyle) url += `&context_style=${contextStyle}`;

        return fetch(url, {
            method: 'POST',
            body: formData
        }).then(r => r.json());
    },

    async deleteMusic(id) {
        return this.request(`/music/${id}`, { method: 'DELETE' });
    }
};

// ============================================================================
// UI Utilities
// ============================================================================

const UI = {
    // Show toast notification
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/></svg>',
            error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;

        container.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    },

    // Show/hide modal
    showModal(title, content) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = content;
        document.getElementById('modal-overlay').classList.add('active');
    },

    hideModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    },

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    },

    // Format duration
    formatDuration(seconds) {
        if (!seconds) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    // Set loading state
    setLoading(isLoading) {
        state.isLoading = isLoading;
        // Could add global loading indicator here
    }
};

// ============================================================================
// View Controllers
// ============================================================================

const Views = {
    // Switch to a view
    switchTo(viewName, params = {}) {
        state.currentView = viewName;

        // Update nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            projects: 'Video Projects',
            create: 'New Project',
            characters: 'Characters',
            backgrounds: 'Backgrounds',
            music: 'Music Library',
            'project-detail': 'Project Details'
        };
        document.getElementById('page-title').textContent = titles[viewName] || 'Dashboard';

        // Show correct view
        document.querySelectorAll('.view').forEach(view => {
            view.classList.toggle('active', view.id === `view-${viewName}`);
        });

        // Load view data
        this.loadViewData(viewName, params);
    },

    async loadViewData(viewName, params) {
        try {
            switch (viewName) {
                case 'dashboard':
                    await this.loadDashboard();
                    break;
                case 'projects':
                    await this.loadProjects();
                    break;
                case 'create':
                    await this.loadCreateForm();
                    break;
                case 'characters':
                    await this.loadCharacters();
                    break;
                case 'backgrounds':
                    await this.loadBackgrounds();
                    break;
                case 'music':
                    await this.loadMusic();
                    break;
                case 'project-detail':
                    await this.loadProjectDetail(params.projectId);
                    break;
            }
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    // Dashboard
    async loadDashboard() {
        const [projects, characters, backgrounds, music] = await Promise.all([
            API.getProjects(),
            API.getCharacters(),
            API.getBackgrounds(),
            API.getMusic()
        ]);

        state.projects = projects;
        state.characters = characters;
        state.backgrounds = backgrounds;
        state.music = music;

        // Update stats
        const statCounts = {
            draft: 0,
            pending: 0,
            rendering: 0,
            completed: 0
        };

        projects.forEach(p => {
            if (p.status === 'draft') statCounts.draft++;
            else if (p.status === 'approved' || p.status === 'audio_ready') statCounts.pending++;
            else if (p.status === 'rendering') statCounts.rendering++;
            else if (p.status === 'completed') statCounts.completed++;
        });

        document.getElementById('stat-draft').textContent = statCounts.draft;
        document.getElementById('stat-pending').textContent = statCounts.pending;
        document.getElementById('stat-rendering').textContent = statCounts.rendering;
        document.getElementById('stat-completed').textContent = statCounts.completed;

        // Update asset counts
        document.getElementById('asset-characters').textContent = characters.length;
        document.getElementById('asset-backgrounds').textContent = backgrounds.length;
        document.getElementById('asset-music').textContent = music.length;

        // Update projects badge
        document.getElementById('projects-count').textContent = projects.length;

        // Render recent projects
        this.renderRecentProjects(projects.slice(0, 5));
    },

    renderRecentProjects(projects) {
        const container = document.getElementById('recent-projects');

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <rect x="2" y="2" width="20" height="20" rx="2"/>
                            <path d="M10 8l4 4-4 4"/>
                        </svg>
                    </div>
                    <p>No projects yet</p>
                    <button class="btn btn-primary btn-sm" data-view="create">Create First Project</button>
                </div>
            `;
            return;
        }

        container.innerHTML = projects.map(project => `
            <div class="project-item" data-project-id="${project.id}">
                <div class="project-thumbnail">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="23,7 16,12 23,17 23,7"/>
                        <rect x="1" y="5" width="15" height="14" rx="2"/>
                    </svg>
                </div>
                <div class="project-info">
                    <div class="project-name">${this.escapeHtml(project.title)}</div>
                    <div class="project-meta">${this.escapeHtml(project.topic.substring(0, 50))}${project.topic.length > 50 ? '...' : ''}</div>
                </div>
                <span class="project-status ${project.status}">${project.status.replace('_', ' ')}</span>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => {
                Views.switchTo('project-detail', { projectId: item.dataset.projectId });
            });
        });
    },

    // Projects list
    async loadProjects(statusFilter = null) {
        const projects = await API.getProjects(statusFilter);
        state.projects = projects;

        const grid = document.getElementById('projects-grid');

        if (projects.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <rect x="2" y="2" width="20" height="20" rx="2"/>
                            <path d="M10 8l4 4-4 4"/>
                        </svg>
                    </div>
                    <p>${statusFilter ? `No ${statusFilter} projects` : 'No projects yet'}</p>
                    <button class="btn btn-primary btn-sm" data-view="create">Create New Project</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = projects.map(project => `
            <div class="project-card" data-project-id="${project.id}">
                <div class="project-card-header">
                    <div>
                        <div class="project-card-title">${this.escapeHtml(project.title)}</div>
                        <div class="project-card-topic">${this.escapeHtml(project.topic)}</div>
                    </div>
                    <span class="project-status ${project.status}">${project.status.replace('_', ' ')}</span>
                </div>
                <div class="project-card-body">
                    <div class="project-card-meta">
                        <span>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2"/>
                                <line x1="16" y1="2" x2="16" y2="6"/>
                                <line x1="8" y1="2" x2="8" y2="6"/>
                                <line x1="3" y1="10" x2="21" y2="10"/>
                            </svg>
                            ${project.context_style}
                        </span>
                        ${project.duration_seconds ? `
                            <span>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <polyline points="12,6 12,12 16,14"/>
                                </svg>
                                ${UI.formatDuration(project.duration_seconds)}
                            </span>
                        ` : ''}
                    </div>
                </div>
                <div class="project-card-footer">
                    <span class="project-card-date">${UI.formatDate(project.created_at)}</span>
                    ${project.status === 'completed' ? `
                        <a href="/api/video/projects/${project.id}/download" class="btn btn-sm btn-primary" onclick="event.stopPropagation()">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7,10 12,15 17,10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Download
                        </a>
                    ` : ''}
                </div>
            </div>
        `).join('');

        // Add click handlers
        grid.querySelectorAll('.project-card').forEach(card => {
            card.addEventListener('click', () => {
                Views.switchTo('project-detail', { projectId: card.dataset.projectId });
            });
        });
    },

    // Create form
    async loadCreateForm() {
        const [characters, music] = await Promise.all([
            API.getCharacters(),
            API.getMusic()
        ]);

        state.characters = characters;
        state.music = music;

        // Populate character dropdowns
        const questioners = characters.filter(c => c.role === 'questioner' || !c.role);
        const explainers = characters.filter(c => c.role === 'explainer' || !c.role);

        document.getElementById('questioner').innerHTML = `
            <option value="">Select character...</option>
            ${questioners.map(c => `<option value="${c.id}">${this.escapeHtml(c.name)}</option>`).join('')}
        `;

        document.getElementById('explainer').innerHTML = `
            <option value="">Select character...</option>
            ${explainers.map(c => `<option value="${c.id}">${this.escapeHtml(c.name)}</option>`).join('')}
        `;

        // Populate music dropdown
        document.getElementById('background-music').innerHTML = `
            <option value="">No background music</option>
            ${music.map(m => `<option value="${m.id}">${this.escapeHtml(m.name)} (${UI.formatDuration(m.duration_seconds)})</option>`).join('')}
        `;
    },

    // Project detail
    async loadProjectDetail(projectId) {
        const project = await API.getProject(projectId);
        state.selectedProject = project;

        const container = document.getElementById('project-detail-content');

        const script = project.script_json;
        const lines = script?.lines || [];

        container.innerHTML = `
            <div class="detail-header">
                <div class="detail-info">
                    <h2>${this.escapeHtml(project.title)}</h2>
                    <p class="topic">${this.escapeHtml(project.topic)}</p>
                    <div class="detail-meta">
                        <span>Style: ${project.context_style}</span>
                        <span>Status: <span class="project-status ${project.status}">${project.status.replace('_', ' ')}</span></span>
                        ${project.duration_seconds ? `<span>Duration: ${UI.formatDuration(project.duration_seconds)}</span>` : ''}
                    </div>
                </div>
                <div class="detail-actions">
                    ${this.getProjectActions(project)}
                </div>
            </div>

            ${lines.length > 0 ? `
                <div class="script-section">
                    <div class="script-header">
                        <h3 class="script-title">Generated Script</h3>
                        <span>${lines.length} dialogue lines</span>
                    </div>
                    <div class="script-content">
                        ${lines.map(line => `
                            <div class="dialogue-line">
                                <div class="dialogue-speaker">
                                    <div class="speaker-name">${this.escapeHtml(line.speaker_name)}</div>
                                    <div class="speaker-role">${line.speaker_role}</div>
                                </div>
                                <div class="dialogue-text">${this.escapeHtml(line.line)}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : `
                <div class="script-section">
                    <div class="panel-content">
                        <div class="empty-state">
                            <p>Script not yet generated</p>
                        </div>
                    </div>
                </div>
            `}

            ${project.takeaway ? `
                <div class="takeaway-section">
                    <div class="takeaway-label">Key Takeaway</div>
                    <div class="takeaway-text">${this.escapeHtml(project.takeaway)}</div>
                </div>
            ` : ''}

            ${project.error_message ? `
                <div class="takeaway-section" style="background: rgba(255, 107, 107, 0.1); border-color: var(--status-failed);">
                    <div class="takeaway-label" style="color: var(--status-failed);">Error</div>
                    <div class="takeaway-text">${this.escapeHtml(project.error_message)}</div>
                </div>
            ` : ''}
        `;

        // Bind action buttons
        this.bindProjectActions(project);
    },

    getProjectActions(project) {
        const actions = [];

        switch (project.status) {
            case 'draft':
                actions.push(`<button class="btn btn-success" id="btn-approve">Approve Script</button>`);
                actions.push(`<button class="btn btn-secondary" id="btn-regenerate">Regenerate</button>`);
                break;
            case 'approved':
            case 'audio_ready':
                actions.push(`<button class="btn btn-primary" id="btn-render">Start Rendering</button>`);
                if (project.voiceover_path) {
                    actions.push(`<a href="/api/video/projects/${project.id}/preview-audio" class="btn btn-secondary" target="_blank">Preview Audio</a>`);
                }
                break;
            case 'completed':
                actions.push(`<a href="/api/video/projects/${project.id}/download" class="btn btn-primary">Download Video</a>`);
                break;
            case 'failed':
                actions.push(`<button class="btn btn-warning" id="btn-regenerate">Retry</button>`);
                break;
        }

        actions.push(`<button class="btn btn-secondary" id="btn-delete">Delete</button>`);

        return actions.join('');
    },

    bindProjectActions(project) {
        const approveBtn = document.getElementById('btn-approve');
        const regenerateBtn = document.getElementById('btn-regenerate');
        const renderBtn = document.getElementById('btn-render');
        const deleteBtn = document.getElementById('btn-delete');

        if (approveBtn) {
            approveBtn.addEventListener('click', async () => {
                try {
                    await API.approveProject(project.id);
                    UI.showToast('Project approved! Generating voiceover...', 'success');
                    this.loadProjectDetail(project.id);
                } catch (error) {
                    UI.showToast(error.message, 'error');
                }
            });
        }

        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', async () => {
                try {
                    await API.regenerateScript(project.id);
                    UI.showToast('Regenerating script...', 'success');
                    this.loadProjectDetail(project.id);
                } catch (error) {
                    UI.showToast(error.message, 'error');
                }
            });
        }

        if (renderBtn) {
            renderBtn.addEventListener('click', async () => {
                try {
                    await API.renderProject(project.id);
                    UI.showToast('Rendering started...', 'success');
                    this.loadProjectDetail(project.id);
                } catch (error) {
                    UI.showToast(error.message, 'error');
                }
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                if (confirm('Are you sure you want to delete this project?')) {
                    try {
                        await API.deleteProject(project.id);
                        UI.showToast('Project deleted', 'success');
                        Views.switchTo('projects');
                    } catch (error) {
                        UI.showToast(error.message, 'error');
                    }
                }
            });
        }
    },

    // Characters
    async loadCharacters() {
        const characters = await API.getCharacters();
        state.characters = characters;

        const grid = document.getElementById('characters-grid');

        if (characters.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="8" r="4"/>
                            <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
                        </svg>
                    </div>
                    <p>No characters yet</p>
                    <button class="btn btn-primary btn-sm" id="add-first-character">Add First Character</button>
                </div>
            `;

            document.getElementById('add-first-character')?.addEventListener('click', () => this.showAddCharacterModal());
            return;
        }

        grid.innerHTML = characters.map(char => `
            <div class="asset-card">
                <div class="asset-preview">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="8" r="4"/>
                        <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
                    </svg>
                </div>
                <div class="asset-info">
                    <div class="asset-name">${this.escapeHtml(char.name)}</div>
                    <div class="asset-meta">
                        <span class="project-status ${char.role}">${char.role}</span>
                    </div>
                </div>
                <div class="asset-actions">
                    <button class="btn btn-sm btn-secondary" onclick="Views.showUploadAssetModal(${char.id}, '${this.escapeHtml(char.name)}')">
                        Upload Pose
                    </button>
                </div>
            </div>
        `).join('');
    },

    showAddCharacterModal() {
        UI.showModal('Add Character', `
            <form id="add-character-form">
                <div class="form-group">
                    <label for="char-name">Character Name</label>
                    <input type="text" id="char-name" placeholder="e.g., Professor Max" required>
                </div>
                <div class="form-group">
                    <label for="char-role">Role</label>
                    <select id="char-role" required>
                        <option value="questioner">Questioner (Asks questions)</option>
                        <option value="explainer">Explainer (Provides answers)</option>
                    </select>
                </div>
                <div class="modal-footer" style="padding: 20px 0 0; margin-top: 20px; border-top: 1px solid var(--border-subtle);">
                    <button type="button" class="btn btn-secondary" onclick="UI.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Create Character</button>
                </div>
            </form>
        `);

        document.getElementById('add-character-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('char-name').value;
            const role = document.getElementById('char-role').value;

            try {
                await API.createCharacter(name, role);
                UI.hideModal();
                UI.showToast('Character created!', 'success');
                this.loadCharacters();
            } catch (error) {
                UI.showToast(error.message, 'error');
            }
        });
    },

    showUploadAssetModal(characterId, characterName) {
        UI.showModal(`Upload Pose - ${characterName}`, `
            <form id="upload-pose-form">
                <div class="form-group">
                    <label for="pose-name">Pose Name</label>
                    <input type="text" id="pose-name" placeholder="e.g., standing, thinking, pointing" required>
                </div>
                <div class="form-group">
                    <label>Image File</label>
                    <div class="upload-zone" id="pose-upload-zone">
                        <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17,8 12,3 7,8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                        <p class="upload-text">Click or drag to upload</p>
                        <p class="upload-hint">PNG or JPG, max 5MB</p>
                    </div>
                    <input type="file" id="pose-file" accept="image/png,image/jpeg" hidden>
                </div>
                <div class="modal-footer" style="padding: 20px 0 0; margin-top: 20px; border-top: 1px solid var(--border-subtle);">
                    <button type="button" class="btn btn-secondary" onclick="UI.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </div>
            </form>
        `);

        const uploadZone = document.getElementById('pose-upload-zone');
        const fileInput = document.getElementById('pose-file');

        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                uploadZone.querySelector('.upload-text').textContent = e.dataTransfer.files[0].name;
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                uploadZone.querySelector('.upload-text').textContent = fileInput.files[0].name;
            }
        });

        document.getElementById('upload-pose-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const pose = document.getElementById('pose-name').value;
            const file = fileInput.files[0];

            if (!file) {
                UI.showToast('Please select a file', 'warning');
                return;
            }

            try {
                await API.uploadCharacterAsset(characterId, pose, file);
                UI.hideModal();
                UI.showToast('Pose uploaded!', 'success');
                this.loadCharacters();
            } catch (error) {
                UI.showToast(error.message, 'error');
            }
        });
    },

    // Backgrounds
    async loadBackgrounds() {
        const backgrounds = await API.getBackgrounds();
        state.backgrounds = backgrounds;

        const grid = document.getElementById('backgrounds-grid');

        if (backgrounds.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <rect x="3" y="3" width="18" height="18" rx="2"/>
                            <circle cx="8.5" cy="8.5" r="1.5"/>
                            <polyline points="21,15 16,10 5,21"/>
                        </svg>
                    </div>
                    <p>No backgrounds yet</p>
                    <button class="btn btn-primary btn-sm" id="add-first-bg">Upload First Background</button>
                </div>
            `;

            document.getElementById('add-first-bg')?.addEventListener('click', () => this.showUploadBackgroundModal());
            return;
        }

        grid.innerHTML = backgrounds.map(bg => `
            <div class="asset-card">
                <div class="asset-preview">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21,15 16,10 5,21"/>
                    </svg>
                </div>
                <div class="asset-info">
                    <div class="asset-name">${this.escapeHtml(bg.name)}</div>
                    <div class="asset-meta">
                        ${bg.context_style ? `<span>${bg.context_style}</span>` : '<span>All styles</span>'}
                    </div>
                </div>
                <div class="asset-actions">
                    <button class="btn btn-sm btn-danger" onclick="Views.deleteBackground(${bg.id})">Delete</button>
                </div>
            </div>
        `).join('');
    },

    showUploadBackgroundModal() {
        UI.showModal('Upload Background', `
            <form id="upload-bg-form">
                <div class="form-group">
                    <label for="bg-name">Background Name</label>
                    <input type="text" id="bg-name" placeholder="e.g., Classroom, Office" required>
                </div>
                <div class="form-group">
                    <label for="bg-style">Content Style (Optional)</label>
                    <select id="bg-style">
                        <option value="">All styles</option>
                        <option value="educational">Educational</option>
                        <option value="motivation">Motivation</option>
                        <option value="finance">Finance</option>
                        <option value="tech">Tech</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Image File</label>
                    <div class="upload-zone" id="bg-upload-zone">
                        <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17,8 12,3 7,8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                        <p class="upload-text">Click or drag to upload</p>
                        <p class="upload-hint">PNG or JPG, 1080x1920 recommended</p>
                    </div>
                    <input type="file" id="bg-file" accept="image/png,image/jpeg" hidden>
                </div>
                <div class="modal-footer" style="padding: 20px 0 0; margin-top: 20px; border-top: 1px solid var(--border-subtle);">
                    <button type="button" class="btn btn-secondary" onclick="UI.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </div>
            </form>
        `);

        this.setupUploadZone('bg-upload-zone', 'bg-file');

        document.getElementById('upload-bg-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('bg-name').value;
            const style = document.getElementById('bg-style').value || null;
            const file = document.getElementById('bg-file').files[0];

            if (!file) {
                UI.showToast('Please select a file', 'warning');
                return;
            }

            try {
                await API.uploadBackground(name, file, style);
                UI.hideModal();
                UI.showToast('Background uploaded!', 'success');
                this.loadBackgrounds();
            } catch (error) {
                UI.showToast(error.message, 'error');
            }
        });
    },

    async deleteBackground(id) {
        if (confirm('Delete this background?')) {
            try {
                await API.deleteBackground(id);
                UI.showToast('Background deleted', 'success');
                this.loadBackgrounds();
            } catch (error) {
                UI.showToast(error.message, 'error');
            }
        }
    },

    // Music
    async loadMusic() {
        const music = await API.getMusic();
        state.music = music;

        const grid = document.getElementById('music-grid');

        if (music.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M9 18V5l12-2v13"/>
                            <circle cx="6" cy="18" r="3"/>
                            <circle cx="18" cy="16" r="3"/>
                        </svg>
                    </div>
                    <p>No music tracks yet</p>
                    <button class="btn btn-primary btn-sm" id="add-first-music">Upload First Track</button>
                </div>
            `;

            document.getElementById('add-first-music')?.addEventListener('click', () => this.showUploadMusicModal());
            return;
        }

        grid.innerHTML = music.map(track => `
            <div class="asset-card">
                <div class="asset-preview">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M9 18V5l12-2v13"/>
                        <circle cx="6" cy="18" r="3"/>
                        <circle cx="18" cy="16" r="3"/>
                    </svg>
                </div>
                <div class="asset-info">
                    <div class="asset-name">${this.escapeHtml(track.name)}</div>
                    <div class="asset-meta">
                        <span>${UI.formatDuration(track.duration_seconds)}</span>
                    </div>
                </div>
                <div class="asset-actions">
                    <button class="btn btn-sm btn-danger" onclick="Views.deleteMusic(${track.id})">Delete</button>
                </div>
            </div>
        `).join('');
    },

    showUploadMusicModal() {
        UI.showModal('Upload Music Track', `
            <form id="upload-music-form">
                <div class="form-group">
                    <label for="music-name">Track Name</label>
                    <input type="text" id="music-name" placeholder="e.g., Upbeat Background" required>
                </div>
                <div class="form-group">
                    <label for="music-style">Content Style (Optional)</label>
                    <select id="music-style">
                        <option value="">All styles</option>
                        <option value="educational">Educational</option>
                        <option value="motivation">Motivation</option>
                        <option value="finance">Finance</option>
                        <option value="tech">Tech</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Audio File</label>
                    <div class="upload-zone" id="music-upload-zone">
                        <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17,8 12,3 7,8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                        <p class="upload-text">Click or drag to upload</p>
                        <p class="upload-hint">MP3 or WAV, max 20MB</p>
                    </div>
                    <input type="file" id="music-file" accept="audio/mpeg,audio/wav" hidden>
                </div>
                <div class="modal-footer" style="padding: 20px 0 0; margin-top: 20px; border-top: 1px solid var(--border-subtle);">
                    <button type="button" class="btn btn-secondary" onclick="UI.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </div>
            </form>
        `);

        this.setupUploadZone('music-upload-zone', 'music-file');

        document.getElementById('upload-music-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('music-name').value;
            const style = document.getElementById('music-style').value || null;
            const file = document.getElementById('music-file').files[0];

            if (!file) {
                UI.showToast('Please select a file', 'warning');
                return;
            }

            try {
                await API.uploadMusic(name, file, style);
                UI.hideModal();
                UI.showToast('Music track uploaded!', 'success');
                this.loadMusic();
            } catch (error) {
                UI.showToast(error.message, 'error');
            }
        });
    },

    async deleteMusic(id) {
        if (confirm('Delete this music track?')) {
            try {
                await API.deleteMusic(id);
                UI.showToast('Music track deleted', 'success');
                this.loadMusic();
            } catch (error) {
                UI.showToast(error.message, 'error');
            }
        }
    },

    // Utility: Setup upload zone
    setupUploadZone(zoneId, inputId) {
        const zone = document.getElementById(zoneId);
        const input = document.getElementById(inputId);

        zone.addEventListener('click', () => input.click());
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                zone.querySelector('.upload-text').textContent = e.dataTransfer.files[0].name;
            }
        });

        input.addEventListener('change', () => {
            if (input.files.length) {
                zone.querySelector('.upload-text').textContent = input.files[0].name;
            }
        });
    },

    // Utility: Escape HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// ============================================================================
// Event Handlers
// ============================================================================

function initializeEventHandlers() {
    // Navigation clicks
    document.querySelectorAll('[data-view]').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            Views.switchTo(el.dataset.view);
        });
    });

    // Refresh button
    document.getElementById('refresh-btn')?.addEventListener('click', () => {
        Views.loadViewData(state.currentView, {});
        UI.showToast('Refreshed', 'success');
    });

    // Status filter
    document.getElementById('status-filter')?.addEventListener('change', (e) => {
        Views.loadProjects(e.target.value || null);
    });

    // Create project form
    document.getElementById('create-project-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = {
            title: formData.get('title'),
            topic: formData.get('topic'),
            context_style: formData.get('context_style'),
            questioner_id: parseInt(formData.get('questioner_id')),
            explainer_id: parseInt(formData.get('explainer_id')),
            background_music_id: formData.get('background_music_id') ? parseInt(formData.get('background_music_id')) : null
        };

        if (!data.questioner_id || !data.explainer_id) {
            UI.showToast('Please select both characters', 'warning');
            return;
        }

        try {
            const project = await API.createProject(data);
            UI.showToast('Project created! Generating script...', 'success');
            Views.switchTo('project-detail', { projectId: project.id });
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    });

    // Add character button
    document.getElementById('add-character-btn')?.addEventListener('click', () => {
        Views.showAddCharacterModal();
    });

    // Add background button
    document.getElementById('add-background-btn')?.addEventListener('click', () => {
        Views.showUploadBackgroundModal();
    });

    // Add music button
    document.getElementById('add-music-btn')?.addEventListener('click', () => {
        Views.showUploadMusicModal();
    });

    // Modal close
    document.getElementById('modal-close')?.addEventListener('click', UI.hideModal);
    document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
        if (e.target === e.currentTarget) UI.hideModal();
    });

    // Escape key closes modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') UI.hideModal();
    });
}

// ============================================================================
// API Status Check
// ============================================================================

async function checkAPIStatus() {
    const indicator = document.getElementById('api-status');
    const isHealthy = await API.checkHealth();

    indicator.classList.remove('connected', 'error');
    indicator.classList.add(isHealthy ? 'connected' : 'error');
}

// ============================================================================
// Initialize App
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventHandlers();
    checkAPIStatus();
    setInterval(checkAPIStatus, 30000); // Check every 30s

    // Load initial view
    Views.switchTo('dashboard');
});
