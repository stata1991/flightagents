/**
 * Comprehensive Trip Planning Display
 * Flow: Itinerary → Flights → Hotels
 */

class ComprehensiveTripPlanner {
    constructor() {
        this.currentPlan = null;
        this.currentStep = 0; // 0: Itinerary, 1: Flights, 2: Hotels
    }

    async createComprehensivePlan(formData) {
        try {
            // Show loading state
            this.showLoadingState();
            
            // Call the comprehensive planning endpoint
            const response = await fetch('/markdown-trip/plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const plan = await response.json();
            this.currentPlan = plan;
            
            // Display the comprehensive plan
            this.displayComprehensivePlan(plan);
            
        } catch (error) {
            console.error('Error creating comprehensive plan:', error);
            this.showError('Failed to create trip plan. Please try again.');
        }
    }

    displayComprehensivePlan(plan) {
        const container = document.getElementById('comprehensivePlanContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="comprehensive-plan">
                <div class="plan-header">
                    <h2>Your Complete Trip Plan</h2>
                    <div class="trip-summary">
                        <div class="summary-item">
                            <strong>From:</strong> ${plan.trip_summary.origin}
                        </div>
                        <div class="summary-item">
                            <strong>To:</strong> ${plan.trip_summary.destination}
                        </div>
                        <div class="summary-item">
                            <strong>Duration:</strong> ${plan.trip_summary.duration_days} days
                        </div>
                        <div class="summary-item">
                            <strong>Travelers:</strong> ${plan.trip_summary.travelers}
                        </div>
                        <div class="summary-item">
                            <strong>Budget:</strong> ${plan.trip_summary.budget_range}
                        </div>
                    </div>
                </div>

                <div class="plan-navigation">
                    <button class="nav-btn active" onclick="comprehensivePlanner.showStep(0)">
                        📋 Itinerary
                    </button>
                    <button class="nav-btn" onclick="comprehensivePlanner.showStep(1)">
                        ✈️ Flights
                    </button>
                    <button class="nav-btn" onclick="comprehensivePlanner.showStep(2)">
                        🏨 Hotels
                    </button>
                </div>

                <div class="plan-content">
                    <div id="itineraryStep" class="plan-step active">
                        ${this.renderItinerary(plan.itinerary)}
                    </div>
                    
                    <div id="flightsStep" class="plan-step">
                        ${this.renderFlights(plan.flights)}
                    </div>
                    
                    <div id="hotelsStep" class="plan-step">
                        ${this.renderHotels(plan.hotels)}
                    </div>
                </div>

                <div class="budget-breakdown">
                    <h3>Budget Breakdown</h3>
                    <div class="budget-items">
                        <div class="budget-item">
                            <span>Flights:</span>
                            <span>$${plan.budget_breakdown.flight_cost ? plan.budget_breakdown.flight_cost.toFixed(2) : '0.00'}</span>
                        </div>
                        <div class="budget-item">
                            <span>Hotels:</span>
                            <span>$${plan.budget_breakdown.hotel_cost ? plan.budget_breakdown.hotel_cost.toFixed(2) : '0.00'}</span>
                        </div>
                        <div class="budget-item">
                            <span>Activities:</span>
                            <span>$${plan.budget_breakdown.activities_cost ? plan.budget_breakdown.activities_cost.toFixed(2) : '0.00'}</span>
                        </div>
                        <div class="budget-item total">
                            <span><strong>Total Estimated:</strong></span>
                            <span><strong>$${plan.budget_breakdown.total_estimated_cost ? plan.budget_breakdown.total_estimated_cost.toFixed(2) : '0.00'}</strong></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderItinerary(itinerary) {
        if (!itinerary || !itinerary.itinerary) {
            return '<p>No itinerary available.</p>';
        }

        let html = '<div class="itinerary-display">';
        
        // Overview
        if (itinerary.destination_recommendations) {
            html += `
                <div class="overview-section">
                    <h3>Trip Overview</h3>
                    <div class="overview-content">
                        <p><strong>Must-See Attractions:</strong></p>
                        <ul>
                            ${(itinerary.destination_recommendations.must_see_attractions || []).slice(0, 5).map(attraction => 
                                `<li>${attraction.name} - ${attraction.time_needed}</li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }

        // Daily itinerary
        html += '<div class="daily-itinerary">';
        itinerary.itinerary.forEach((day, index) => {
            html += `
                <div class="day-card">
                    <div class="day-header">Day ${day.day}: Plan</div>
                    <div class="day-content">
                        <div class="time-slot">
                            <strong>Morning (${day.morning.start_time} - ${day.morning.end_time}):</strong>
                            <ul>
                                ${day.morning.activities.map(activity => `<li>${activity.name || activity}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="time-slot">
                            <strong>Afternoon (${day.afternoon.start_time} - ${day.afternoon.end_time}):</strong>
                            <ul>
                                ${day.afternoon.activities.map(activity => `<li>${activity.name || activity}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="time-slot">
                            <strong>Evening (${day.evening.start_time} - ${day.evening.end_time}):</strong>
                            <ul>
                                ${day.evening.activities.map(activity => `<li>${activity.name || activity}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        html += '</div>';
        return html;
    }

    renderFlights(flights) {
        if (!flights || flights.error) {
            return `<p>Flight search error: ${flights?.error || 'Unknown error'}</p>`;
        }

        let html = '<div class="flights-display">';
        
        // Cheapest flights
        html += `
            <div class="flight-category">
                <h3>💰 Cheapest Flights</h3>
                <div class="flight-cards">
                    ${this.renderFlightCards(flights.cheapest || [])}
                </div>
            </div>
        `;

        // Fastest flights
        html += `
            <div class="flight-category">
                <h3>⚡ Fastest Flights</h3>
                <div class="flight-cards">
                    ${this.renderFlightCards(flights.fastest || [])}
                </div>
            </div>
        `;

        // Best value flights
        html += `
            <div class="flight-category">
                <h3>🎯 Best Value Flights</h3>
                <div class="flight-cards">
                    ${this.renderFlightCards(flights.best_value || [])}
                </div>
            </div>
        `;

        html += '</div>';
        return html;
    }

    renderFlightCards(flights) {
        if (!flights.length) {
            return '<p>No flights found in this category.</p>';
        }

        return flights.map(flight => `
            <div class="flight-card">
                <div class="flight-header">
                    <h4>${flight.airline}</h4>
                    <div class="flight-price">$${flight.price} ${flight.currency}</div>
                </div>
                <div class="flight-details">
                    <div class="flight-time">
                        <span>${flight.departure_time}</span> → <span>${flight.arrival_time}</span>
                    </div>
                    <div class="flight-info">
                        <span>Duration: ${flight.duration}</span>
                        <span>Stops: ${flight.stops}</span>
                    </div>
                </div>
                <button class="book-btn" onclick="window.open('${flight.booking_url || '#'}', '_blank')">
                    Book Flight
                </button>
            </div>
        `).join('');
    }

    renderHotels(hotels) {
        if (!hotels || hotels.error) {
            return `<p>Hotel search error: ${hotels?.error || 'Unknown error'}</p>`;
        }

        let html = '<div class="hotels-display">';
        
        // Show message if available
        if (hotels.message) {
            html += `<div class="hotel-message">${hotels.message}</div>`;
        }
        
        // Budget hotels
        html += `
            <div class="hotel-category">
                <h3>💰 Budget Hotels</h3>
                <div class="hotel-cards">
                    ${this.renderHotelCards(hotels.budget || [])}
                </div>
            </div>
        `;

        // Mid-range hotels
        html += `
            <div class="hotel-category">
                <h3>🏢 Mid-Range Hotels</h3>
                <div class="hotel-cards">
                    ${this.renderHotelCards(hotels.mid_range || [])}
                </div>
            </div>
        `;

        // Luxury hotels
        html += `
            <div class="hotel-category">
                <h3>⭐ Luxury Hotels</h3>
                <div class="hotel-cards">
                    ${this.renderHotelCards(hotels.luxury || [])}
                </div>
            </div>
        `;

        html += '</div>';
        return html;
    }

    renderHotelCards(hotels) {
        if (!hotels || hotels.length === 0) {
            return '<p class="no-hotels">No hotels found in this category.</p>';
        }

        return hotels.map(hotel => {
            const rating = hotel.rating || 0;
            const starRating = hotel.star_rating || 0;
            // Use star_rating for display, fallback to rating if star_rating is 0
            const displayStars = starRating > 0 ? starRating : Math.floor(rating);
            const stars = '★'.repeat(Math.max(0, displayStars)) + '☆'.repeat(Math.max(0, 5 - displayStars));
            const price = hotel.average_price_per_night ? `$${hotel.average_price_per_night.toFixed(2)} per night` : 'Price not available';
            const reviews = hotel.review_count || 0;
            const photo = hotel.photos && hotel.photos.length > 0 ? hotel.photos[0] : '';
            
            // Generate proper Booking.com URL
            const bookingUrl = `https://www.booking.com/hotel/${hotel.hotel_id}.html`;
            
            return `
                <div class="hotel-card">
                    <div class="hotel-header">
                        <h4>${hotel.name}</h4>
                        <div class="hotel-rating">
                            <span class="stars">${stars}</span>
                            <span class="score">${rating.toFixed(1)}</span>
                        </div>
                    </div>
                    ${photo ? `<div class="hotel-photo"><img src="${photo}" alt="${hotel.name}" /></div>` : ''}
                    <div class="hotel-details">
                        ${hotel.address ? `<div class="hotel-address">${hotel.address}</div>` : ''}
                        <div class="hotel-price">${price}</div>
                        <div class="hotel-reviews">${reviews} reviews</div>
                    </div>
                    <a href="${bookingUrl}" target="_blank" class="book-btn">Book Now</a>
                </div>
            `;
        }).join('');
    }

    showStep(stepIndex) {
        // Update navigation buttons
        document.querySelectorAll('.nav-btn').forEach((btn, index) => {
            btn.classList.toggle('active', index === stepIndex);
        });

        // Update content sections
        document.querySelectorAll('.plan-step').forEach((step, index) => {
            step.classList.toggle('active', index === stepIndex);
        });

        this.currentStep = stepIndex;
    }

    showLoadingState() {
        const container = document.getElementById('comprehensivePlanContainer');
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <h3>Creating Your Complete Trip Plan...</h3>
                    <p>This may take a few moments as we search for the best flights and hotels.</p>
                </div>
            `;
        }
    }

    showError(message) {
        const container = document.getElementById('comprehensivePlanContainer');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                    <button onclick="location.reload()">Try Again</button>
                </div>
            `;
        }
    }
}

// Initialize the comprehensive planner
const comprehensivePlanner = new ComprehensiveTripPlanner();

// Export for use in other scripts
window.comprehensivePlanner = comprehensivePlanner; 