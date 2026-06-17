async function cargarAgenda() {
    const response = await fetch('data.json');
    const data = await response.json();
    const container = document.getElementById('agenda-container');

    data.forEach((venue, index) => {
        // Hacemos que el primer bloque (index 0) esté abierto por defecto
        let isOpenClass = index === 0 ? 'open' : '';

        let html = `
            <div class="venue-block theme-${venue.color} ${isOpenClass}">
                <div class="venue-header" onclick="toggleAcordeon(this)">
                    <div style="display: flex; align-items: center;">
                        <div class="icon-box">${venue.icon}</div>
                        <span>${venue.venue}</span>
                    </div>
                    <div class="toggle-icon">▼</div>
                </div>
                
                <div class="events-body">
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
        
        html += `
                </div> </div> `;
        
        container.innerHTML += html;
    });
}

// Función súper sencilla para abrir y cerrar (añade o quita la clase 'open')
function toggleAcordeon(elemento) {
    const bloque = elemento.parentElement;
    bloque.classList.toggle('open');
}

cargarAgenda();
