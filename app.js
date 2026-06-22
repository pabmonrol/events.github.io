let allData = []; 

async function cargarAgenda() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error(`No se encontró el archivo data.json`);
        allData = await response.json();
        
        renderizarEventos('all'); 
        configurarFiltros();      
    } catch (error) {
        const container = document.getElementById('agenda-container');
        container.innerHTML = `
            <div style="background: #ffebe9; border: 2px dashed #ff8182; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #cf222e; margin-top: 0;">🚨 Error al cargar la agenda</h3>
                <p style="color: #24292f;"><strong>Detalle:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function renderizarEventos(filtroSeleccionado) {
    const container = document.getElementById('agenda-container');
    container.innerHTML = ''; 

    // 🎯 FILTRADO: Mapeamos los botones en español con las categorías en inglés de Python
    let eventosFiltrados = allData.filter(ev => {
        if (filtroSeleccionado === 'all') return true;
        const cat = ev.category ? ev.category.toLowerCase() : '';
        
        if (filtroSeleccionado === 'deportes') return cat === 'sport';
        if (filtroSeleccionado === 'musica') return cat === 'music';
        if (filtroSeleccionado === 'cultura') return cat === 'culture';
        if (filtroSeleccionado === 'ocio') return cat === 'leisure';
        if (filtroSeleccionado === 'naturaleza') return cat === 'nature';
        
        return cat === filtroSeleccionado.toLowerCase();
    });

    if (eventosFiltrados.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 40px; color: #666; font-size: 14px;">No hay eventos disponibles en esta categoría.</p>`;
        return;
    }

    const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
    const diasSemana = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];

    // 📅 PARSER DE FECHAS: Convierte "2026-06-24" y "12:00" en un objeto Date real de JS
    function getFechaDeEvento(dateStr, timeStr) {
        if (!dateStr) return new Date(0);
        const horaPart = timeStr || "00:00";
        const [anio, mes, dia] = dateStr.split('-');
        const [hora, min] = horaPart.split(':');
        return new Date(anio, mes - 1, dia, hora, min);
    }

    // Ordenamos cronológicamente de forma estricta
    eventosFiltrados.sort((a, b) => getFechaDeEvento(a.date, a.time) - getFechaDeEvento(b.date, b.time));

    // Agrupamos los eventos por días para la interfaz limpia
    const eventosAgrupados = {};
    eventosFiltrados.forEach(ev => {
        const dateObj = getFechaDeEvento(ev.date, ev.time);

        const nombreDia = isNaN(dateObj.getTime()) ? "" : diasSemana[dateObj.getDay()];
        const diaNum = isNaN(dateObj.getTime()) ? "??" : dateObj.getDate().toString().padStart(2, '0');
        const mesNombre = isNaN(dateObj.getTime()) ? "??" : meses[dateObj.getMonth()];
        const horaStr = ev.time ? `${ev.time}h` : "Todo el día";

        const grupoKey = nombreDia ? `${nombreDia}, ${diaNum} ${mesNombre}` : "Fecha por determinar";

        if (!eventosAgrupados[grupoKey]) {
            eventosAgrupados[grupoKey] = [];
        }
        
        ev.displayDia = diaNum;
        ev.displayMes = mesNombre;
        ev.displayHora = horaStr;

        eventosAgrupados[grupoKey].push(ev);
    });

    // 🎨 RENDERIZADO PIXEL PERFECT
    for (const [diaTexto, eventosDelDia] of Object.entries(eventosAgrupados)) {
        let html = `
            <div class="venue-block">
                <div class="venue-header" style="background-color: #24292f; color: #ffffff; border-bottom: none;">
                    <div class="icon-box" style="background-color: #3b4046; color: #ffffff;">📅</div>
                    <span>${diaTexto}</span>
                </div>
        `;
        
        eventosDelDia.forEach(ev => {
            // Control de precios vacíos/gratuitos
            const precioDisplay = (ev.price === null || ev.price === 0) ? "Entrada gratuita" : `CHF ${ev.price}.-`;
            
            // Si el color de Python no existe en CSS, usamos 'blue' por defecto
            const temaColor = ev.colour || 'blue';

            // Generamos enlace rápido para guardar en Google Calendar
            const fechaFormateada = ev.date.replace(/-/g, '');
            const googleCalLink = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(ev.title)}&dates=${fechaFormateada}T000000Z/${fechaFormateada}T235959Z&details=${encodeURIComponent(ev.description || '')}&location=${encodeURIComponent(ev.location || '')}`;

            html += `
                <div class="event-row theme-${temaColor}">
                    <div class="event-row-main">
                        <div class="date-badge">
                            <span class="day">${ev.displayDia}</span>
                            <span class="month">${ev.displayMes}</span>
                        </div>
                        <div class="event-content">
                            <p class="event-title">${ev.icon || '📍'} ${ev.title}</p>
                            <p class="event-desc"><strong>${ev.displayHora}</strong> · ${ev.location || 'Lugar no especificado'}</p>
                            <span class="event-price">${precioDisplay}</span>
                        </div>
                        <div class="event-actions">
                            <a href="${googleCalLink}" class="cal-btn" target="_blank">+ Agenda</a>
                            ${ev.google_maps ? `<a href="${ev.google_maps}" class="loc-btn" target="_blank">📍 Cómo llegar</a>` : ''}
                            ${ev.description ? `
                                <button class="info-btn" onclick="toggleDetail(this)">
                                    Más info <i class="info-arrow">▾</i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    ${ev.description ? `
                        <div class="event-detail-panel">
                            <div class="event-detail-inner">
                                ${ev.description.replace(/\n/g, '<br>')}
                            </div>
                        </div>
                    ` : ''}
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