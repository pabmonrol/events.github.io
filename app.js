let allEventsData = []; 
let specialEventsData = [];
let agendaIsStale = false;

function markAgendaFreshness() {
    const dated = [...allEventsData, ...specialEventsData]
        .map(ev => parseEventDate(ev.date, "00:00"))
        .filter(d => !isNaN(d.getTime()) && d.getTime() !== 0);
    if (dated.length === 0) {
        agendaIsStale = false;
        return;
    }
    const latest = new Date(Math.max(...dated.map(d => d.getTime())));
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    agendaIsStale = latest < startOfToday;
}

async function loadAgenda() {
    try {
        const response = await fetch('data/data.json');
        if (!response.ok) throw new Error(`Could not retrieve data/data.json file`);
        allEventsData = await response.json();
        
        try {
            const specialResponse = await fetch('data/data_special.json');
            if (specialResponse.ok) {
                specialEventsData = await specialResponse.json();
            }
        } catch (error) {
            console.log("No data_special.json found. Skipping featured events.");
        }

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
        
        markAgendaFreshness();
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

const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];


function parseEventDate(dateString, timeString) {
    if (!dateString) return new Date(0);
    const timePart = timeString || "00:00";
    const [year, month, day] = dateString.split('-');
    const [hours, minutes] = timePart.split(':');
    return new Date(year, month - 1, day, hours, minutes);
}

function generateEventRowHTML(eventItem, isSpecial = false) {
    let priceLabel = "";
    const isRuggell = (eventItem.comunity && eventItem.comunity.toLowerCase().includes('ruggell')) || 
                    (eventItem.location && eventItem.location.toLowerCase().includes('ruggell')) ||
                    (eventItem.comunity && eventItem.comunity.toLowerCase().includes('schellenberg')) ||
                    (eventItem.location && eventItem.location.toLowerCase().includes('schellenberg')) ||
                    (eventItem.comunity && eventItem.comunity.toLowerCase().includes('triesen')) ||
                    (eventItem.location && eventItem.location.toLowerCase().includes('triesen'));
    if (isRuggell) {
        priceLabel = "Not specified";
    } else {
        priceLabel = (eventItem.price === null || eventItem.price === 0) ? "Free admission" : `CHF ${eventItem.price}.-`;
    }
    const colorThemeClass = eventItem.colour || 'blue';
    const cleanDateString = eventItem.date ? eventItem.date.replace(/-/g, '') : '';
    const calendarLocation = eventItem.location ? `${eventItem.location}${eventItem.comunity && !eventItem.location.toLowerCase().includes(eventItem.comunity.toLowerCase()) ? `, ${eventItem.comunity}` : ''}` : (eventItem.comunity || '');

    const isAppleDevice = /Mac|iPod|iPhone|iPad/.test(navigator.platform) || /Macintosh|iPhone|iPad|iPod/.test(navigator.userAgent);
    
    let finalCalendarUrl = "";
    let calendarButtonText = "+ Calendar";

    if (isAppleDevice) {
        calendarButtonText = "+ Apple Cal";
        let icsContent = `BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:${eventItem.title}\n`;
        
        if (eventItem.time) {
            const startHours = eventItem.time.replace(/:/g, '').substring(0, 4) + "00"; 
            const [h, m] = eventItem.time.split(':').map(Number);
            const endHours = ((h + 1) % 24).toString().padStart(2, '0') + m.toString().padStart(2, '0') + "00";
            icsContent += `DTSTART:${cleanDateString}T${startHours}\n`;
            icsContent += `DTEND:${cleanDateString}T${endHours}\n`;
        } else {
            icsContent += `DTSTART;VALUE=DATE:${cleanDateString}\n`;
        }
        
        icsContent += `LOCATION:${calendarLocation}\n`;
        const cleanDesc = (eventItem.description || '').replace(/\n/g, '\\n');
        icsContent += `DESCRIPTION:${cleanDesc}\n`;
        icsContent += `END:VEVENT\nEND:VCALENDAR`;
        
        icsContent = icsContent.replace(/\n/g, '\r\n');
        finalCalendarUrl = `data:text/calendar;charset=utf8,${encodeURIComponent(icsContent)}`;
    } else {
        calendarButtonText = "+ Google Cal";
        let timeSuffix = "T000000/T235959"; 
        if (eventItem.time) {
            const startHours = eventItem.time.replace(/:/g, '').substring(0, 4) + "00"; 
            const [h, m] = eventItem.time.split(':').map(Number);
            const endHours = ((h + 1) % 24).toString().padStart(2, '0') + m.toString().padStart(2, '0') + "00";
            timeSuffix = `T${startHours}/T${endHours}`;
        }
        finalCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(eventItem.title)}&dates=${cleanDateString}${timeSuffix}&details=${encodeURIComponent(eventItem.description || '')}&location=${encodeURIComponent(calendarLocation)}`;
    }
    const specialClass = isSpecial ? 'special-event' : '';

    return `
        <div class="event-row theme-${colorThemeClass} ${specialClass}">
            <div class="event-row-main">
                <div class="event-content">
                    <p class="event-title"><span class="event-icon">${eventItem.icon || '📍'}</span> ${eventItem.title}</p>
                    <p class="event-desc"><strong>${eventItem.displayTime}</strong> · ${eventItem.location ? `${eventItem.location}${eventItem.comunity && !eventItem.location.toLowerCase().includes(eventItem.comunity.toLowerCase()) ? `, ${eventItem.comunity}` : ''}` : (eventItem.comunity || 'Location not specified')}</p>
                    <span class="event-price">${priceLabel}</span>
                </div>
                <div class="event-actions">
                    <a href="${finalCalendarUrl}" class="cal-btn" target="_blank">+ Calendar</a>
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

    if (agendaIsStale) {
        container.innerHTML = `
            <div style="background: #fff8c5; border: 2px dashed #d4a72c; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #9a6700; margin-top: 0;">Agenda data is out of date</h3>
                <p style="color: #24292f; margin-bottom: 0;">The newest saved event is before today, so this week looks empty.</p>
            </div>
        `;
    } 

    let filteredEvents = allEventsData.filter(ev => selectedFilter === 'all' || (ev.category && ev.category.toLowerCase() === selectedFilter.toLowerCase()));
    let filteredSpecial = selectedFilter === 'all' ? specialEventsData : [];

    if (filteredEvents.length === 0 && filteredSpecial.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 40px; color: #666; font-size: 14px;">No events available in this category.</p>`;
        return;
    }
 
    if (filteredSpecial.length > 0) {
        filteredSpecial.sort((a, b) => parseEventDate(a.date, a.time) - parseEventDate(b.date, b.time));
        
        let specialHtml = `
            <div class="venue-block">
                <div class="venue-header" style="background-color: #D20000; color: #ffffff; border-bottom: none;">
                    <div class="icon-box" style="background-color: #a30000; color: #ffffff;">⭐</div>
                    <span>Featured Events</span>
                </div>
        `;
        
        filteredSpecial.forEach(ev => {
            const d = parseEventDate(ev.date, ev.time);
            
            let cleanTime = null;
            if (ev.time) {
                cleanTime = ev.time.substring(0, 5);
            }
            const timeStr = cleanTime ? `${cleanTime}h` : "Time unconfirmed";
            
            ev.displayTime = isNaN(d.getTime()) ? timeStr : `${months[d.getMonth()]} ${d.getDate()} · ${timeStr}`;
            
            specialHtml += generateEventRowHTML(ev, true);
        });
        
        specialHtml += `</div>`;
        container.innerHTML += specialHtml;
    }

    const today = new Date();
    const dateRange = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        dateRange.push(date);
    }

    const vistos = new Set();
    filteredEvents = filteredEvents.filter(ev => {
        const idUnico = `${ev.title}-${ev.date}-${ev.comunity}`;
        if (vistos.has(idUnico)) return false;
        vistos.add(idUnico);
        return true;
    });

    filteredEvents.sort((a, b) => parseEventDate(a.date, a.time) - parseEventDate(b.date, b.time));

    const groupedEvents = {};
    dateRange.forEach(date => {
        const weekdayName = weekdays[date.getDay()];
        const dayNumber = date.getDate().toString().padStart(2, '0');
        const monthName = months[date.getMonth()];
        const groupingKey = `${weekdayName}, ${monthName} ${dayNumber}`;
        groupedEvents[groupingKey] = [];
    });

    filteredEvents.forEach(ev => {
        const parsedDateObj = parseEventDate(ev.date, ev.time);
        const weekdayName = isNaN(parsedDateObj.getTime()) ? "" : weekdays[parsedDateObj.getDay()];
        const dayNumber = isNaN(parsedDateObj.getTime()) ? "??" : parsedDateObj.getDate().toString().padStart(2, '0');
        const monthName = isNaN(parsedDateObj.getTime()) ? "??" : months[parsedDateObj.getMonth()];
        
        const groupingKey = weekdayName ? `${weekdayName}, ${monthName} ${dayNumber}` : "Date to be determined";

        if (!groupedEvents[groupingKey]) return;
        
        let cleanTime = null;
        if (ev.time) {
            cleanTime = ev.time.substring(0, 5);
        }
        ev.displayTime = cleanTime ? `${cleanTime}h` : "Time unconfirmed"; 
        
        groupedEvents[groupingKey].push(ev);
    });

    for (const [dayHeaderLabel, dailyEventsList] of Object.entries(groupedEvents)) {
        
        if (selectedFilter.toLowerCase() !== 'all' && dailyEventsList.length === 0) {
            continue; 
        }

        let regularHtml = `
            <div class="venue-block">
                <div class="venue-header" style="background-color: #24292f; color: #ffffff; border-bottom: none;">
                    <div class="icon-box" style="background-color: #3b4046; color: #ffffff;">📅</div>
                    <span>${dayHeaderLabel}</span>
                </div>
        `;
        
        if (dailyEventsList.length === 0) {
            regularHtml += `<p style="padding: 16px; color: #666; font-size: 14px; text-align: center; margin: 0;">No events scheduled</p>`;
        } else {
            dailyEventsList.forEach(ev => {
                regularHtml += generateEventRowHTML(ev);
            });
        }
        
        regularHtml += `</div>`;
        container.innerHTML += regularHtml;
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

loadAgenda();
