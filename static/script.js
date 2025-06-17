document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('searchButton');
    const searchQuery = document.getElementById('searchQuery');
    const preferredAirlines = document.getElementById('preferredAirlines');
    const maxStops = document.getElementById('maxStops');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const results = document.getElementById('results');

    searchButton.addEventListener('click', async function() {
        // Clear previous results and errors
        errorMessage.classList.add('d-none');
        results.classList.add('d-none');
        loadingIndicator.classList.remove('d-none');

        // Prepare filters
        const filters = {};
        if (preferredAirlines.value) {
            filters.preferred_airlines = preferredAirlines.value.split(',').map(airline => airline.trim());
        }
        if (maxStops.value !== '') {
            filters.max_stops = parseInt(maxStops.value);
        }

        try {
            const response = await fetch('/api/search/natural', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: searchQuery.value,
                    filters: filters
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'An error occurred while searching for flights');
            }

            if (data.error) {
                throw new Error(data.error);
            }

            displayResults(data);
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.classList.remove('d-none');
        } finally {
            loadingIndicator.classList.add('d-none');
        }
    });

    function displayResults(data) {
        // Clear previous results
        document.getElementById('cheapestFlights').innerHTML = '';
        document.getElementById('fastestFlights').innerHTML = '';
        document.getElementById('optimalFlights').innerHTML = '';

        // Display results
        if (data.results) {
            displayFlightSection('cheapestFlights', data.results.cheapest.cheapest);
            displayFlightSection('fastestFlights', data.results.fastest.fastest);
            displayFlightSection('optimalFlights', data.results.optimal.optimal);
            results.classList.remove('d-none');
        }
    }

    function displayFlightSection(sectionId, flights) {
        const section = document.getElementById(sectionId);
        
        if (!flights || flights.length === 0) {
            section.innerHTML = '<p class="text-muted">No flights found</p>';
            return;
        }

        flights.forEach(flight => {
            const card = createFlightCard(flight);
            section.appendChild(card);
        });
    }

    function createFlightCard(flight) {
        const card = document.createElement('div');
        card.className = 'flight-card';

        // Helper to format time
        function formatTime(isoString) {
            if (!isoString) return '';
            const d = new Date(isoString);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        // Helper to format duration
        function formatDuration(mins) {
            if (typeof mins !== 'number') return '';
            const h = Math.floor(mins / 60);
            const m = mins % 60;
            return `${h}h ${m}m`;
        }

        // Helper to format stops
        function formatStops(stops) {
            if (stops === 0) return 'Non-stop';
            if (stops === 1) return '1 stop';
            return `${stops} stops`;
        }

        // Outbound leg details
        function renderLeg(leg, label) {
            if (!leg) return '';
            return `
                <div class="leg-section">
                    <div class="leg-label"><strong>${label}</strong></div>
                    <div class="airline">
                        ${leg.airline && leg.airline.logo ? `<img src="${leg.airline.logo}" alt="${leg.airline.name}" class="airline-logo" />` : ''}
                        ${leg.airline ? `${leg.airline.name} (${leg.airline.code || ''})` : ''}
                    </div>
                    <div class="details">
                        <div class="time">${formatTime(leg.departure && leg.departure.time)} → ${formatTime(leg.arrival && leg.arrival.time)}</div>
                        <div class="route">${leg.departure && leg.departure.airport ? leg.departure.airport.code : ''} → ${leg.arrival && leg.arrival.airport ? leg.arrival.airport.code : ''}</div>
                        <div class="duration">${formatDuration(leg.duration)}</div>
                        <div class="stops">${formatStops(leg.stops)}</div>
                        <div class="flight-number">Flight ${leg.flight_number || ''}</div>
                    </div>
                    ${leg.layover_times && leg.layover_times.length > 0 ? `<div class="layovers">${leg.layover_times.map(layover => `Layover: ${formatDuration(layover)}`).join('<br>')}</div>` : ''}
                </div>
            `;
        }

        let cardContent = `<div class="price">${flight.price && flight.price.formatted ? flight.price.formatted : flight.price}</div>`;

        if (flight.trip_type === 'round_trip' && flight.outbound && flight.inbound) {
            cardContent += renderLeg(flight.outbound, 'Outbound');
            cardContent += renderLeg(flight.inbound, 'Inbound');
        } else if (flight.outbound) {
            cardContent += renderLeg(flight.outbound, 'Flight');
        } else {
            // fallback for legacy/one-way
            cardContent += `
                <div class="airline">${flight.airlines || ''}</div>
                <div class="details">
                    <div class="time">${flight.departure_time || ''} - ${flight.arrival_time || ''}</div>
                    <div class="duration">${flight.duration || ''}</div>
                    <div class="stops">${flight.stops !== undefined ? formatStops(flight.stops) : ''}</div>
                    <div class="aircraft">${flight.aircraft || ''}</div>
                </div>
            `;
        }

        cardContent += `<a href="${flight.booking_url}" target="_blank" class="booking-link">Book Now</a>`;
        card.innerHTML = cardContent;
        return card;
    }
}); 