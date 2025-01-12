let map;
        let marker;
        let autocomplete;
        let directionsService;
        let directionsRenderers = [];

        const routeColors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"];

        function initMap() {
            const defaultLocation = { lat: 37.7749, lng: -122.4194 }; // San Francisco
            const mapOptions = {
                center: defaultLocation,
                zoom: 10,
            };

            map = new google.maps.Map(document.getElementById("map"), mapOptions);

            marker = new google.maps.Marker({
                position: defaultLocation,
                map: map,
                title: "Default Location",
            });

            directionsService = new google.maps.DirectionsService();

            if (navigator.geolocation) {   // gets users current position
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const userLocation = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                        };
                        map.setCenter(userLocation);
                        map.setZoom(15);
                        marker.setPosition(userLocation);
                        marker.setTitle("You are here!");

                        findNearestHospital(userLocation);
                    },
                    () => {
                        console.error("Geolocation failed or was denied.");
                    }
                );
            }

            const input = document.getElementById("address");
            autocomplete = new google.maps.places.Autocomplete(input);
            autocomplete.bindTo("bounds", map);
        }

        function setAddress() {
            const place = autocomplete.getPlace();

            const input = document.getElementById("address").value.trim();

            if (!input) {  // if no inputted location, users current location is used
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            const userLocation = {
                                lat: position.coords.latitude,
                                lng: position.coords.longitude,
                            };
                            map.setCenter(userLocation);
                            map.setZoom(15);
                            marker.setPosition(userLocation);
                            marker.setTitle("You are here!");

                            findNearestHospital(userLocation);
                        },
                        () => {
                            console.error("Geolocation failed or was denied.");
                        }
                    );
                }
                return;
            }

            if (!place.geometry) {
                alert("No details available for the entered address.");
                return;
            }

            map.setCenter(place.geometry.location);
            map.setZoom(15);
            marker.setPosition(place.geometry.location);
            marker.setTitle(place.formatted_address || "Selected Location");

            findNearestHospital(place.geometry.location);
        }

        function findNearestHospital(location) {
            const request = {
                location: location,
                radius: 5000,
                keyword: "emergency room hospital",
            };

            const service = new google.maps.places.PlacesService(map);

            service.nearbySearch(request, (results, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK && results.length > 0) {
                    const hospital = results[0];

                    const hospitalMarker = new google.maps.Marker({
                        position: hospital.geometry.location,
                        map: map,
                        title: hospital.name,
                    });

                    // Create an InfoWindow for the hospital marker
                    const infoWindow = new google.maps.InfoWindow();

                    // Fetch additional details for the hospital
                    service.getDetails({ placeId: hospital.place_id }, (placeDetails, detailsStatus) => {
                        if (detailsStatus === google.maps.places.PlacesServiceStatus.OK) {
                            const hours = placeDetails.opening_hours
                                ? placeDetails.opening_hours.weekday_text[new Date().getDay() - 1] || 'No hours available today'
                                : 'Hours not provided by Google Maps';

                            const content = `
                                <div>
                                    <h3>${placeDetails.name}</h3>
                                    <p><strong>Address:</strong> ${placeDetails.formatted_address}</p>
                                    <p><strong>Hours:</strong> ${hours}</p>
                                </div>
                            `;

                            infoWindow.setContent(content);
                        } else {
                            // Fallback content if details can't be fetched
                            infoWindow.setContent(`<div><h3>${hospital.name}</h3><p>No additional details available.</p></div>`);
                        }
                    });

                    // Add a click event to open the InfoWindow
                    hospitalMarker.addListener("click", () => {
                        infoWindow.open(map, hospitalMarker);
                    });

                    const travelMode = document.getElementById("travel-mode").value;
                    displayRoutes(location, hospital.geometry.location, travelMode);
                } else {
                    alert("No emergency hospitals found nearby.");
                }
            });
        }


        function displayRoutes(origin, destination, travelMode) {
            const request = {
                origin: origin,
                destination: destination,
                travelMode: travelMode,
                provideRouteAlternatives: true,
            };

            directionsService.route(request, (response, status) => {
                if (status === google.maps.DirectionsStatus.OK) {
                    directionsRenderers.forEach((renderer) => renderer.setMap(null));
                    directionsRenderers = [];

                    const routeInfo = document.getElementById("route-info");
                    routeInfo.innerHTML = `<h3>${travelMode} Routes</h3>`;

                    const routes = response.routes;
                    const allRoutesSteps = [];
                    const seenRoutes = new Set();
                    let routeNumber = 1;

                    routes.forEach((route, index) => {
                        const routeKey = route.overview_polyline;
                        if (seenRoutes.has(routeKey)) {
                            return;
                        }
                        seenRoutes.add(routeKey);

                        const renderer = new google.maps.DirectionsRenderer({
                            map: map,
                            directions: response,
                            routeIndex: index,
                            polylineOptions: {
                                strokeColor: routeColors[routeNumber % routeColors.length],
                                strokeOpacity: 0.7,
                                strokeWeight: 5,
                            },
                            suppressMarkers: true,
                        });

                        directionsRenderers.push(renderer);

                        const eta = route.legs[0].duration.text;
                        const colorIndicator = `<span class="route-color" style="background-color: ${routeColors[routeNumber % routeColors.length]};"></span>`;
                        let transitDetails = "";

                        if (travelMode === "TRANSIT") {
                            const steps = route.legs[0].steps;
                            steps.forEach((step) => {
                                if (step.travel_mode === "TRANSIT") {
                                    const transit = step.transit;
                                    transitDetails += `
                                        <br><strong>Take:</strong> ${transit.line.name || transit.line.short_name} (${transit.line.vehicle.type})
                                        <br><strong>From:</strong> ${transit.departure_stop.name}
                                        <br><strong>To:</strong> ${transit.arrival_stop.name}
                                        <br><strong>Departure:</strong> ${transit.departure_time.text}
                                        <br><strong>Arrival:</strong> ${transit.arrival_time.text}
                                        <br>`;
                                }
                            });
                        }

                        routeInfo.innerHTML += `<p>${colorIndicator}<strong>Route ${routeNumber}:</strong> ETA: ${eta}${transitDetails}</p>`;

                        const steps = route.legs[0].steps;
                        const routeSteps = steps.map((step, stepIndex) => {
                            const roadName = step.instructions.replace(/<[^>]*>/g, '') || 'Unnamed road';
                            return `Step ${stepIndex + 1}: ${roadName}`;
                        });

                        allRoutesSteps.push(`Route ${routeNumber}:\nETA: ${eta}\n${routeSteps.join('\n')}`);
                        routeNumber++;
                    });

                    let downloadButton = document.getElementById("download-button");
                    if (!downloadButton) {
                        downloadButton = document.createElement('button');
                        downloadButton.id = "download-button";
                        downloadButton.textContent = 'Download All Routes';
                        downloadButton.onclick = () => downloadRoutesAsICS(allRoutesSteps);
                        routeInfo.appendChild(downloadButton);
                    }
                } else {
                    console.error(`Directions request failed due to ${status}`);
                }
            });
        }



        function downloadRoutesAsICS(allRoutesSteps) {
            let icsContent = 'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Routes Export//EN\n';

            allRoutesSteps.forEach((routeSteps, index) => {
                icsContent += `BEGIN:VEVENT\n`;
                icsContent += `SUMMARY:Route ${index + 1}\n`;
                icsContent += `DESCRIPTION:${routeSteps.replace(/\n/g, '\\n')}\n`;
                icsContent += `DTSTART:${formatICSDate(new Date())}\n`; // Start date of the route
                icsContent += `DTEND:${formatICSDate(new Date(new Date().getTime() + 3600000))}\n`; // End date + 1 hour
                icsContent += `END:VEVENT\n`;
            });

            icsContent += 'END:VCALENDAR';

            // Create and download the .ics file
            const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'routes.ics';
            a.click();
            URL.revokeObjectURL(url);
        }

        function formatICSDate(date) {
            const year = date.getUTCFullYear();
            const month = String(date.getUTCMonth() + 1).padStart(2, '0');
            const day = String(date.getUTCDate()).padStart(2, '0');
            const hours = String(date.getUTCHours()).padStart(2, '0');
            const minutes = String(date.getUTCMinutes()).padStart(2, '0');
            const seconds = String(date.getUTCSeconds()).padStart(2, '0');
            return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
        }