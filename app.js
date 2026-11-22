let allEventsData = [];
let specialEventsData = [];
let agendaIsStale = false;
let latestEventLabel = "";
let freeOnly = false;
let activeTown = null;
let searchQuery = "";

function markAgendaFreshness() {
    const dated = [...allEventsData, ...specialEventsData]
        .map(ev => parseEventDate(ev.date, "00:00"))
        .filter(d => !isNaN(d.getTime()) && d.getTime() !== 0);
    if (dated.length === 0) {
        agendaIsStale = false;
        return;
    }
    const latest = new Date(Math.max(...dated.map(d => d.getTime())));
    latestEventLabel = `${weekdays[latest.getDay()]}, ${months[latest.getMonth()]} ${latest.getDate()}`;
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    agendaIsStale = latest < startOfToday;
}

async function loadAgenda() {
    try {
        const response = await fetch("data/data.json");
        if (!response.ok) throw new Error("Could not retrieve data/data.json file");
        allEventsData = await response.json();

        try {
            const specialResponse = await fetch("data/data_special.json");
            if (specialResponse.ok) {
                specialEventsData = await specialResponse.json();
            }
        } catch (error) {
            console.log("No data_special.json found. Skipping featured events.");
        }

        const allCombined = [...allEventsData, ...specialEventsData];
        const activeCategories = new Set(allCombined.map(ev => ev.category ? ev.category.toLowerCase() : ""));

        document.querySelectorAll(".filter-btn").forEach(button => {
            const filterValue = button.getAttribute("data-filter");
            if (filterValue !== "all" && !activeCategories.has(filterValue.toLowerCase())) {
                button.style.display = "none";
            } else {
                button.style.display = "";
            }
        });

        markAgendaFreshness();
        renderEvents("all");
        setupFilterListeners();
        const upto = document.getElementById("data-upto");
        if (upto) upto.textContent = latestEventLabel ? `Agenda data up to ${latestEventLabel}` : "";
    } catch (error) {
        const container = document.getElementById("agenda-container");
        container.innerHTML = `
            <div style="background: #ffebe9; border: 2px dashed #ff8182; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #cf222e; margin-top: 0;">🚨 Error loading agenda</h3>
                <p style="color: #24292f;"><strong>Details:</strong> ${error.message}</p>
            </div>
        `;
    }
}

const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const CONTENT_LANGS = [
    { code: "en", short: "EN" },
    { code: "es", short: "ES" },
    { code: "it", short: "IT" },
    { code: "de", short: "DE" },
    { code: "sr", short: "SR" },
    { code: "fr", short: "FR" },
    { code: "pt", short: "PT" },
    { code: "pl", short: "PL" },
    { code: "hi", short: "HI" },
    { code: "ru", short: "RU" },
];
const LANG_STORAGE_KEY = "agenda-content-langs";
const LANG_SHORT = Object.fromEntries(CONTENT_LANGS.map(lang => [lang.code, lang.short]));

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function selectedLangCodes() {
    const codes = [...document.querySelectorAll(".lang-btn.active")].map(btn => btn.getAttribute("data-lang"));
    return codes.length ? [...new Set(codes)] : ["en"];
}

function fieldText(field, code) {
    if (field == null || field === "") return "";
    if (typeof field === "string") return code === "en" ? field : "";
    if (typeof field === "object") return field[code] || "";
    return "";
}

function selectedFieldParts(field) {
    const seenTexts = new Set();
    return selectedLangCodes()
        .map(code => ({ code, text: fieldText(field, code) }))
        .filter(part => part.text)
        .filter(part => {
            const key = part.text.trim().toLowerCase();
            if (seenTexts.has(key)) return false;
            seenTexts.add(key);
            return true;
        });
}

function plainField(field) {
    const parts = selectedFieldParts(field);
    return parts.length ? parts[0].text : "";
}

function englishField(field) {
    return fieldText(field, "en");
}

function eventUniqueKey(ev) {
    const titles = (ev.title && typeof ev.title === "object")
        ? Object.values(ev.title).map(v => String(v).trim().toLowerCase()).join("|")
        : String(ev.title || "").trim().toLowerCase();
    return `${titles}-${ev.date || ""}-${ev.time || ""}-${(ev.community || "").trim().toLowerCase()}`;
}

function htmlField(field) {
    const parts = selectedFieldParts(field);
    if (parts.length === 0) return "";
    if (parts.length === 1) {
        return escapeHtml(parts[0].text).replace(/\n/g, "<br>");
    }
    return parts.map(part => {
        const body = escapeHtml(part.text).replace(/\n/g, "<br>");
        return `<span class="lang-line"><span class="lang-code">${LANG_SHORT[part.code] || ""}</span> ${body}</span>`;
    }).join("");
}

function locationWithTown(eventItem, emptyLabel) {
    const town = (eventItem.community || "").trim();
    const place = (eventItem.location || "").trim();
    if (!place) return town || emptyLabel;
    if (!town || place.toLowerCase().includes(town.toLowerCase())) return place;
    return `${place}, ${town}`;
}

function activeCategory() {
    const active = document.querySelector(".filter-btn.active[data-filter]");
    return active ? active.getAttribute("data-filter") : "all";
}

function matchesSearch(ev) {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const hay = selectedLangCodes()
        .map(code => `${fieldText(ev.title, code)} ${fieldText(ev.description, code)}`)
        .join(" ") + ` ${ev.location || ""} ${ev.community || ""}`;
    return hay.toLowerCase().includes(q);
}

function passesExtraFilters(ev) {
    if (freeOnly && !(ev.price === null || ev.price === 0)) return false;
    if (activeTown && (ev.community || "").trim().toLowerCase() !== activeTown.toLowerCase()) return false;
    return matchesSearch(ev);
}

function setupLangFilters() {
    let saved = ["en"];
    try {
        const parsed = JSON.parse(localStorage.getItem(LANG_STORAGE_KEY));
        if (Array.isArray(parsed)) {
            const known = new Set(CONTENT_LANGS.map(lang => lang.code));
            const picked = parsed.filter(code => known.has(code));
            if (picked.length) saved = [picked[picked.length - 1]];
        }
    } catch (error) {
        saved = ["en"];
    }

    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.classList.toggle("active", saved.includes(btn.getAttribute("data-lang")));
        btn.addEventListener("click", () => {
            const lang = btn.getAttribute("data-lang");
            document.querySelectorAll(".lang-btn").forEach(other => other.classList.toggle("active", other.getAttribute("data-lang") === lang));
            localStorage.setItem(LANG_STORAGE_KEY, JSON.stringify(selectedLangCodes()));
            renderEvents(activeCategory());
        });
    });
}

function parseEventDate(dateString, timeString) {
    if (!dateString) return new Date(0);
    const timePart = timeString || "00:00";
    const [year, month, day] = dateString.split("-");
    const [hours, minutes] = timePart.split(":");
    return new Date(year, month - 1, day, hours, minutes);
}

function calendarTimeBounds(timeString) {
    const start = timeString.replace(/:/g, "").substring(0, 4) + "00";
    const [h, m] = timeString.split(":").map(Number);
    const end = ((h + 1) % 24).toString().padStart(2, "0") + m.toString().padStart(2, "0") + "00";
    return { start, end };
}

function buildCalendarLink(eventItem, cleanDateString, title, description, location) {
    const isAppleDevice = /Mac|iPod|iPhone|iPad/.test(navigator.platform) || /Macintosh|iPhone|iPad|iPod/.test(navigator.userAgent);

    if (isAppleDevice) {
        let icsContent = `BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:${title}\n`;
        if (eventItem.time) {
            const bounds = calendarTimeBounds(eventItem.time);
            icsContent += `DTSTART:${cleanDateString}T${bounds.start}\n`;
            icsContent += `DTEND:${cleanDateString}T${bounds.end}\n`;
        } else {
            icsContent += `DTSTART;VALUE=DATE:${cleanDateString}\n`;
        }
        icsContent += `LOCATION:${location}\n`;
        icsContent += `DESCRIPTION:${description.replace(/\n/g, "\\n")}\n`;
        icsContent += `END:VEVENT\nEND:VCALENDAR`;
        const ics = icsContent.replace(/\n/g, "\r\n");
        return { url: `data:text/calendar;charset=utf8,${encodeURIComponent(ics)}`, label: "+ Apple Cal" };
    }

    let timeSuffix = "T000000/T235959";
    if (eventItem.time) {
        const bounds = calendarTimeBounds(eventItem.time);
        timeSuffix = `T${bounds.start}/T${bounds.end}`;
    }
    const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${cleanDateString}${timeSuffix}&details=${encodeURIComponent(description)}&location=${encodeURIComponent(location)}`;
    return { url, label: "+ Google Cal" };
}

function generateEventRowHTML(eventItem, isSpecial = false) {
    const town = (eventItem.community || "").toLowerCase();
    const place = (eventItem.location || "").toLowerCase();
    const priceNotSpecified = ["ruggell", "schellenberg", "triesen"].some(name => town.includes(name) || place.includes(name));

    let priceLabel;
    if (priceNotSpecified) {
        priceLabel = "Not specified";
    } else {
        priceLabel = (eventItem.price === null || eventItem.price === 0) ? "Free admission" : `CHF ${eventItem.price}.-`;
    }

    const colorThemeClass = eventItem.colour || "blue";
    const cleanDateString = eventItem.date ? eventItem.date.replace(/-/g, "") : "";
    const calendarLocation = locationWithTown(eventItem, "");
    const visibleLocation = locationWithTown(eventItem, "Location not specified");
    const calendarTitle = plainField(eventItem.title);
    const calendarDescription = plainField(eventItem.description);
    const titleHtml = htmlField(eventItem.title);
    const descriptionHtml = htmlField(eventItem.description);
    const calendar = buildCalendarLink(eventItem, cleanDateString, calendarTitle, calendarDescription, calendarLocation);
    const specialClass = isSpecial ? "special-event" : "";

    return `
        <div class="event-row theme-${colorThemeClass} ${specialClass}">
            <div class="event-row-main">
                <div class="event-content">
                    <p class="event-title"><span class="event-icon">${eventItem.icon || '📍'}</span> ${titleHtml}</p>
                    <p class="event-desc"><span class="event-time">🕒 ${eventItem.displayTime}</span><span class="event-loc">${escapeHtml(visibleLocation)}</span></p>
                    <span class="event-price">${priceLabel}</span>
                </div>
                <div class="event-actions">
                    <a href="${calendar.url}" class="cal-btn" target="_blank">${calendar.label}</a>
                    ${eventItem.google_maps ? `<a href="${eventItem.google_maps}" class="loc-btn" target="_blank">📍 Maps</a>` : ""}
                    ${descriptionHtml ? `
                        <button class="info-btn" onclick="toggleDetail(this)">
                            More info <i class="info-arrow">▾</i>
                        </button>
                    ` : ""}
                </div>
            </div>
            ${descriptionHtml ? `
                <div class="event-detail-panel">
                    <div class="event-detail-inner">
                        ${descriptionHtml}
                    </div>
                </div>
            ` : ""}
        </div>`;
}

function venueBlockHtml(headerColor, iconColor, icon, label, bodyHtml, extraAttrs = "", badge = "") {
    return `
        <div class="venue-block"${extraAttrs}>
            <div class="venue-header" style="background-color: ${headerColor}; color: #ffffff; border-bottom: none;">
                <div class="icon-box" style="background-color: ${iconColor}; color: #ffffff;">${icon}</div>
                <span>${label}</span>${badge}
            </div>
            ${bodyHtml}
        </div>`;
}

function renderEvents(selectedFilter) {
    const container = document.getElementById("agenda-container");
    const htmlParts = [];

    if (agendaIsStale) {
        htmlParts.push(`
            <div style="background: #fff8c5; border: 2px dashed #d4a72c; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #9a6700; margin-top: 0;">Agenda data is out of date</h3>
                <p style="color: #24292f; margin-bottom: 0;">The newest saved event is before today, so this week looks empty.</p>
            </div>
        `);
    }

    let filteredEvents = allEventsData.filter(ev =>
        (selectedFilter === "all" || (ev.category && ev.category.toLowerCase() === selectedFilter.toLowerCase())) &&
        passesExtraFilters(ev)
    );
    const normalKeys = new Set(allEventsData.map(eventUniqueKey));
    const filteredSpecial = selectedFilter === "all"
        ? specialEventsData.filter(ev => passesExtraFilters(ev) && !normalKeys.has(eventUniqueKey(ev)))
        : [];

    const today = new Date();
    const dateRange = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        dateRange.push(date);
    }
    const rangeKeys = new Set(dateRange.map(d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`));
    const baseForCounts = allEventsData.filter(ev =>
        (selectedFilter === "all" || (ev.category && ev.category.toLowerCase() === selectedFilter.toLowerCase())) &&
        ev.date && rangeKeys.has(ev.date) && matchesSearch(ev)
    );
    updateExtraRail(baseForCounts, filteredEvents.length + filteredSpecial.length);

    if (filteredEvents.length === 0 && filteredSpecial.length === 0) {
        container.innerHTML = `<p style="text-align:center; padding: 40px; color: #666; font-size: 14px;">No events available in this category.</p>`;
        return;
    }

    if (filteredSpecial.length > 0) {
        filteredSpecial.sort((a, b) => parseEventDate(a.date, a.time) - parseEventDate(b.date, b.time));
        
        let specialBody = "";
        filteredSpecial.forEach(ev => {
            const d = parseEventDate(ev.date, ev.time);
            const cleanTime = ev.time ? ev.time.substring(0, 5) : null;
            const timeStr = cleanTime ? `${cleanTime}h` : "Time unconfirmed";
            ev.displayTime = isNaN(d.getTime()) ? timeStr : `${months[d.getMonth()]} ${d.getDate()} · ${timeStr}`;
            specialBody += generateEventRowHTML(ev, true);
        });

        htmlParts.push(venueBlockHtml("#D20000", "#a30000", "⭐", "Featured Events", specialBody));
    }

    const seen = new Set();
    filteredEvents = filteredEvents.filter(ev => {
        const uniqueId = eventUniqueKey(ev);
        if (seen.has(uniqueId)) return false;
        seen.add(uniqueId);
        return true;
    });

    filteredEvents.sort((a, b) => parseEventDate(a.date, a.time) - parseEventDate(b.date, b.time));

    const groupedEvents = {};
    dateRange.forEach(date => {
        const groupingKey = `${weekdays[date.getDay()]}, ${months[date.getMonth()]} ${date.getDate().toString().padStart(2, "0")}`;
        groupedEvents[groupingKey] = [];
    });

    filteredEvents.forEach(ev => {
        const parsedDate = parseEventDate(ev.date, ev.time);
        const validDate = !isNaN(parsedDate.getTime());
        const weekdayName = validDate ? weekdays[parsedDate.getDay()] : "";
        const dayNumber = validDate ? parsedDate.getDate().toString().padStart(2, "0") : "??";
        const monthName = validDate ? months[parsedDate.getMonth()] : "??";
        const groupingKey = weekdayName ? `${weekdayName}, ${monthName} ${dayNumber}` : "Date to be determined";

        if (!groupedEvents[groupingKey]) return;

        const cleanTime = ev.time ? ev.time.substring(0, 5) : null;
        ev.displayTime = cleanTime ? `${cleanTime}h` : "Time unconfirmed";

        groupedEvents[groupingKey].push(ev);
    });

    let dayIndex = 0;
    for (const [dayHeaderLabel, dailyEventsList] of Object.entries(groupedEvents)) {
        const isToday = dayIndex === 0;
        const dayId = dayIndex;
        dayIndex++;

        if (selectedFilter.toLowerCase() !== 'all' && dailyEventsList.length === 0) {
            continue; 
        }

        let regularHtml = `
            <div class="venue-block">
                <div class="venue-header venue-header--day">
                    <div class="icon-box icon-box--day">📅</div>
                    <span>${dayHeaderLabel}</span>${isToday ? ' <span class="today-badge">Today</span>' : ''}
                </div>
        `;
        
        let dayBody;
        if (dailyEventsList.length === 0) {
            dayBody = `<p style="padding: 16px; color: #666; font-size: 14px; text-align: center; margin: 0;">No events scheduled</p>`;
        } else {
            dayBody = dailyEventsList.map(ev => generateEventRowHTML(ev)).join("");
        }

        htmlParts.push(venueBlockHtml("#24292f", "#3b4046", "📅", dayHeaderLabel, dayBody, ` id="agenda-day-${dayId}"`, isToday ? ' <span class="today-badge">Today</span>' : ""));
    }

    container.innerHTML = htmlParts.join("");
}

function setupFilterListeners() {
    const filterButtons = document.querySelectorAll(".filter-btn");
    filterButtons.forEach(button => {
        button.addEventListener("click", (clickEvent) => {
            const activeFilterQuery = clickEvent.currentTarget.getAttribute("data-filter");
            filterButtons.forEach(btn => btn.classList.toggle("active", btn.getAttribute("data-filter") === activeFilterQuery));
            renderEvents(activeFilterQuery);
        });
    });
}

function updateExtraRail(baseForCounts, totalShown) {
    const freeBtn = document.getElementById("rail-free");
    const freeCount = document.getElementById("rail-free-count");
    if (freeBtn && freeCount) {
        freeCount.textContent = baseForCounts.filter(ev => ev.price === null || ev.price === 0).length;
        freeBtn.classList.toggle("active", freeOnly);
    }
    const townsEl = document.getElementById("rail-towns");
    if (townsEl) {
        const counts = {};
        baseForCounts.forEach(ev => {
            const town = (ev.community || "").trim();
            if (town) counts[town] = (counts[town] || 0) + 1;
        });
        const entries = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
        townsEl.innerHTML =
            `<button type="button" class="rail-day${activeTown ? "" : " active"}" data-town=""><span>All towns</span></button>` +
            entries.map(([town, n]) =>
                `<button type="button" class="rail-day${activeTown === town ? " active" : ""}" data-town="${escapeHtml(town)}"><span>${escapeHtml(town)}</span><span class="rail-count">${n}</span></button>`
            ).join("");
        townsEl.querySelectorAll(".rail-day").forEach(btn => {
            btn.addEventListener("click", () => {
                activeTown = btn.getAttribute("data-town") || null;
                renderEvents(activeCategory());
            });
        });
    }
    const searchCount = document.getElementById("rail-search-count");
    if (searchCount) {
        searchCount.textContent = searchQuery ? `${totalShown} result${totalShown === 1 ? "" : "s"}` : "";
    }
}

function setupRailControls() {
    const search = document.getElementById("rail-search");
    if (search) search.addEventListener("input", () => {
        searchQuery = search.value.trim();
        renderEvents(activeCategory());
    });
    const freeBtn = document.getElementById("rail-free");
    if (freeBtn) freeBtn.addEventListener("click", () => {
        freeOnly = !freeOnly;
        renderEvents(activeCategory());
    });
}

function toggleDetail(btn) {
    const row = btn.closest(".event-row");
    const panel = row.querySelector(".event-detail-panel");
    const isOpen = panel.classList.contains("open");

    panel.classList.toggle("open", !isOpen);
    btn.classList.toggle("expanded", !isOpen);
    btn.querySelector(".info-arrow").textContent = isOpen ? "▾" : "▴";
}

setupLangFilters();
setupRailControls();
loadAgenda();
