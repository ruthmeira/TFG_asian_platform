let currentDate = new Date();
let eventsData = [];

const monthNames = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

async function fetchEvents(month, year) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('active');
    
    try {
        const response = await fetch(`/api/calendar/events?month=${month + 1}&year=${year}`);
        eventsData = await response.json();
        renderCalendar();
    } catch (error) {
        console.error("Error fetching events:", error);
    } finally {
        if (overlay) overlay.classList.remove('active');
    }
}

function renderCalendar() {
    const grid = document.getElementById('calendarDays');
    const monthTitle = document.getElementById('monthTitle');
    
    if (!grid || !monthTitle) return;
    
    grid.innerHTML = '';
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    monthTitle.innerText = `${monthNames[month]} ${year}`;
    
    const firstDay = new Date(year, month, 1).getDay();
    const offset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    for (let i = 0; i < offset; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        grid.appendChild(emptyDay);
    }
    
    const today = new Date();
    const isCurrentMonth = today.getMonth() === month && today.getFullYear() === year;

    for (let day = 1; day <= daysInMonth; day++) {
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        if (isCurrentMonth && today.getDate() === day) {
            dayEl.classList.add('today');
        }
        
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayEvents = eventsData.filter(e => e.date === dateStr);
        
        dayEl.innerHTML = `
            <span class="day-number">${day}</span>
            <div class="event-list">
                ${dayEvents.slice(0, 3).map(e => `
                    <div class="event-item" title="${e.title}">
                        ${e.event_type}: ${e.title}
                    </div>
                `).join('')}
                ${dayEvents.length > 3 ? `<div class="event-item" style="background:none; border:none; text-align:center; font-weight:700; opacity:0.6">+ ${dayEvents.length - 3} más</div>` : ''}
            </div>
        `;
        
        if (dayEvents.length > 0) {
            dayEl.onclick = () => showDayEvents(day, month, year, dayEvents);
            dayEl.style.cursor = 'pointer';
        }
        
        grid.appendChild(dayEl);
    }
}

function showDayEvents(day, month, year, events) {
    const modal = document.getElementById('dayModal');
    const list = document.getElementById('modalEventsList');
    const title = document.getElementById('modalDateTitle');
    
    if (!modal || !list || !title) return;
    
    title.innerText = `${day} de ${monthNames[month]}, ${year}`;
    const placeholder = '/static/img/no-poster.png';
    
    list.innerHTML = events.map(e => {
        const posterUrl = e.poster ? `https://image.tmdb.org/t/p/w200${e.poster}` : placeholder;
        return `
            <a href="/media/${e.type}/${e.id}" class="daily-event-card">
                <img src="${posterUrl}" 
                     class="daily-event-poster" 
                     alt="${e.title}"
                     onerror="this.src='${placeholder}'">
                <div class="daily-event-info">
                    <span class="daily-event-title">${e.title}</span>
                    <span class="daily-event-tag">${e.event_type}</span>
                </div>
                <span style="font-size: 1.2rem; opacity: 0.4;"><i class="fas fa-chevron-right"></i></span>
            </a>
        `;
    }).join('');
    
    modal.classList.add('active');
}

function closeModal(event) {
    const modal = document.getElementById('dayModal');
    if (modal) {
        if (!event || event.target === modal) {
            modal.classList.remove('active');
        }
    }
}

function changeMonth(delta) {
    currentDate.setMonth(currentDate.getMonth() + delta);
    fetchEvents(currentDate.getMonth(), currentDate.getFullYear());
}

function resetToToday() {
    currentDate = new Date();
    fetchEvents(currentDate.getMonth(), currentDate.getFullYear());
}

document.addEventListener('DOMContentLoaded', () => {
    fetchEvents(currentDate.getMonth(), currentDate.getFullYear());
});
