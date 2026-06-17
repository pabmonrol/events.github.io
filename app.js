let allData = []; // Aquí guardaremos todo el JSON para no descargarlo varias veces

async function cargarAgenda() {
    const response = await fetch('data.json');
    allData = await response.json();
    
    renderizarEventos('all'); // Nada más cargar, mostramos 'Todos'
    configurarFiltros();      // Activamos los botones
}

function renderizarEventos(filtroSeleccionado) {
    const container = document.getElementById('agenda-container');
    container.innerHTML = ''; // Limpiamos la lista actual

    // Filtramos: Si es 'all', mostramos todo. Si no, solo los que coinciden con la categoría
    const datosParaMostrar = filtroSeleccionado === 'all' 
        ? allData 
        : allData.filter(venue => venue.category === filtroSeleccionado);

    // Pintamos los datos filtrados
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
            // 1. Quitamos el color azul (clase active) a todos los botones
            botones.forEach(b => b.classList.remove('active'));
            
            // 2. Le ponemos el color azul al botón que acabamos de pulsar
            e.target.classList.add('active');
            
            // 3. Leemos el "data-filter" de ese botón y renderizamos de nuevo
            const filtro = e.target.getAttribute('data-filter');
            renderizarEventos(filtro);
        });
    });
}

// Arrancar la aplicación
cargarAgenda();
