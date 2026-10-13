/* Synthalingua control panel (main.html).
   Plain static JS, no build step, no external URLs.
   Binds every control to a CONTRACT v1 settings key and drives the
   /api/settings, /api/run/*, /api/models/available, /api/microphones and
   /api/preview/namespace routes. */
(function () {
    'use strict';

    var MODES = ['captions', 'hls', 'mic'];
    var state = {
        mode: 'captions',
        settings: {},
        accepted: false,
        runState: 'idle',
        logNext: 0,
        logLines: [],
        socket: null,
        socketLive: false,
        saveTimer: null,
        statusTimer: null,
        logTimer: null,
        videoSession: null,
        elapsedBase: null
    };

    function byId(id) { return document.getElementById(id); }

    function api(path, options) {
        var opts = options || {};
        var init = { method: opts.method || 'GET', headers: {} };
        if (opts.body !== undefined) {
            init.headers['Content-Type'] = 'application/json';
            init.body = JSON.stringify(opts.body);
        }
        return fetch(path, init).then(function (response) {
            return response.json().catch(function () { return {}; }).then(function (data) {
                data = data || {};
                if (!response.ok) {
                    var message = data.error || ('HTTP ' + response.status);
                    var error = new Error(message);
                    error.status = response.status;
                    error.data = data;
                    throw error;
                }
                return data;
            });
        });
    }

    function note(text, kind) {
        var line = byId('run-message');
        if (!line) { return; }
        line.textContent = text || '';
        line.className = 'status-line' + (kind ? ' ' + kind : '');
    }

    function isHidden(el) {
        if (!el) { return true; }
        if (el.offsetParent === null && el.tagName !== 'OPTION') { return true; }
        var panel = el.closest ? el.closest('.tab-panel') : null;
        if (panel && panel.classList.contains('hidden')) { return true; }
        var gated = el.closest ? el.closest('[data-modes]') : null;
        if (gated) {
            var modes = (gated.getAttribute('data-modes') || '').split(/\s+/);
            if (modes.indexOf(state.mode) === -1) { return true; }
        }
        return false;
    }

    // ---------------------------------------------------------------- values
    function readValue(el, type) {
        if (el.type === 'checkbox') { return el.checked; }
        var raw = (el.value === null || el.value === undefined) ? '' : String(el.value);
        if (type === 'int' || type === 'int-null') {
            if (raw.trim() === '') { return type === 'int' ? 0 : null; }
            var n = parseInt(raw, 10);
            return isNaN(n) ? (type === 'int' ? 0 : null) : n;
        }
        if (type === 'float' || type === 'float-null') {
            if (raw.trim() === '') { return type === 'float' ? 0 : null; }
            var f = parseFloat(raw);
            return isNaN(f) ? (type === 'float' ? 0 : null) : f;
        }
        if (type === 'bool') { return !!el.checked; }
        var trimmed = raw.trim();
        return trimmed === '' ? (type === 'str-null' ? null : '') : trimmed;
    }

    function writeValue(el, type, value) {
        if (el.type === 'checkbox') {
            el.checked = !!value;
            return;
        }
        if (value === null || value === undefined) {
            el.value = (type === 'bool') ? '' : '';
            return;
        }
        el.value = String(value);
    }

    function keyedElements() {
        return Array.prototype.slice.call(document.querySelectorAll('[data-key]'));
    }

    function collectPatch() {
        var patch = {};
        keyedElements().forEach(function (el) {
            if (isHidden(el)) { return; }
            var key = el.getAttribute('data-key');
            var type = el.getAttribute('data-type') || 'str';
            patch[key] = readValue(el, type);
        });
        patch.mode = state.mode;
        patch.microphone_enabled = (state.mode === 'mic') ? true : null;

        var compare = byId('captions-compare');
        patch.makecaptions = (compare && compare.checked) ? 'compare' : true;

        var selectsource = byId('hls-selectsource');
        patch.selectsource = (selectsource && selectsource.checked) ? 'interactive' : null;

        patch.subtype = readChecked('subtype');
        patch.substyle = buildSubstyle();

        var batch = readChecked('batch-mode') || 'none';
        patch.adaptive_batch = (batch === 'auto');
        if (batch !== 'manual') {
            patch.batchmode = 1;
        }
        return patch;
    }

    function readChecked(name) {
        var el = document.querySelector('input[name="' + name + '"]:checked');
        return el ? el.value : null;
    }

    function setChecked(name, value) {
        var list = document.querySelectorAll('input[name="' + name + '"]');
        Array.prototype.forEach.call(list, function (el) {
            el.checked = (el.value === (value === null || value === undefined ? '' : String(value)));
        });
    }

    function buildSubstyle() {
        var subtype = readChecked('subtype');
        if (subtype !== 'burn') { return null; }
        var font = (byId('substyle-font').value || '').trim();
        var size = (byId('substyle-size').value || '').trim();
        var color = (byId('substyle-color').value || '').trim();
        var parts = [];
        if (font) { parts.push(font); }
        parts.push(size || '24');
        parts.push(color || 'yellow');
        return parts.join(',');
    }

    function applySubstyle(value) {
        var text = (value || '').trim();
        var parts = text ? text.split(',') : [];
        var font = '';
        var size = '24';
        var color = 'yellow';
        if (parts.length >= 3) { font = parts[0].trim(); size = parts[1].trim(); color = parts[2].trim(); }
        else if (parts.length === 2) { size = parts[0].trim(); color = parts[1].trim(); }
        else if (parts.length === 1 && parts[0].trim()) { color = parts[0].trim(); }
        if (byId('substyle-font')) { byId('substyle-font').value = font; }
        if (byId('substyle-size')) { byId('substyle-size').value = size || '24'; }
        if (byId('substyle-color')) { byId('substyle-color').value = color || 'yellow'; }
    }

    function applySettings(settings) {
        state.settings = settings || {};
        keyedElements().forEach(function (el) {
            var key = el.getAttribute('data-key');
            var type = el.getAttribute('data-type') || 'str';
            if (!(key in state.settings)) { return; }
            writeValue(el, type, state.settings[key]);
        });
        if (byId('captions-compare')) { byId('captions-compare').checked = (state.settings.makecaptions === 'compare'); }
        if (byId('hls-selectsource')) { byId('hls-selectsource').checked = !!state.settings.selectsource; }
        setChecked('subtype', state.settings.subtype || '');
        applySubstyle(state.settings.substyle);
        var batch = 'none';
        if (state.settings.adaptive_batch) { batch = 'auto'; }
        else if (state.settings.batchmode && parseInt(state.settings.batchmode, 10) > 1) { batch = 'manual'; }
        setChecked('batch-mode', batch);
        if (byId('mic-enabled')) { byId('mic-enabled').checked = !!state.settings.microphone_enabled || state.settings.mode === 'mic'; }
        var lastTab = state.settings.ui_last_tab;
        if (MODES.indexOf(lastTab) !== -1) { switchTab(lastTab, true); }
        else { switchTab(state.settings.mode || 'captions', true); }
        applyModeVisibility();
    }

    // Mirrors: the HLS and microphone panels carry the same web server keys.
    // Copy the visible value onto the hidden twins before switching panels.
    function syncMirrors() {
        var values = {};
        keyedElements().forEach(function (el) {
            if (isHidden(el)) { return; }
            values[el.getAttribute('data-key')] = el.value;
        });
        keyedElements().forEach(function (el) {
            var key = el.getAttribute('data-key');
            if (key in values && el.value !== values[key]) { el.value = values[key]; }
        });
    }

    function applyModeVisibility() {
        Array.prototype.forEach.call(document.querySelectorAll('[data-modes]'), function (el) {
            var modes = (el.getAttribute('data-modes') || '').split(/\s+/);
            el.classList.toggle('hidden', modes.indexOf(state.mode) === -1);
        });
    }

    function switchTab(mode, silent) {
        if (MODES.indexOf(mode) === -1) { return; }
        if (!silent) { syncMirrors(); }
        state.mode = mode;
        Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (tab) {
            var active = tab.getAttribute('data-mode') === mode;
            tab.classList.toggle('active', active);
            tab.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        Array.prototype.forEach.call(document.querySelectorAll('.tab-panel'), function (panel) {
            panel.classList.toggle('hidden', panel.getAttribute('data-panel') !== mode);
        });
        applyModeVisibility();
        if (!silent) { scheduleSave(); }
    }

    // ---------------------------------------------------------------- saving
    function scheduleSave() {
        if (state.saveTimer) { clearTimeout(state.saveTimer); }
        state.saveTimer = setTimeout(function () { saveSettings(true); }, 700);
    }

    function saveSettings(quiet) {
        var patch = collectPatch();
        return api('/api/settings', { method: 'POST', body: patch }).then(function (data) {
            state.settings = data.settings || state.settings;
            if (!quiet) { note('Settings saved.', 'ok'); }
            return data;
        }).catch(function (error) {
            note('Could not save settings: ' + error.message, 'bad');
            throw error;
        });
    }

    // ---------------------------------------------------------------- models
    function refreshModels() {
        return api('/api/models/available').then(function (data) {
            var lists = {
                whisper: data.whisper || [],
                fasterwhisper: data.fasterwhisper || [],
                openvino: data.openvino || [],
                demucs: data.demucs || []
            };
            var select = byId('demucs_model');
            if (select) {
                var current = select.value || state.settings.demucs_model || 'DEFAULT';
                select.innerHTML = '';
                var fallback = document.createElement('option');
                fallback.value = 'DEFAULT';
                fallback.textContent = 'App default';
                select.appendChild(fallback);
                lists.demucs.forEach(function (name) {
                    var option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    select.appendChild(option);
                });
                if (!lists.demucs.length) {
                    ['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q', 'hdemucs', 'demucs'].forEach(function (name) {
                        var option = document.createElement('option');
                        option.value = name;
                        option.textContent = name;
                        select.appendChild(option);
                    });
                }
                if (current && current !== 'DEFAULT') { select.value = current; }
                if (select.value !== current) { select.value = 'DEFAULT'; }
            }
            var listing = byId('model-listing');
            if (listing) {
                var parts = [];
                ['whisper', 'fasterwhisper', 'openvino', 'demucs'].forEach(function (family) {
                    parts.push(family + ': ' + (lists[family].length ? lists[family].join(', ') : 'none found'));
                });
                parts.push('folder: ' + (data.model_dir || 'unknown'));
                listing.textContent = parts.join(' | ');
            }
            return lists;
        }).catch(function (error) {
            var listing = byId('model-listing');
            if (listing) { listing.textContent = 'Model list unavailable: ' + error.message; }
            return null;
        });
    }

    function refreshMicrophones() {
        return api('/api/microphones').then(function (data) {
            var select = byId('set_microphone');
            if (!select) { return; }
            var current = select.value;
            select.innerHTML = '';
            var auto = document.createElement('option');
            auto.value = '';
            auto.textContent = 'System default';
            select.appendChild(auto);
            (data.devices || []).forEach(function (device) {
                var option = document.createElement('option');
                option.value = String(device.index);
                option.textContent = device.index + ': ' + device.name;
                select.appendChild(option);
            });
            if (current !== '' && current !== null && current !== undefined) { select.value = current; }
            else if (data.default_index !== null && data.default_index !== undefined) { select.value = String(data.default_index); }
        }).catch(function (error) {
            note('Microphone list unavailable: ' + error.message, 'bad');
        });
    }

    function refreshLanguages() {
        return api('/api/languages').then(function (data) {
            var list = byId('language-options');
            if (!list) { return; }
            list.innerHTML = '';
            (data.values || data.languages || []).forEach(function (value) {
                var option = document.createElement('option');
                option.value = typeof value === 'string' ? value : (value.code || '');
                option.label = typeof value === 'string' ? value : (value.name || '');
                list.appendChild(option);
            });
        }).catch(function () { /* free text entry still works */ });
    }

    function refreshBlocklist() {
        return api('/api/blocklist').then(function (data) {
            var box = byId('blocklist-listing');
            if (!box) { return; }
            var words = data.words || [];
            box.textContent = words.length ? (words.length + ' entries from ' + (data.path || 'the default list') + ': ' + words.slice(0, 20).join(', ')) : 'No blocklist loaded.';
        }).catch(function () { /* optional */ });
    }

    // ---------------------------------------------------------------- run
    function setRunState(status) {
        state.runState = status.state || 'idle';
        var pill = byId('run-pill');
        if (pill) {
            pill.textContent = state.runState;
            pill.className = 'pill ' + state.runState;
        }
        var start = byId('btn-start');
        var stop = byId('btn-stop');
        var running = (state.runState === 'starting' || state.runState === 'running' || state.runState === 'stopping');
        if (start) { start.disabled = running || !state.accepted; }
        if (stop) { stop.disabled = !running; }
        state.elapsedBase = status.started_at ? Date.parse(status.started_at) : null;
        if (status.error) { note(status.error, 'bad'); }
        if (status.log_lines && status.log_lines > state.logNext && state.logLines.length === 0) {
            backfillLog();
        }
    }

    function refreshStatus() {
        return api('/api/run/status').then(function (data) {
            setRunState(data);
            if (data.log_tail && data.log_tail.length && state.logLines.length === 0) {
                data.log_tail.forEach(appendLog);
            }
        }).catch(function () { /* server busy or restarting */ });
    }

    function startRun() {
        if (!state.accepted) { note('Accept the disclaimer before starting.', 'bad'); return; }
        var patch = collectPatch();
        note('Saving settings...');
        api('/api/settings', { method: 'POST', body: patch }).catch(function () { /* start still proceeds */ }).then(function () {
            return api('/api/run/start', { method: 'POST', body: patch });
        }).then(function (data) {
            note('Run started (' + (data.run_id || 'starting') + ').', 'ok');
            refreshStatus();
        }).catch(function (error) {
            if (error.status === 409) { note('A run is already active. Stop it first.', 'bad'); }
            else if (error.status === 400) { note('Cannot start: ' + error.message, 'bad'); }
            else { note('Start failed: ' + error.message, 'bad'); }
            refreshStatus();
        });
    }

    function stopRun() {
        api('/api/run/stop', { method: 'POST' }).then(function (data) {
            note('Stop requested (' + (data.state || 'stopping') + ').', 'ok');
            refreshStatus();
        }).catch(function (error) {
            note('Stop failed: ' + error.message, 'bad');
        });
    }

    function preview() {
        api('/api/preview/namespace', { method: 'POST', body: collectPatch() }).then(function (data) {
            var box = byId('command-preview');
            if (!box) { return; }
            var line = data.command_line || ((data.argv || []).join(' '));
            box.textContent = line;
            box.classList.remove('hidden');
        }).catch(function (error) {
            note('Preview failed: ' + error.message, 'bad');
        });
    }

    // ---------------------------------------------------------------- log
    function appendLog(line) {
        var box = byId('run-log');
        if (!box) { return; }
        state.logLines.push(line);
        if (state.logLines.length > 2000) { state.logLines.shift(); }
        box.textContent += (box.textContent ? '\n' : '') + line;
        if (box.scrollHeight - box.scrollTop - box.clientHeight < 80) { box.scrollTop = box.scrollHeight; }
    }

    function backfillLog() {
        return api('/api/run/log?since=' + state.logNext).then(function (data) {
            (data.lines || []).forEach(appendLog);
            if (typeof data.next === 'number') { state.logNext = data.next; }
        }).catch(function () { /* socket may already cover it */ });
    }

    function pollLog() {
        if (state.socketLive) { return; }
        api('/api/run/log?since=' + state.logNext).then(function (data) {
            (data.lines || []).forEach(appendLog);
            if (typeof data.next === 'number') { state.logNext = data.next; }
        }).catch(function () { /* transient */ });
    }

    function connectSocket() {
        if (typeof window.io !== 'function') { return; }
        try {
            // The bundled Flask server runs SocketIO with async_mode='threading',
            // which has no websocket support. Polling keeps live logs working and
            // avoids the failed upgrade the browser would otherwise log.
            state.socket = window.io({ transports: ['polling'] });
        } catch (error) {
            return;
        }
        state.socket.on('connect', function () { state.socketLive = true; });
        state.socket.on('disconnect', function () { state.socketLive = false; });
        state.socket.on('run_log', function (payload) {
            if (!payload || typeof payload.line !== 'string') { return; }
            appendLog(payload.line);
            if (typeof payload.n === 'number') { state.logNext = payload.n; }
        });
        state.socket.on('run_state', function (payload) {
            if (payload) { setRunState(payload); }
        });
    }

    // ---------------------------------------------------------------- disclaimer
    function showDisclaimer() {
        var modal = byId('disclaimer-modal');
        if (modal) { modal.classList.remove('hidden'); }
    }

    function hideDisclaimer() {
        var modal = byId('disclaimer-modal');
        if (modal) { modal.classList.add('hidden'); }
    }

    function applyDisclaimerGate() {
        state.accepted = state.settings.ui_disclaimer_accepted === true;
        var declined = byId('declined-notice');
        // The refused notice belongs to an explicit decline, not to first run.
        if (declined && state.accepted) { declined.classList.add('hidden'); }
        var start = byId('btn-start');
        if (start) { start.disabled = !state.accepted; }
        if (!state.accepted) { showDisclaimer(); } else { hideDisclaimer(); }
    }

    // ---------------------------------------------------------------- shell
    function shellReady() {
        return !!(window.__synthalinguaShell && window.pywebview && window.pywebview.api);
    }

    function refreshShellUi() {
        var shell = !!window.__synthalinguaShell;
        Array.prototype.forEach.call(document.querySelectorAll('.shell-only'), function (el) {
            el.classList.toggle('hidden', !shell);
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-pick]'), function (button) {
            button.title = shell ? 'Choose a file with the desktop picker' : 'Browser file picker (path may be name only)';
        });
    }

    function pickFile(kind, targetId) {
        var target = byId(targetId);
        if (!target) { return; }
        if (shellReady() && typeof window.pywebview.api.pick_file === 'function') {
            window.pywebview.api.pick_file(kind).then(function (result) {
                if (result && result.path) {
                    target.value = result.path;
                    if (targetId === 'file_input') { suggestNames(result.path); }
                    scheduleSave();
                }
            }).catch(function () { /* picker cancelled */ });
            return;
        }
        var input = document.createElement('input');
        input.type = 'file';
        input.style.display = 'none';
        document.body.appendChild(input);
        input.addEventListener('change', function () {
            var file = input.files && input.files[0];
            if (file) {
                target.value = file.name;
                if (targetId === 'file_input') { suggestNames(file.name); }
                note('Browser picked ' + file.name + '. Browsers hide the full path, so a run needs the path typed in or the desktop app.', 'bad');
            }
            document.body.removeChild(input);
        });
        input.click();
    }

    // ---------------------------------------------------------------- drop
    function baseName(path) {
        return String(path || '').split(/[\\/]/).pop() || '';
    }

    function dirName(path) {
        var text = String(path || '');
        var cut = Math.max(text.lastIndexOf('\\'), text.lastIndexOf('/'));
        return cut > 0 ? text.slice(0, cut) : '';
    }

    function stripExtension(name) {
        var cut = name.lastIndexOf('.');
        return cut > 0 ? name.slice(0, cut) : name;
    }

    function suggestNames(path) {
        var name = baseName(path);
        if (!name) { return; }
        var outName = byId('file_output_name');
        if (outName && !outName.value.trim()) { outName.value = stripExtension(name); }
        var outDir = byId('file_output');
        if (outDir && !outDir.value.trim()) { outDir.value = dirName(path); }
    }

    function handleDroppedPath(path) {
        if (!path) { return; }
        var input = byId('file_input');
        if (input) { input.value = path; }
        suggestNames(path);
        if (state.mode !== 'captions') { switchTab('captions'); }
        scheduleSave();
        note('Dropped ' + baseName(path) + '.', 'ok');
        createVideoSession(path);
    }

    function createVideoSession(path) {
        api('/api/video/create_from_path', { method: 'POST', body: { path: path } }).then(function (data) {
            if (!data || !data.session_id) { return; }
            state.videoSession = data.session_id;
            var link = byId('video-translate-link');
            if (link) {
                link.href = '/video_player.html?session=' + encodeURIComponent(data.session_id);
                link.textContent = 'Video translate (session ready)';
            }
            note('Video session ready for ' + baseName(path) + '. Open Video translate to use it.', 'ok');
        }).catch(function (error) {
            note('Captions input filled. Video session not created: ' + error.message, 'bad');
        });
    }

    function uploadBrowserVideo(file) {
        var form = new FormData();
        form.append('video', file);
        note('Uploading ' + file.name + '...');
        fetch('/api/video/upload', { method: 'POST', body: form }).then(function (response) {
            return response.json().then(function (data) {
                if (!response.ok) { throw new Error(data.error || ('HTTP ' + response.status)); }
                return data;
            });
        }).then(function (data) {
            var link = byId('video-translate-link');
            if (data.session_id && link) {
                link.href = '/video_player.html?session=' + encodeURIComponent(data.session_id);
                link.textContent = 'Video translate (session ready)';
            }
            note('Uploaded ' + file.name + '. Open Video translate to use it.', 'ok');
        }).catch(function (error) {
            note('Upload failed: ' + error.message, 'bad');
        });
    }

    var VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.mov', '.avi', '.webm', '.m4v'];

    function wireDropZones() {
        var zone = byId('drop-captions');
        function highlight(on) {
            if (zone) { zone.classList.toggle('over', !!on); }
        }
        ['dragenter', 'dragover'].forEach(function (name) {
            document.addEventListener(name, function (event) {
                if (event.dataTransfer && Array.prototype.indexOf.call(event.dataTransfer.types || [], 'Files') !== -1) {
                    event.preventDefault();
                    highlight(true);
                }
            });
        });
        document.addEventListener('dragleave', function () { highlight(false); });
        document.addEventListener('drop', function (event) {
            if (!event.dataTransfer || !event.dataTransfer.files || !event.dataTransfer.files.length) { return; }
            event.preventDefault();
            highlight(false);
            var file = event.dataTransfer.files[0];
            if (window.__synthalinguaShell) {
                // The shell calls window.__synthalinguaDrop with real paths.
                return;
            }
            var name = file.name || '';
            var lower = name.toLowerCase();
            var isVideo = VIDEO_EXTENSIONS.some(function (ext) { return lower.slice(-ext.length) === ext; });
            var outName = byId('file_output_name');
            if (outName && !outName.value.trim()) { outName.value = stripExtension(name); }
            if (isVideo) { uploadBrowserVideo(file); }
            else { note('Browser drop keeps only the file name. Type or paste the full path, or use the desktop app.', 'bad'); }
        });
    }

    // The shell calls this on an OS drop (absolute Windows paths).
    window.__synthalinguaDrop = function (paths) {
        var list = [];
        if (Array.isArray(paths)) { list = paths; }
        else if (typeof paths === 'string') { list = [paths]; }
        list = list.filter(function (item) { return typeof item === 'string' && item.length; });
        if (!list.length) { return; }
        handleDroppedPath(list[0]);
    };

    // ---------------------------------------------------------------- wiring
    function wireTabs() {
        Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (tab) {
            tab.addEventListener('click', function () { switchTab(tab.getAttribute('data-mode')); });
        });
    }

    function wireShellButtons() {
        var open = byId('btn-caption-window');
        if (open) {
            open.addEventListener('click', function () {
                if (shellReady() && window.pywebview.api.open_caption_window) {
                    window.pywebview.api.open_caption_window().catch(function () { /* ignore */ });
                }
            });
        }
        var close = byId('btn-caption-close');
        if (close) {
            close.addEventListener('click', function () {
                if (shellReady() && window.pywebview.api.close_caption_window) {
                    window.pywebview.api.close_caption_window().catch(function () { /* ignore */ });
                }
            });
        }
        var pin = byId('chk-caption-pin');
        if (pin) {
            pin.addEventListener('change', function () {
                state.settings.ui_caption_pinned = pin.checked;
                api('/api/settings', { method: 'POST', body: { ui_caption_pinned: pin.checked } }).catch(function () { /* ignore */ });
                if (shellReady() && window.pywebview.api.set_caption_pinned) {
                    window.pywebview.api.set_caption_pinned(pin.checked).catch(function () { /* ignore */ });
                }
            });
        }
        var quit = byId('btn-quit');
        if (quit) {
            quit.addEventListener('click', function () {
                if (shellReady() && window.pywebview.api.quit_app && window.confirm('Close Synthalingua?')) {
                    window.pywebview.api.quit_app();
                }
            });
        }
    }

    function wireControls() {
        document.addEventListener('input', function (event) {
            if (event.target && event.target.hasAttribute && event.target.hasAttribute('data-key')) { scheduleSave(); }
        });
        document.addEventListener('change', function (event) {
            if (event.target && event.target.closest && event.target.closest('[data-key]')) { scheduleSave(); }
            else if (event.target && (event.target.name === 'subtype' || event.target.name === 'batch-mode')) { scheduleSave(); }
            else if (event.target && event.target.id === 'captions-compare') { scheduleSave(); }
            else if (event.target && event.target.id === 'hls-selectsource') { scheduleSave(); }
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-pick]'), function (button) {
            button.addEventListener('click', function () {
                pickFile(button.getAttribute('data-pick'), button.getAttribute('data-target'));
            });
        });
        if (byId('btn-start')) { byId('btn-start').addEventListener('click', startRun); }
        if (byId('btn-stop')) { byId('btn-stop').addEventListener('click', stopRun); }
        if (byId('btn-preview')) { byId('btn-preview').addEventListener('click', preview); }
        if (byId('btn-save')) { byId('btn-save').addEventListener('click', function () { saveSettings(false); }); }
        if (byId('btn-reload')) { byId('btn-reload').addEventListener('click', function () { loadSettings(); }); }
        if (byId('btn-refresh-models')) { byId('btn-refresh-models').addEventListener('click', refreshModels); }
        if (byId('btn-refresh-mics')) { byId('btn-refresh-mics').addEventListener('click', refreshMicrophones); }
        if (byId('btn-copy-log')) {
            byId('btn-copy-log').addEventListener('click', function () {
                var text = state.logLines.join('\n');
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text).then(function () { note('Log copied.', 'ok'); }).catch(function () { note('Copy failed.', 'bad'); });
                } else {
                    note('Clipboard unavailable in this view.', 'bad');
                }
            });
        }
        if (byId('btn-clear-log')) {
            byId('btn-clear-log').addEventListener('click', function () {
                state.logLines = [];
                var box = byId('run-log');
                if (box) { box.textContent = ''; }
            });
        }
        if (byId('btn-disclaimer-accept')) {
            byId('btn-disclaimer-accept').addEventListener('click', function () {
                api('/api/settings', { method: 'POST', body: { ui_disclaimer_accepted: true } }).then(function (data) {
                    state.settings = data.settings || state.settings;
                    state.settings.ui_disclaimer_accepted = true;
                    applyDisclaimerGate();
                    note('Disclaimer accepted.', 'ok');
                }).catch(function (error) {
                    note('Could not record acceptance: ' + error.message, 'bad');
                });
            });
        }
        if (byId('btn-disclaimer-decline')) {
            byId('btn-disclaimer-decline').addEventListener('click', function () {
                hideDisclaimer();
                state.accepted = false;
                var declined = byId('declined-notice');
                if (declined) { declined.classList.remove('hidden'); }
                if (byId('btn-start')) { byId('btn-start').disabled = true; }
            });
        }
        if (byId('btn-review-disclaimer')) {
            byId('btn-review-disclaimer').addEventListener('click', function () {
                var declined = byId('declined-notice');
                if (declined) { declined.classList.add('hidden'); }
                showDisclaimer();
            });
        }
    }

    function startTimers() {
        state.statusTimer = setInterval(function () {
            refreshStatus();
            if (state.elapsedBase) {
                var seconds = Math.max(0, Math.round((Date.now() - state.elapsedBase) / 1000));
                var label = byId('run-elapsed');
                if (label) { label.textContent = 'elapsed ' + seconds + 's'; }
            }
        }, 2000);
        state.logTimer = setInterval(pollLog, 2500);
    }

    function loadSettings() {
        return api('/api/settings').then(function (data) {
            applySettings(data.settings || {});
            applyDisclaimerGate();
            var pin = byId('chk-caption-pin');
            if (pin) { pin.checked = !!state.settings.ui_caption_pinned; }
            return data;
        }).catch(function (error) {
            note('Could not load settings: ' + error.message, 'bad');
        });
    }

    function init() {
        refreshShellUi();
        wireTabs();
        wireControls();
        wireShellButtons();
        wireDropZones();
        loadSettings().then(function () {
            refreshModels();
            refreshMicrophones();
            refreshLanguages();
            refreshBlocklist();
        });
        connectSocket();
        backfillLog();
        refreshStatus();
        startTimers();
        window.addEventListener('pywebviewready', function () {
            refreshShellUi();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
