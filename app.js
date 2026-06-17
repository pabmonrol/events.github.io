let allData = []; 

// 1. Diccionario para traducir el mes de texto a número
const meses = {
    "Ene": 0, "Feb": 1, "Mar": 2, "Abr": 3, "May": 4, "Jun": 5, 
    "Jul": 6, "Ago": 7, "Sep": 8, "Oct": 9, "Nov": 10, "Dic": 11
};

// 2. Función que convierte "12" y "Jul" en una fecha matemática ordenable
function convertirAFecha(dia, mes) {
    const añoActual = new Date().getFullYear(); // Usa el año actual
    return new Date(añoActual, meses[mes], parseInt(dia)).getTime();
}

async function cargarAgenda() {
    try {
        const response = await fetch('data.json');
        
        if (!response.ok) {
            throw new Error(`No se encontró el archivo data.json (Error ${response.status})`);
        }

        let datosBrutos = await response.json();
        
        // ==========================================
        // 🚀 MAGIA DE ORDENACIÓN CRONOLÓGICA
        // ==========================================
        
        // Paso A: Ordenar los eventos cronológicamente dentro de cada lugar
        datosBrutos.forEach(venue => {
            venue.events.sort((a, b) => convertirAFecha(a.day, a.month) - convertirAFecha(b.day, b.month));
        });

        // Paso B: Ordenar las cajas de los lugares (El lugar con el evento más cercano va primero)
        datosBrutos.sort((a, b) => {
            const primerEventoA = convertirAFecha(a.events[0].day, a.events[0].month);
            const primerEventoB = convertirAFecha(b.events[0].day, b.events[0].month);
            return primerEventoA - primerEventoB;
        });
        
        // Guardamos los datos ya ordenados para usarlos en los filtros
        allData = datosBrutos;
        
        // ==========================================

        renderizarEventos('all'); 
        configurarFiltros();      

    } catch (error) {
        // Caja roja de error por si algo falla
        const container = document.getElementById('agenda-container');
        container.innerHTML = `
            <div style="background: #ffebe9; border: 2px dashed #ff8182; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #cf222e; margin-top: 0;">🚨 El JavaScript se ha bloqueado</h3>
                <p style="color: #24292f;"><strong>Detalle del error:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function renderizarEventos(filtroSeleccionado) {
    const container = document.getElementById('agenda-container');
    container.innerHTML = ''; 

    // Filtramos los datos que ya están ordenados en memoria
    const datosParaMostrar = filtroSeleccionado === 'all' 
        ? allData 
        : allData.filter(venue => venue.category === filtroSeleccionado);

    if (datosParaMostrar.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 20px; color: #666;">No hay eventos en esta categoría.</p>`;
        return;
    }

    // Dibujamos el HTML
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
            
            const botonPulsado = e.currentTarget;
            botonPulsado.classList.add('active');
            
            const filtro = botonPulsado.getAttribute('data-filter');
            renderizarEventos(filtro);
        });
    });
}

cargarAgenda();
