let allEventsData = []; 

async function loadAgenda() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error(`Could not retrieve data.json file`);
        allEventsData = await response.json();
        
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

function renderEvents(selectedFilter) {
    const container = document.getElementById('agenda-container');
    container.innerHTML = ''; 

    // 🎯 FILTERING LOGIC
    let filteredEvents = allEventsData.filter(eventItem => {
        if (selectedFilter === 'all') return true;
        const categoryString = eventItem.category ? eventItem.category.toLowerCase() : '';
        return categoryString === selectedFilter.toLowerCase();
    });

    if (filteredEvents.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 40px; color: #666; font-size: 14px;">No events available in this category.</p>`;
        return;
    }

    // 📅 ENGLISH DATE ARRAYS FOR FORMATTING
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

    // TIMESTAMP PARSER FOR SORTING
    function parseEventDate(dateString, timeString) {
        if (!dateString) return new Date(0);
        const timePart = timeString || "00:00";
        const [year, month, day] = dateString.split('-');
        const [hours, minutes] = timePart.split(':');
        return new Date(year, month - 1, day, hours, minutes);
    }

    // CHRONOLOGICAL SORTING
    filteredEvents.sort((eventA, eventB) => parseEventDate(eventA.date, eventA.time) - parseEventDate(eventB.date, eventB.time));

    // GROUPING EVENTS BY DAY
    const groupedEvents = {};
    filteredEvents.forEach(eventItem => {
        const parsedDateObj = parseEventDate(eventItem.date, eventItem.time);

        const weekdayName = isNaN(parsedDateObj.getTime()) ? "" : weekdays[parsedDateObj.getDay()];
        const dayNumber = isNaN(parsedDateObj.getTime()) ? "??" : parsedDateObj.getDate().toString().padStart(2, '0');
        const monthName = isNaN(parsedDateObj.getTime()) ? "??" : months[parsedDateObj.getMonth()];
        const formattedTime = eventItem.time ? `${eventItem.time}h` : "All day";

        const groupingKey = weekdayName ? `${weekdayName}, ${monthName} ${dayNumber}` : "Date to be determined";

        if (!groupedEvents[groupingKey]) {
            groupedEvents[groupingKey] = [];
        }
        
        eventItem.displayTime = formattedTime;
        groupedEvents[groupingKey].push(eventItem);
    });

    // 🎨 DYNAMIC DOM RENDERING
    for (const [dayHeaderLabel, dailyEventsList] of Object.entries(groupedEvents)) {
        let blockHtml = `
            <div class="venue-block">
                <div class="venue-header" style="background-color: #24292f; color: #ffffff; border-bottom: none;">
                    <div class="icon-box" style="background-color: #3b4046; color: #ffffff;">📅</div>
                    <span>${dayHeaderLabel}</span>
                </div>
        `;
        
        dailyEventsList.forEach(eventItem => {
            const priceLabel = (eventItem.price === null || eventItem.price === 0) ? "Free admission" : `CHF ${eventItem.price}.-`;
            const colorThemeClass = eventItem.colour || 'blue';

            // Google Calendar Generation
            const cleanDateString = eventItem.date.replace(/-/g, '');
            const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(eventItem.title)}&dates=${cleanDateString}T000000Z/${cleanDateString}T235959Z&details=${encodeURIComponent(eventItem.description || '')}&location=${encodeURIComponent(eventItem.location || '')}`;

            blockHtml += `
                <div class="event-row theme-${colorThemeClass}">
                    <div class="event-row-main">
                        <div class="event-content">
                            <p class="event-title">${eventItem.icon || '📍'} ${eventItem.title}</p>
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
        });
        
        blockHtml += `</div>`;
        container.innerHTML += blockHtml;
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