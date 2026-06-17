async function cargarAgenda() {
    const response = await fetch('data.json');
    const data = await response.json();
    const container = document.getElementById('agenda-container');

    data.forEach(venue => {
        // Asignamos la clase theme-${venue.color} (ej: theme-blue)
        let html = `
            <div class="venue-block theme-${venue.color}">
                <div class="venue-header">
                    <div class="icon-box">${venue.icon}</div>
                    <span>${venue.venue}</span>
                </div>
            `;
        
        venue.events.forEach(ev => {
            html += `
                <div class="event-row">
                    <div class="date-badge">
                        <span class="day">${ev.day}</span>
                        <span class="month">${ev.month}</span>
                    </div>
                    <div class="event-content">
                        <p class="event-title">${ev.title}</p>
                        <p class="event-desc">${ev.desc}</p>
                        <span class="event-price">${ev.price}</span>
                    </div>
                    <a href="${ev.calLink || '#'}" class="cal-btn">+ Añadir</a>
                </div>`;
        });
        
        html += `</div>`;
        container.innerHTML += html;
    });
}

cargarAgenda();
