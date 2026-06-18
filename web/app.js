let isPlaying = true;
let playInterval = null;
let currentCameraIndex = 0;
const cameraImages = [
    "road.png",
    "road.png",
    "road.png",
    "road.png"
];

// Animation state
let lastState = null;
let vehicles = [];
let laneWidth = 12;

window.lightHotspots = [];

async function handleCanvasClick(e) {
    const toggle = document.getElementById('manual-override-toggle');
    if (!toggle || (!toggle.checked && toggle.value !== 'on')) return;

    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    for (let light of window.lightHotspots) {
        if (Math.abs(x - light.x) < 35 && Math.abs(y - light.y) < 35) {
            const nextState = light.currentState === 'GREEN' ? 'RED' : 'GREEN';
            
            if (lastState && lastState.intersections.length > 0) {
                const int_id = lastState.intersections[0].id;
                const lanesToUpdate = lastState.intersections[0].lanes.filter(l => l.name.startsWith(light.direction));
                
                for (let lane of lanesToUpdate) {
                    await fetch('/api/signal/override', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            intersection_id: int_id,
                            lane_id: lane.name,
                            state: nextState
                        })
                    });
                }
                showToast(`${light.direction} signals set to ${nextState}`);
            }
            break;
        }
    }
}

class Vehicle {
    constructor(id, laneId, startX, startY, endX, endY, color) {
        this.id = id;
        this.laneId = laneId;
        this.x = startX;
        this.y = startY;
        this.startX = startX;
        this.startY = startY;
        this.endX = endX;
        this.endY = endY;
        this.progress = 0;
        this.speed = 0.005 + Math.random() * 0.005;
        this.color = color;
        this.isStopped = false;
        this.isEmergency = id.includes('E') || color === '#ef4444';
    }

    update(signalState, currentRule, vehicleAhead) {
        let shouldStop = false;
        // Near-side stopping logic
        const stopProgress = 0.45; 
        
        if (currentRule === 'SIGNALIZED') {
            if (signalState === 'RED' && this.progress > stopProgress - 0.05 && this.progress < stopProgress) {
                shouldStop = true;
            }
        }
        
        if (vehicleAhead) {
            let dist = vehicleAhead.progress - this.progress;
            if (dist > 0 && dist < 0.035) {
                shouldStop = true;
            }
        }

        this.isStopped = shouldStop;

        if (!this.isStopped) {
            this.progress += this.speed;
            if (this.progress > 1) this.progress = 0;
        }

        this.x = this.startX + (this.endX - this.startX) * this.progress;
        this.y = this.startY + (this.endY - this.startY) * this.progress;
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);

        const isHorizontal = Math.abs(this.endX - this.startX) > Math.abs(this.endY - this.startY);
        if (!isHorizontal) {
            ctx.rotate(Math.PI / 2);
        } else if (this.startX > this.endX) {
            ctx.rotate(Math.PI);
        }

        const carLen = laneWidth * 1.5;
        const carWid = laneWidth * 0.7;

        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.roundRect(-carLen / 2, -carWid / 2, carLen, carWid, 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fillRect(-carLen * 0.2, -carWid * 0.4, carLen * 0.4, carWid * 0.8);

        if (this.isEmergency) {
            ctx.fillStyle = (Date.now() % 400 < 200) ? '#ff0000' : '#0000ff';
            ctx.beginPath(); ctx.arc(0, 0, 2, 0, Math.PI * 2); ctx.fill();
        }

        ctx.rotate(isHorizontal ? 0 : -Math.PI / 2);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 8px Outfit';
        ctx.textAlign = 'center';
        ctx.fillText(this.id.replace('Vehicle-', 'V'), 0, -6);

        ctx.restore();
    }
}

async function fetchState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        lastState = data;
        syncVehicles(data);
        updateUI(data);
    } catch (error) {
        console.error('Error fetching state:', error);
    }
}

function syncVehicles(data) {
    const mapContainer = document.getElementById('simulation-map');
    if (!mapContainer) return;
    const width = mapContainer.clientWidth;
    const height = mapContainer.clientHeight;

    let nextVehicles = [];
    const mainLanes = document.getElementById('main-lanes-select') ? parseInt(document.getElementById('main-lanes-select').value) : 2;
    const secLanes = document.getElementById('secondary-lanes-select') ? parseInt(document.getElementById('secondary-lanes-select').value) : 2;

    laneWidth = Math.max(width, height) * 0.025;

    data.intersections.forEach((intx) => {
        const cx = width / 2;
        const cy = height / 2;

        intx.lanes.forEach(lane => {
            const [direction, laneNum] = lane.name.split('-');
            const lIdx = parseInt(laneNum);
            const totalLanesInDir = (direction === 'North' || direction === 'South') ? mainLanes : secLanes;

            const offsetMag = (totalLanesInDir - lIdx + 0.5) * laneWidth;
            let laneOffset = 0;
            if (direction === 'North') laneOffset = -offsetMag;
            else if (direction === 'South') laneOffset = offsetMag;
            else if (direction === 'East') laneOffset = -offsetMag;
            else if (direction === 'West') laneOffset = offsetMag;

            lane.vehicles.forEach(vId => {
                let startX, startY, endX, endY;
                const roadLen = Math.max(width, height) * 0.8;

                if (direction === 'North') { startX = cx + laneOffset; startY = cy - roadLen; endX = cx + laneOffset; endY = cy + roadLen; }
                else if (direction === 'South') { startX = cx + laneOffset; startY = cy + roadLen; endX = cx + laneOffset; endY = cy - roadLen; }
                else if (direction === 'East') { startX = cx + roadLen; startY = cy + laneOffset; endX = cx - roadLen; endY = cy + laneOffset; }
                else if (direction === 'West') { startX = cx - roadLen; startY = cy + laneOffset; endX = cx + roadLen; endY = cy + laneOffset; }

                let existing = vehicles.find(v => v.id === vId);
                let color = lane.has_emergency ? '#ef4444' : (vId.includes('E') ? '#ef4444' : '#3b82f6');
                let v = new Vehicle(vId, lane.name, startX, startY, endX, endY, color);
                if (existing) v.progress = existing.progress;
                nextVehicles.push(v);
            });
        });
    });
    vehicles = nextVehicles;
}

async function tick() {
    try {
        const response = await fetch('/api/tick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ steps: 1 })
        });
        const data = await response.json();
        lastState = data;
        syncVehicles(data);
        updateUI(data);
    } catch (error) {
        console.error('Error ticking:', error);
    }
}

async function reset() {
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json();
        lastState = data;
        syncVehicles(data);
        updateUI(data);
        showToast('Simulation Reset');
    } catch (error) {
        console.error('Error resetting:', error);
    }
}

async function updateConfig() {
    const rule = document.getElementById('rule-select').value;
    const mainLanes = document.getElementById('main-lanes-select') ? parseInt(document.getElementById('main-lanes-select').value) : 2;
    const secondaryLanes = document.getElementById('secondary-lanes-select') ? parseInt(document.getElementById('secondary-lanes-select').value) : 2;

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rule, main_lanes: mainLanes, secondary_lanes: secondaryLanes })
        });
        const data = await response.json();
        lastState = data;
        syncVehicles(data);
        updateUI(data);
        showToast(`Configuration Updated: ${rule}`);
    } catch (error) {
        console.error('Error updating config:', error);
    }
}

async function updateTraffic() {
    const intensity = document.getElementById('intensity-slider').value;
    try {
        await fetch('/api/traffic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ intensity })
        });
        showToast(`Traffic Intensity: ${intensity}%`);
    } catch (error) {
        console.error('Error updating traffic:', error);
    }
}

function updateUI(data) {
    const ruleBadge = document.getElementById('active-rule-badge');
    if (ruleBadge) {
        ruleBadge.textContent = data.rule;
        ruleBadge.className = `status-badge rule ${data.rule.toLowerCase()}`;
    }

    const intensityVal = document.getElementById('intensity-val');
    if (intensityVal) {
        const slider = document.getElementById('intensity-slider');
        intensityVal.textContent = slider.value + '%';
    }

    const signalsContainer = document.getElementById('signals-container');
    signalsContainer.innerHTML = '';

    data.intersections.forEach(intx => {
        intx.lanes.forEach(lane => {
            if (!lane.name.endsWith('-1')) return;

            const miniCard = document.createElement('div');
            miniCard.className = 'signal-mini-card';

            const isSignalized = data.rule === 'SIGNALIZED';
            let lightsHtml = '';
            
            if (isSignalized) {
                lightsHtml = `
                    <div class="signal-head">
                        <div class="light-unit red ${lane.signal_state === 'RED' ? 'active' : ''}"></div>
                        <div class="light-unit yellow ${lane.signal_state === 'YELLOW' ? 'active' : ''}"></div>
                        <div class="light-unit green ${lane.signal_state === 'GREEN' ? 'active' : ''}"></div>
                    </div>
                    <div class="signal-info">
                        <span class="signal-timer-label">${lane.signal_timer}s</span>
                        <span class="signal-status-text">${lane.signal_state}</span>
                    </div>
                `;
            } else {
                lightsHtml = `<div class="mini-lights-off"><i data-lucide="shield-check" class="rule-icon"></i></div>`;
            }

            miniCard.innerHTML = `
                <h4>${intx.id} - ${lane.name.split('-')[0]}</h4>
                ${lightsHtml}
            `;
            
            if (isSignalized && document.getElementById('manual-override-toggle').checked) {
                miniCard.style.cursor = 'pointer';
                miniCard.title = 'Click to cycle signal state (Manual Mode)';
                miniCard.addEventListener('click', async () => {
                    const nextState = { 'RED': 'GREEN', 'GREEN': 'YELLOW', 'YELLOW': 'RED' }[lane.signal_state];
                    try {
                        await fetch('/api/signal/override', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ intersection_id: intx.id, lane_id: lane.name, state: nextState })
                        });
                        fetchState();
                    } catch (e) { console.error(e); }
                });
            }
            
            signalsContainer.appendChild(miniCard);
        });
    });
    lucide.createIcons();

    const totalVehicles = data.intersections.reduce((sum, intx) => sum + intx.lanes.reduce((s, l) => s + l.vehicle_count, 0), 0);
    document.getElementById('total-vehicles-count').textContent = totalVehicles.toLocaleString();

    let efficiency = 85;
    if (data.rule === 'RIGHT_PRIORITY') efficiency = 65;
    if (data.rule === 'PRIORITY_ROAD') efficiency = 75;
    updateDonut(efficiency);
}

function updateDonut(val) {
    const donut = document.getElementById('flow-donut');
    if (!donut) return;
    const center = donut.querySelector('.donut-center h4');
    if (center) center.textContent = val + '%';
    donut.style.background = `conic-gradient(var(--status-green) 0% ${val}%, var(--status-yellow) ${val}% 85%, var(--status-red) 85% 95%, var(--status-gray) 95% 100%)`;
}

function animate() {
    const mapContainer = document.getElementById('simulation-map');
    if (!mapContainer) return requestAnimationFrame(animate);

    let canvas = mapContainer.querySelector('canvas');
    if (!canvas) {
        canvas = document.createElement('canvas');
        canvas.width = mapContainer.clientWidth;
        canvas.height = mapContainer.clientHeight;
        mapContainer.innerHTML = '';
        mapContainer.appendChild(canvas);
        canvas.addEventListener('click', handleCanvasClick);
    }

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);
    window.lightHotspots = [];

    if (lastState) {
        const mainLanes = document.getElementById('main-lanes-select') ? parseInt(document.getElementById('main-lanes-select').value) : 2;
        const secLanes = document.getElementById('secondary-lanes-select') ? parseInt(document.getElementById('secondary-lanes-select').value) : 2;
        const currentRule = lastState.rule;

        const cx = width / 2;
        const cy = height / 2;

        const vRoadW = (mainLanes * 2) * laneWidth + 10;
        const hRoadW = (secLanes * 2) * laneWidth + 10;

        lastState.intersections.forEach(intx => {
            ctx.fillStyle = 'rgba(255,255,255,0.8)';
            ctx.font = 'bold 16px Outfit';
            ctx.textAlign = 'center';
            ctx.fillText(intx.id, cx, cy - hRoadW / 2 - 30);

            intx.lanes.forEach(lane => {
                const [direction, laneNum] = lane.name.split('-');
                const lIdx = parseInt(laneNum);
                const totalLanesInDir = (direction === 'North' || direction === 'South') ? mainLanes : secLanes;

                const offsetMag = (totalLanesInDir - lIdx + 0.5) * laneWidth;
                let laneOffset = 0;
                if (direction === 'North') laneOffset = -offsetMag;
                else if (direction === 'South') laneOffset = offsetMag;
                else if (direction === 'East') laneOffset = -offsetMag;
                else if (direction === 'West') laneOffset = offsetMag;

                let laneVehicles = vehicles.filter(v => v.laneId === lane.name);
                laneVehicles.sort((a, b) => b.progress - a.progress);

                laneVehicles.forEach((v, idx) => {
                    let vehicleAhead = idx > 0 ? laneVehicles[idx - 1] : null;
                    v.update(lane.signal_state, currentRule, vehicleAhead);
                    v.draw(ctx);
                });

                // Signal Rendering
                if (currentRule === 'SIGNALIZED') {
                    const signalState = lane.signal_state;
                    const activeColor = signalState === 'GREEN' ? '#4cd964' : (signalState === 'YELLOW' ? '#ffcc00' : '#ff3b30');
                    
                    if (lIdx === 1) {
                        // Calculate the center point of the incoming lanes
                        const incCenter = (totalLanesInDir * laneWidth) / 2;
                        let finalSx, finalSy;
                        const margin = 20;
                        
                        if (direction === 'North') { 
                            finalSx = cx - incCenter; 
                            finalSy = cy - hRoadW / 2 - margin; 
                        }
                        else if (direction === 'South') { 
                            finalSx = cx + incCenter; 
                            finalSy = cy + hRoadW / 2 + margin; 
                        }
                        else if (direction === 'East') { 
                            finalSx = cx + vRoadW / 2 + margin; 
                            finalSy = cy - incCenter; 
                        }
                        else if (direction === 'West') { 
                            finalSx = cx - vRoadW / 2 - margin; 
                            finalSy = cy + incCenter; 
                        }

                        // Helper to draw a traffic light head
                        const drawSignalHead = (x, y, vertical = true) => {
                            const headW = vertical ? 20 : 45;
                            const headH = vertical ? 45 : 20;
                            
                            // Housing
                            ctx.fillStyle = '#1a1a1a';
                            ctx.beginPath();
                            ctx.roundRect(x - headW / 2, y - headH / 2, headW, headH, 4);
                            ctx.fill();
                            ctx.strokeStyle = '#333';
                            ctx.lineWidth = 1;
                            ctx.stroke();

                            // Lights
                            const positions = [-12, 0, 12];
                            const states = ['RED', 'YELLOW', 'GREEN'];

                            positions.forEach((pos, i) => {
                                const lx = vertical ? x : x + pos;
                                const ly = vertical ? y + pos : y;
                                const isActive = signalState === states[i];
                                
                                ctx.fillStyle = isActive ? activeColor : '#333';
                                ctx.beginPath();
                                ctx.arc(lx, ly, 4, 0, Math.PI * 2);
                                ctx.fill();

                                if (isActive) {
                                    ctx.shadowBlur = 15;
                                    ctx.shadowColor = activeColor;
                                    ctx.beginPath();
                                    ctx.arc(lx, ly, 4.5, 0, Math.PI * 2);
                                    ctx.stroke();
                                    ctx.shadowBlur = 0;
                                }
                            });
                        };

                        drawSignalHead(finalSx, finalSy, (direction === 'East' || direction === 'West'));
                        
                        window.lightHotspots.push({
                            x: finalSx,
                            y: finalSy,
                            direction: direction,
                            currentState: signalState
                        });
                    }
                }
            });
        });
    }
    requestAnimationFrame(animate);
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.style = "position:fixed; bottom:20px; left:50%; transform:translateX(-50%); background:rgba(37,99,235,0.9); color:white; padding:12px 24px; border-radius:12px; z-index:1000; font-size:0.9rem; font-weight:600; box-shadow:0 4px 15px rgba(0,0,0,0.3);";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

document.getElementById('tick-btn').addEventListener('click', tick);
document.getElementById('play-btn').addEventListener('click', () => {
    isPlaying = !isPlaying;
    const btn = document.getElementById('play-btn');
    if (isPlaying) {
        btn.innerHTML = '<i data-lucide="pause"></i>';
        playInterval = setInterval(tick, 1000);
    } else {
        btn.innerHTML = '<i data-lucide="fast-forward"></i>';
        clearInterval(playInterval);
    }
    lucide.createIcons();
});
const resetBtn = document.getElementById('reset-btn');
if (resetBtn) resetBtn.addEventListener('click', reset);

const ruleSelect = document.getElementById('rule-select');
if (ruleSelect) ruleSelect.addEventListener('change', updateConfig);

const mainLanesSelect = document.getElementById('main-lanes-select');
if (mainLanesSelect) mainLanesSelect.addEventListener('change', updateConfig);

const secLanesSelect = document.getElementById('secondary-lanes-select');
if (secLanesSelect) secLanesSelect.addEventListener('change', updateConfig);

const intensitySlider = document.getElementById('intensity-slider');
if (intensitySlider) {
    intensitySlider.addEventListener('input', (e) => {
        const val = document.getElementById('intensity-val');
        if (val) val.textContent = e.target.value + '%';
    });
    intensitySlider.addEventListener('change', updateTraffic);
}

document.getElementById('manual-override-toggle').addEventListener('change', async (e) => {
    const isManual = e.target.value === 'on' || e.target.checked;
    document.getElementById('manual-status').textContent = isManual ? 'Manual' : 'Auto';
    document.getElementById('manual-status').style.color = isManual ? 'var(--status-yellow)' : 'var(--text-secondary)';
    
    if (!isManual) {
        // Clear all overrides
        try {
            if (lastState) {
                for (let intx of lastState.intersections) {
                    await fetch('/api/signal/override', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ intersection_id: intx.id, state: null })
                    });
                }
            }
        } catch (e) { console.error(e); }
    }
    fetchState();
});

const navItems = [
    { id: 'nav-dashboard', show: ['section-map', 'section-settings', 'section-overview', 'section-analytics', 'section-signals', 'section-incidents', 'section-camera'] },
    { id: 'nav-live-traffic', show: ['section-map', 'section-camera', 'section-overview'] },
    { id: 'nav-traffic-lights', show: ['section-signals', 'section-settings'] },
    { id: 'nav-incidents', show: ['section-incidents', 'section-camera'] },
    { id: 'nav-analytics', show: ['section-analytics', 'section-overview'] },
    { id: 'nav-reports', show: ['section-overview', 'section-analytics'] },
    { id: 'nav-settings', show: ['section-settings'] }
];

navItems.forEach(item => {
    const el = document.getElementById(item.id);
    if (!el) return;

    el.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        el.classList.add('active');

        const allSections = ['section-map', 'section-settings', 'section-overview', 'section-analytics', 'section-signals', 'section-incidents', 'section-camera'];
        allSections.forEach(sId => {
            const s = document.getElementById(sId);
            if (s) s.style.display = 'none';
        });

        item.show.forEach(sId => {
            const s = document.getElementById(sId);
            if (s) {
                s.style.display = 'block';
                if (sId === 'section-map') s.style.display = 'flex';
            }
        });

        showToast(`Switched to ${el.textContent.trim()}`);
        document.querySelector('.main-content').scrollTo({ top: 0, behavior: 'smooth' });
    });
});

window.addEventListener('DOMContentLoaded', () => {
    fetchState();
    animate();
    lucide.createIcons();
    
    // Sidebar toggle functionality
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }
    
    // Start live traffic by default
    if (isPlaying) {
        playInterval = setInterval(tick, 1000);
        const playBtn = document.getElementById('play-btn');
        if (playBtn) playBtn.innerHTML = '<i data-lucide="pause"></i>';
    }
});
