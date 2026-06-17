async function cargarAgenda() {
    const response = await fetch('data.json');
    const data = await response.json();
    const container = document.getElementById('agenda-container');

    data.forEach(venue => {
        // Usamos la clase venue-block y venue-header de tu style.css
        let html = `
            <div class="venue-block">
                <div class="venue-header">
                    <span style="margin-right: 10px;">${venue.icon}</span>
                    <span>${venue.venue}</span>
                </div>
            `;
        
        venue.events.forEach(ev => {
            // Usamos las clases event-row, date-badge, event-content, etc. de tu style.css
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
