async function cargarAgenda() {
    const response = await fetch('data.json');
    const data = await response.json();
    const container = document.getElementById('agenda-container');

    data.forEach(venue => {
        let html = `
            <div class="venue-block p-3 border-bottom">
                <div class="d-flex align-items-center mb-3">
                    <span class="me-2">${venue.icon}</span>
                    <strong class="text-${venue.color}">${venue.venue}</strong>
                </div>
            `;
        
        venue.events.forEach(ev => {
            html += `
                <div class="row align-items-center mb-3">
                    <div class="col-auto text-center bg-light p-2 rounded">
                        <div class="fw-bold">${ev.day}</div>
                        <small class="text-uppercase">${ev.month}</small>
                    </div>
                    <div class="col">
                        <div class="fw-bold">${ev.title}</div>
                        <small class="text-muted">${ev.desc}</small>
                        <div class="text-success small fw-bold">${ev.price}</div>
                    </div>
                    <div class="col-auto">
                        <a href="${ev.calLink}" class="btn btn-sm btn-primary">+ Agenda</a>
                    </div>
                </div>`;
        });
        
        html += `</div>`;
        container.innerHTML += html;
    });
}

cargarAgenda();