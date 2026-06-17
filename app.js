let allData = []; 

async function cargarAgenda() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error(`No se encontró el archivo data.json`);
        allData = await response.json();
        
        renderizarEventos('all'); 
        configurarFiltros();      
    } catch (error) {
        // Detector de errores
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

    // 1. EXTRAER TODOS LOS EVENTOS (y guardarles la info de su lugar y color)
    let eventosFiltrados = [];
    allData.forEach(venue => {
        if (filtroSeleccionado === 'all' || venue.category === filtroSeleccionado) {
            venue.events.forEach(ev => {
                eventosFiltrados.push({
                    ...ev,
                    venueName: venue.venue,
                    venueIcon: venue.icon,
                    venueColor: venue.color // Azul o Verde
                });
            });
        }
    });

    if (eventosFiltrados.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 20px; color: #666;">No hay eventos en esta categoría.</p>`;
        return;
    }

    // 2. ORDENAR CRONOLÓGICAMENTE Y AGRUPAR POR DÍA
    const meses = { "Ene": 0, "Feb": 1, "Mar": 2, "Abr": 3, "May": 4, "Jun": 5, "Jul": 6, "Ago": 7, "Sep": 8, "Oct": 9, "Nov": 10, "Dic": 11 };
    const diasSemana = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
    const currentYear = new Date().getFullYear();

    // Función auxiliar para obtener una Fecha real de JavaScript
    function getFechaDeEvento(ev) {
        // Limpiamos el mes por si acaso (ej: "jul" -> "Jul")
        const mesLimpio = ev.month.charAt(0).toUpperCase() + ev.month.slice(1, 3).toLowerCase();
        const monthIndex = meses[mesLimpio] !== undefined ? meses[mesLimpio] : 0;
        return new Date(currentYear, monthIndex, parseInt(ev.day));
    }

    // Ordenamos los eventos por fecha para que salgan en orden en la agenda
    eventosFiltrados.sort((a, b) => getFechaDeEvento(a) - getFechaDeEvento(b));

    // Agrupamos los eventos bajo su fecha
    const eventosAgrupados = {};
    eventosFiltrados.forEach(ev => {
        const date = getFechaDeEvento(ev);
        const nombreDia = isNaN(date.getTime()) ? "" : diasSemana[date.getDay()];
        
        // Creamos el Título del bloque (Ej: "Viernes, 12 Jul")
        const grupoKey = nombreDia ? `${nombreDia}, ${ev.day} ${ev.month}` : `${ev.day} ${ev.month}`;
        
        if (!eventosAgrupados[grupoKey]) {
            eventosAgrupados[grupoKey] = [];
        }
        eventosAgrupados[grupoKey].push(ev);
    });

    // 3. PINTAR LOS BLOQUES EN PANTALLA
    for (const [diaTexto, eventosDelDia] of Object.entries(eventosAgrupados)) {
        
        // El bloque principal ahora es un "DÍA" (le ponemos un gris elegante para la cabecera)
        let html = `
            <div class="venue-block">
                <div class="venue-header" style="background-color: #24292f; color: #ffffff; border-bottom: none;">
                    <div class="icon-box" style="background-color: #3b4046; color: #ffffff;">📅</div>
                    <span>${diaTexto}</span>
                </div>
            `;
        
        eventosDelDia.forEach(ev => {
            // A cada evento le aplicamos SU PROPIO TEMA (Azul, Verde...) y le añadimos su estadio/sala en la descripción
            html += `
                <div class="event-row theme-${ev.venueColor}">
                    <div class="date-badge">
                        <span class="day">${ev.day}</span>
                        <span class="month">${ev.month}</span>
                    </div>
                    <div class="event-content">
                        <p class="event-title">${ev.venueIcon} ${ev.title}</p>
                        <p class="event-desc"><strong>${ev.venueName}</strong> · ${ev.desc}</p>
                        <span class="event-price">${ev.price}</span>
                    </div>
                    <a href="${ev.calLink || '#'}" class="cal-btn">+ Añadir</a>
                </div>`;
        });
        
        html += `</div>`;
        container.innerHTML += html;
    }
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
