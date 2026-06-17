let allData = []; 

async function cargarAgenda() {
    const response = await fetch('data.json');
    allData = await response.json();
    
    renderizarEventos('all'); 
    configurarFiltros();      
}

function renderizarEventos(filtroSeleccionado) {
    const container = document.getElementById('agenda-container');
    container.innerHTML = ''; 

    // Filtramos los datos
    const datosParaMostrar = filtroSeleccionado === 'all' 
        ? allData 
        : allData.filter(venue => venue.category === filtroSeleccionado);

    // Pintamos los bloques
    datosParaMostrar.forEach(venue => {
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

function configurarFiltros() {
    const botones = document.querySelectorAll('.filter-btn');
    
    botones.forEach(boton => {
        boton.addEventListener('click', (e) => {
            botones.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            const filtro = e.target.getAttribute('data-filter');
            renderizarEventos(filtro);
        });
    });
}

cargarAgenda();
