let allEventsData = []; 
let specialEventsData = [];

async function loadAgenda() {
    try {
        // 1. Cargar la agenda normal
        const response = await fetch('data/data.json');
        if (!response.ok) throw new Error(`Could not retrieve data/data.json file`);
        allEventsData = await response.json();
        
        // 2. Cargar la agenda de eventos especiales (Silencioso si el archivo no existe)
        try {
            const specialResponse = await fetch('data/data_special.json');
            if (specialResponse.ok) {
                specialEventsData = await specialResponse.json();
            }
        } catch (error) {
            console.log("No data_special.json found. Skipping featured events.");
        }

        // 🎯 LÓGICA PARA OCULTAR FILTROS VACÍOS (Combina ambos archivos para revisar)
        const allCombined = [...allEventsData, ...specialEventsData];
        const activeCategories = new Set(allCombined.map(ev => ev.category ? ev.category.toLowerCase() : ''));
        
        document.querySelectorAll('.filter-btn').forEach(button => {
            const filterValue = button.getAttribute('data-filter');
            if (filterValue !== 'all' && !activeCategories.has(filterValue.toLowerCase())) {
                button.style.display = 'none';
            } else {
                button.style.display = ''; 
            }
        });
        
        renderEvents('all'); 
        setupFilterListeners();      
    } catch (error) {
        const container = document.getElementById('agenda-container');
        container.innerHTML = `
            <div style="background: #ffebe9; border: 2px dashed #ff8182; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #cf222e; margin-top: 0;">🚨 Error loading agenda</h3>
                <p style="color: #24292f;"><strong>Details:</strong> ${error.message}</p>
            </div>
        `;
    }
}

// 📅 LÓGICA DE FECHAS
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function parseEventDate(dateString, timeString) {
    if (!dateString) return new Date(0);
    const timePart = timeString || "00:00";
    const [year, month, day] = dateString.split('-');
    const [hours, minutes] = timePart.split(':');
    return new Date(year, month - 1, day, hours, minutes);
}

// 🧩 FUNCIÓN MOLDE PARA DIBUJAR CADA EVENTO SIN REPETIR CÓDIGO
function generateEventRowHTML(eventItem) {
    const priceLabel = (eventItem.price === null || eventItem.price === 0) ? "Free admission" : `CHF ${eventItem.price}.-`;
    const colorThemeClass = eventItem.colour || 'blue';
    const cleanDateString = eventItem.date ? eventItem.date.replace(/-/g, '') : '';
    const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(eventItem.title)}&dates=${cleanDateString}T000000Z/${cleanDateString}T235959Z&details=${encodeURIComponent(eventItem.description || '')}&location=${encodeURIComponent(eventItem.location || '')}`;

    return `
        <div class="event-row theme-${colorThemeClass}">
            <div class="event-row-main">
                <div class="event-content">
                    <p class="event-title"><span class="event-icon">${eventItem.icon || '📍'}</span> ${eventItem.title}</p>
                    <p class="event-desc"><strong>${eventItem.displayTime}</strong> · ${eventItem.location || 'Location not specified'}</p>
                    <span class="event-price">${priceLabel}</span>
                </div>
                <div class="event-actions">
                    <a href="${googleCalendarUrl}" class="cal-btn" target="_blank">+ Calendar</a>
                    ${eventItem.google_maps ? `<a href="${eventItem.google_maps}" class="loc-btn" target="_blank">📍 Maps</a>` : ''}
                    ${eventItem.description ? `
                        <button class="info-btn" onclick="toggleDetail(this)">
                            More info <i class="info-arrow">▾</i>
                        </button>
                    ` : ''}
                </div>
            </div>
            ${eventItem.description ? `
                <div class="event-detail-panel">
                    <div class="event-detail-inner">
                        ${eventItem.description.replace(/\n/g, '<br>')}
                    </div>
                </div>
            ` : ''}
        </div>`;
}

function renderEvents(selectedFilter) {
    const container = document.getElementById('agenda-container');
    container.innerHTML = ''; 

    // Filtrar ambos arrays
    let filteredEvents = allEventsData.filter(ev => selectedFilter === 'all' || (ev.category && ev.category.toLowerCase() === selectedFilter.toLowerCase()));
    let filteredSpecial = specialEventsData.filter(ev => selectedFilter === 'all' || (ev.category && ev.category.toLowerCase() === selectedFilter.toLowerCase()));

    if (filteredEvents.length === 0 && filteredSpecial.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 40px; color: #666; font-size: 14px;">No events available in this category.</p>`;
        return;
    }

    // ==========================================
    // ⭐ 1. RENDERIZAR EVENTOS ESPECIALES (TOP)
    // ==========================================
    if (filteredSpecial.length > 0) {
        // Ordenarlos cronológicamente
        filteredSpecial.sort((a, b) => parseEventDate(a.date, a.time) - parseEventDate(b.date, b.time));
        
        // Cabecera Especial Hilti (Roja con Estrella)
        let specialHtml = `
            <div class="venue-block">
                <div class="venue-header" style="background-color: #D20000; color: #ffffff; border-bottom: none;">
                    <div class="icon-box" style="background-color: #a30000; color: #ffffff;">⭐</div>
                    <span>Featured Events</span>
                </div>
        `;
        
        filteredSpecial.forEach(ev => {
            // Como los especiales no tienen cabecera de "día", añadimos el mes y día a su hora (Ej: Oct 25 · 20:00h)
            const d = parseEventDate(ev.date, ev.time);
            const timeStr = ev.time ? `${ev.time}h` : "All day";
            ev.displayTime = isNaN(d.getTime()) ? timeStr : `${months[d.getMonth()]} ${d.getDate()} · ${timeStr}`;
            
            specialHtml += generateEventRowHTML(ev);
        });
        
        specialHtml += `</div>`;
        container.innerHTML += specialHtml;
    }

    // ==========================================
    // 📅 2. RENDERIZAR EVENTOS NORMALES (ABAJO)
    // ==========================================
    if (filteredEvents.length > 0) {
        filteredEvents.sort((a, b) => parseEventDate(a.date, a.time) - parseEventDate(b.date, b.time));

        const groupedEvents = {};
        filteredEvents.forEach(ev => {
            const parsedDateObj = parseEventDate(ev.date, ev.time);
            const weekdayName = isNaN(parsedDateObj.getTime()) ? "" : weekdays[parsedDateObj.getDay()];
            const dayNumber = isNaN(parsedDateObj.getTime()) ? "??" : parsedDateObj.getDate().toString().padStart(2, '0');
            const monthName = isNaN(parsedDateObj.getTime()) ? "??" : months[parsedDateObj.getMonth()];
            
            const groupingKey = weekdayName ? `${weekdayName}, ${monthName} ${dayNumber}` : "Date to be determined";

            if (!groupedEvents[groupingKey]) groupedEvents[groupingKey] = [];
            
            ev.displayTime = ev.time ? `${ev.time}h` : "All day"; // Los normales solo muestran la hora
            groupedEvents[groupingKey].push(ev);
        });

        for (const [dayHeaderLabel, dailyEventsList] of Object.entries(groupedEvents)) {
            let regularHtml = `
                <div class="venue-block">
                    <div class="venue-header" style="background-color: #24292f; color: #ffffff; border-bottom: none;">
                        <div class="icon-box" style="background-color: #3b4046; color: #ffffff;">📅</div>
                        <span>${dayHeaderLabel}</span>
                    </div>
            `;
            
            dailyEventsList.forEach(ev => {
                regularHtml += generateEventRowHTML(ev);
            });
            
            regularHtml += `</div>`;
            container.innerHTML += regularHtml;
        }
    }
}

function setupFilterListeners() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(buttonElement => {
        buttonElement.addEventListener('click', (clickEvent) => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            const clickedTarget = clickEvent.currentTarget;
            clickedTarget.classList.add('active');
            
            const activeFilterQuery = clickedTarget.getAttribute('data-filter');
            renderEvents(activeFilterQuery);
        });
    });
}

// Initialize Application
loadAgenda();