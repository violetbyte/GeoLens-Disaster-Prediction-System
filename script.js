
/* ==========================================
   GEO LENS — ENVIRONMENTAL MONITORING
   Illustrative placeholders — not live data
========================================== */

const environmentalData = {
    flood: {
        label: "FLOOD MONITORING",
        value: "Moderate",
        status: "moderate",
        description: "Illustrative flood status",
        color: "#4D829B"
    },
    drought: {
        label: "DROUGHT MONITORING",
        value: "Low",
        status: "low",
        description: "Illustrative drought status",
        color: "#A78342"
    },
    vegetation: {
        label: "VEGETATION MONITORING",
        value: "Healthy",
        status: "healthy",
        description: "Illustrative vegetation status",
        color: "#4F805C"
    }
};

const categoryInfo = {
    flood: {
        title: "Flood Monitoring",
        description: "Browse locations for flood-related environmental monitoring.",
        eyebrow: "WATER SYSTEMS"
    },
    drought: {
        title: "Drought Monitoring",
        description: "Browse locations for drought-related environmental monitoring.",
        eyebrow: "WATER AVAILABILITY"
    },
    vegetation: {
        title: "Vegetation Monitoring",
        description: "Browse locations for vegetation and land-cover monitoring.",
        eyebrow: "LAND SYSTEMS"
    }
};

const monitoringLocations = {
    flood: [
        { name: "Kolkata", region: "West Bengal, India" },
        { name: "Sundarbans", region: "West Bengal, India" },
        { name: "Malda", region: "West Bengal, India" },
        { name: "Murshidabad", region: "West Bengal, India" },
        { name: "Howrah", region: "West Bengal, India" }
    ],
    drought: [
        { name: "Bankura", region: "West Bengal, India" },
        { name: "Purulia", region: "West Bengal, India" },
        { name: "Jhargram", region: "West Bengal, India" },
        { name: "Birbhum", region: "West Bengal, India" },
        { name: "Paschim Medinipur", region: "West Bengal, India" }
    ],
    vegetation: [
        { name: "Sundarbans", region: "West Bengal, India" },
        { name: "Dooars", region: "North Bengal, India" },
        { name: "Darjeeling", region: "West Bengal, India" },
        { name: "Jalpaiguri", region: "West Bengal, India" },
        { name: "Purulia", region: "West Bengal, India" }
    ]
};

/* ==========================================
   DOM ELEMENTS
========================================== */

const layerButtons = document.querySelectorAll(".layer-button");
const navItems = document.querySelectorAll(".nav-item");
const statusCards = document.querySelectorAll(".status-card");

const monitoringTitle = document.querySelector("#monitoringTitle");
const floodValue = document.querySelector("#floodValue");
const droughtValue = document.querySelector("#droughtValue");
const vegetationValue = document.querySelector("#vegetationValue");

const lastUpdated = document.querySelector("#lastUpdated");
const refreshButton = document.querySelector("#refreshButton");
const systemStatus = document.querySelector("#systemStatus");
const themeToggle = document.querySelector("#themeToggle");

const mapLegendText = document.querySelector("#mapLegendText");
const mapLegendColor = document.querySelector(".legend-color");

const locationSearch = document.querySelector("#locationSearch");
const searchMessage = document.querySelector("#searchMessage");
const categoryCards = document.querySelectorAll(".category-card");
const categoryButtons = document.querySelectorAll("[data-open-category]");

const homepage = document.querySelector("#home");
const legacyDashboard = document.querySelector("#legacyDashboard");
const categoryPage = document.querySelector("#categoryPage");
const locationAnalysisPage = document.querySelector("#locationAnalysisPage");

const homepageLocationResults =
    document.querySelector("#homepageLocationResults");

const backToLocations = document.querySelector("#backToLocations");
const analysisCategoryLink = document.querySelector("#analysisCategoryLink");
const analysisHomeLink = document.querySelector("#analysisHomeLink");
const backToHome = document.querySelector("#backToHome");

let currentCategory = null;

/* ==========================================
   THEME TOGGLE
========================================== */

function setTheme(theme, savePreference = true) {
    const isDark = theme === "dark";

    document.body.classList.toggle("dark-theme", isDark);
    document.body.classList.toggle("light-theme", !isDark);

    if (themeToggle) {
        themeToggle.setAttribute(
            "aria-label",
            isDark ? "Switch to light theme" : "Switch to dark theme"
        );

        themeToggle.setAttribute("aria-pressed", String(isDark));
        themeToggle.textContent = isDark ? "☀ Light mode" : "◐ Dark mode";
    }

    if (savePreference) {
        try {
            localStorage.setItem("geolens-theme", isDark ? "dark" : "light");
        } catch (error) {
            // Theme still works when storage is unavailable.
        }
    }
}

function initializeTheme() {
    let savedTheme = "light";

    try {
        savedTheme = localStorage.getItem("geolens-theme") || "light";
    } catch (error) {
        // Use light theme when browser storage is unavailable.
    }

    setTheme(savedTheme, false);
}

if (themeToggle) {
    themeToggle.addEventListener("click", function () {
        const isDark = document.body.classList.contains("dark-theme");
        setTheme(isDark ? "light" : "dark");
    });
}

initializeTheme();

/* ==========================================
   PAGE VISIBILITY AND NAVIGATION
========================================== */

function hideAllMainViews() {
    if (homepage) homepage.hidden = true;
    if (categoryPage) categoryPage.hidden = true;
    if (locationAnalysisPage) locationAnalysisPage.hidden = true;

    if (legacyDashboard) {
        legacyDashboard.hidden = true;
        legacyDashboard.setAttribute("aria-hidden", "true");
    }
}

function showHomepageSection(sectionId) {
    const target = document.getElementById(sectionId);

    if (!target || !homepage) return;

    hideAllMainViews();
    homepage.hidden = false;

    requestAnimationFrame(function () {
        target.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    });
}

function returnToHomepage() {
    hideAllMainViews();

    if (homepage) homepage.hidden = false;

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function handleTopNavigation(event) {
    const link = event.currentTarget;
    const href = link.getAttribute("href") || "";
    const target = link.dataset.navTarget || "";
    const label = link.textContent.trim().toLowerCase();

    if (href === "#home" || target === "home" || label === "home") {
        event.preventDefault();
        returnToHomepage();
        return;
    }

    if (
        href === "#monitoring" ||
        target === "monitoring" ||
        label.includes("monitoring")
    ) {
        event.preventDefault();
        showHomepageSection("monitoring");
        return;
    }

    if (href === "#about" || target === "about" || label.includes("about")) {
        event.preventDefault();
        showHomepageSection("about");
    }
}

document.querySelectorAll(
    ".home-nav a, .navbar nav a, a[data-nav-target]"
).forEach(function (link) {
    link.addEventListener("click", handleTopNavigation);
});

/* ==========================================
   STATUS COLOURS
========================================== */

function updateStatusColor(element, status) {
    if (!element) return;

    const statusColors = {
        high: "#955C58",
        moderate: "#A78342",
        low: "#4F805C",
        healthy: "#4F805C"
    };

    element.style.color = statusColors[status] || "";
}

/* ==========================================
   TIME FORMAT
========================================== */

function getFormattedTime() {
    return new Date().toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

/* ==========================================
   LEGACY MAP
========================================== */

let map = null;
let floodLayer = null;
let droughtLayer = null;
let vegetationLayer = null;

function initializeMap() {
    const mapElement = document.querySelector("#map");

    if (!mapElement || typeof L === "undefined" || map !== null) {
        return;
    }

    map = L.map("map").setView([22.5726, 88.3639], 7);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    L.marker([22.5726, 88.3639])
        .addTo(map)
        .bindPopup(
            "<strong>West Bengal</strong><br>" +
            "Illustrative monitoring location"
        );

    floodLayer = L.circle([22.5726, 88.3639], {
        radius: 50000,
        color: "#4D829B",
        fillColor: "#4D829B",
        fillOpacity: 0.2
    });

    droughtLayer = L.circle([22.5726, 88.3639], {
        radius: 50000,
        color: "#A78342",
        fillColor: "#A78342",
        fillOpacity: 0.2
    });

    vegetationLayer = L.circle([22.5726, 88.3639], {
        radius: 50000,
        color: "#4F805C",
        fillColor: "#4F805C",
        fillOpacity: 0.2
    });

    showMapLayer("flood");
}

function showMapLayer(layer) {
    if (!map) return;

    [floodLayer, droughtLayer, vegetationLayer].forEach(function (item) {
        if (item && map.hasLayer(item)) {
            map.removeLayer(item);
        }
    });

    const selectedLayers = {
        flood: floodLayer,
        drought: droughtLayer,
        vegetation: vegetationLayer
    };

    if (selectedLayers[layer]) {
        selectedLayers[layer].addTo(map);
    }
}

/* ==========================================
   LEGACY MONITORING CONTROLS
========================================== */

function selectMonitoringLayer(selectedLayer) {
    const selectedData = environmentalData[selectedLayer];

    if (!selectedData) return;

    layerButtons.forEach(function (button) {
        button.classList.toggle(
            "active",
            button.dataset.layer === selectedLayer
        );
    });

    statusCards.forEach(function (card) {
        card.classList.toggle(
            "selected",
            card.classList.contains(selectedLayer + "-card")
        );
    });

    if (monitoringTitle) monitoringTitle.textContent = selectedData.label;

    const valueElements = {
        flood: floodValue,
        drought: droughtValue,
        vegetation: vegetationValue
    };

    if (valueElements[selectedLayer]) {
        valueElements[selectedLayer].textContent = selectedData.value;
        updateStatusColor(valueElements[selectedLayer], selectedData.status);
    }

    const selectedCard = document.querySelector("." + selectedLayer + "-card");

    if (selectedCard) {
        const description = selectedCard.querySelector("p");
        if (description) description.textContent = selectedData.description;
    }

    if (mapLegendText) {
        mapLegendText.textContent =
            selectedData.label + " — illustrative overlay";
    }

    if (mapLegendColor) {
        mapLegendColor.style.background = selectedData.color;
    }

    showMapLayer(selectedLayer);
}

layerButtons.forEach(function (button) {
    button.addEventListener("click", function () {
        selectMonitoringLayer(button.dataset.layer);
    });
});

navItems.forEach(function (item) {
    item.addEventListener("click", function (event) {
        event.preventDefault();

        navItems.forEach(function (navItem) {
            navItem.classList.remove("active");
        });

        item.classList.add("active");

        const section = item.dataset.section;
        selectMonitoringLayer(section === "dashboard" ? "flood" : section);
    });
});

updateStatusColor(floodValue, environmentalData.flood.status);

/* ==========================================
   REFRESH BUTTON
   No live environmental data is fetched.
========================================== */

if (lastUpdated) {
    lastUpdated.textContent = "Illustrative data · No live feed connected";
}

if (refreshButton) {
    refreshButton.addEventListener("click", function () {
        if (systemStatus) {
            systemStatus.textContent =
                "No live data source is connected. No data was fetched.";
        }

        if (lastUpdated) {
            lastUpdated.textContent = "Last checked: " + getFormattedTime();
        }
    });
}
/* ==========================================
   SATELLITE IMAGE HANDLER
========================================== */

function updateSatelliteImage(side, imageUrl, acquisitionDate) {
    const image = document.getElementById(side + "SatelliteImage");
    const placeholder = document.getElementById(side + "ImagePlaceholder");
    const dateLabel = document.getElementById(side + "ImageDate");

    if (!image || !placeholder || !dateLabel) return;

    image.onload = null;
    image.onerror = null;
    image.hidden = true;
    placeholder.hidden = false;
    image.removeAttribute("src");
    dateLabel.textContent = "Date unavailable";

    if (typeof imageUrl !== "string" || !imageUrl.trim()) return;

    let parsedUrl;

    try {
        parsedUrl = new URL(imageUrl, window.location.href);
    } catch (error) {
        return;
    }

    if (!["http:", "https:"].includes(parsedUrl.protocol)) return;

    image.onload = function () {
        image.hidden = false;
        placeholder.hidden = true;

        if (
            typeof acquisitionDate === "string" &&
            /^\d{4}-\d{2}-\d{2}$/.test(acquisitionDate)
        ) {
            const parsedDate = new Date(acquisitionDate + "T00:00:00Z");

            if (
                !Number.isNaN(parsedDate.getTime()) &&
                parsedDate.toISOString().slice(0, 10) === acquisitionDate
            ) {
                dateLabel.textContent = parsedDate.toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    timeZone: "UTC"
                });
            }
        }
    };

    image.onerror = function () {
        image.hidden = true;
        placeholder.hidden = false;
        dateLabel.textContent = "Date unavailable";
        image.removeAttribute("src");
    };

    image.src = parsedUrl.href;
}

/* ==========================================
   HOMEPAGE SEARCH — INTERACTIVE ENHANCEMENTS
========================================== */

/* Add a clear button without changing index.html. */
let clearSearchButton = null;

function initializeSearchEnhancements() {
    if (!locationSearch) return;

    locationSearch.setAttribute("aria-label", "Search monitoring categories and locations");
    locationSearch.setAttribute("aria-describedby", "searchMessage");

    if (searchMessage) {
        searchMessage.setAttribute("role", "status");
        searchMessage.setAttribute("aria-live", "polite");
    }

    if (homepageLocationResults) {
        homepageLocationResults.setAttribute("role", "list");
        homepageLocationResults.setAttribute("aria-label", "Matching locations");
    }

    clearSearchButton = document.createElement("button");
    clearSearchButton.type = "button";
    clearSearchButton.className = "clear-search-button";
    clearSearchButton.textContent = "Clear";
    clearSearchButton.setAttribute("aria-label", "Clear location search");
    clearSearchButton.hidden = true;

    locationSearch.insertAdjacentElement("afterend", clearSearchButton);

    clearSearchButton.addEventListener("click", function () {
        locationSearch.value = "";
        locationSearch.dispatchEvent(new Event("input", { bubbles: true }));
        locationSearch.focus();
    });

    locationSearch.addEventListener("input", function () {
        clearSearchButton.hidden = !locationSearch.value.trim();
    });
}

/* Safely highlight matching text without inserting HTML. */
function appendHighlightedText(container, text, query) {
    const normalizedText = String(text);
    const normalizedQuery = String(query || "").trim();

    if (!normalizedQuery) {
        container.textContent = normalizedText;
        return;
    }

    const lowerText = normalizedText.toLowerCase();
    const lowerQuery = normalizedQuery.toLowerCase();

    let currentIndex = 0;
    let matchIndex = lowerText.indexOf(lowerQuery);

    while (matchIndex !== -1) {
        if (matchIndex > currentIndex) {
            container.append(
                document.createTextNode(
                    normalizedText.slice(currentIndex, matchIndex)
                )
            );
        }

        const highlight = document.createElement("mark");
        highlight.className = "search-match";
        highlight.textContent = normalizedText.slice(
            matchIndex,
            matchIndex + normalizedQuery.length
        );

        container.append(highlight);

        currentIndex = matchIndex + normalizedQuery.length;
        matchIndex = lowerText.indexOf(lowerQuery, currentIndex);
    }

    if (currentIndex < normalizedText.length) {
        container.append(
            document.createTextNode(normalizedText.slice(currentIndex))
        );
    }
}

function renderHomepageLocationResults(results, query) {
    if (!homepageLocationResults) return;

    homepageLocationResults.replaceChildren();

    results.forEach(function (result) {
        const item = document.createElement("div");
        item.className = "homepage-location-result";
        item.setAttribute("role", "listitem");

        const details = document.createElement("div");
        details.className = "homepage-location-result-details";

        const name = document.createElement("h3");
        appendHighlightedText(name, result.location.name, query);

        const region = document.createElement("p");
        appendHighlightedText(region, result.location.region, query);

        const categoryLabel = document.createElement("span");
        categoryLabel.className = "search-result-category";
        categoryLabel.textContent = categoryInfo[result.category].title;

        const viewButton = document.createElement("button");
        viewButton.type = "button";
        viewButton.textContent = "View Analysis ↗";

        viewButton.addEventListener("click", function () {
            openLocationAnalysis(result.category, result.location);
        });

        details.append(name, region, categoryLabel);
        item.append(details, viewButton);
        homepageLocationResults.append(item);
    });

    homepageLocationResults.hidden = results.length === 0;
}

function searchHomepage(query) {
    const normalizedQuery = query.trim().toLowerCase();
    const matchingLocations = [];
    let matchingCategories = 0;

    if (!normalizedQuery) {
        categoryCards.forEach(function (card) {
            card.classList.remove("search-hidden");
        });

        if (homepageLocationResults) {
            homepageLocationResults.replaceChildren();
            homepageLocationResults.hidden = true;
        }

        if (searchMessage) {
            searchMessage.textContent = "";
            searchMessage.hidden = true;
        }

        return;
    }

    categoryCards.forEach(function (card) {
        const searchableText = (
            card.innerText + " " + (card.dataset.search || "")
        ).toLowerCase();

        const matches = searchableText.includes(normalizedQuery);

        card.classList.toggle("search-hidden", !matches);

        if (matches) matchingCategories++;
    });

    Object.entries(monitoringLocations).forEach(function ([category, locations]) {
        locations.forEach(function (location) {
            const searchableText = (
                location.name + " " +
                location.region + " " +
                category + " " +
                categoryInfo[category].title
            ).toLowerCase();

            if (searchableText.includes(normalizedQuery)) {
                matchingLocations.push({ category, location });
            }
        });
    });

    renderHomepageLocationResults(matchingLocations, query);

    if (!searchMessage) return;

    const parts = [];

    if (matchingCategories) {
        parts.push(
            matchingCategories + " categor" +
            (matchingCategories === 1 ? "y" : "ies")
        );
    }

    if (matchingLocations.length) {
        parts.push(
            matchingLocations.length + " location" +
            (matchingLocations.length === 1 ? "" : "s")
        );
    }

    if (parts.length === 0) {
        searchMessage.textContent =
            'No results for "' + query.trim() + '". Try a location such as Kolkata or Bankura.';
    } else {
        searchMessage.textContent = "Found " + parts.join(" and ") + ".";
    }

    searchMessage.hidden = false;
}

if (locationSearch) {
    locationSearch.addEventListener("input", function () {
        searchHomepage(locationSearch.value);
    });
}

initializeSearchEnhancements();

/* ==========================================
   OPEN CATEGORY PAGE
========================================== */

function openCategory(category) {
    const info = categoryInfo[category];

    if (!info || !categoryPage || !homepage) {
        console.error("Category page or category information is missing.");
        return;
    }

    hideAllMainViews();
    categoryPage.hidden = false;

    const title = document.querySelector("#categoryPageTitle");
    const description = document.querySelector("#categoryPageDescription");
    const eyebrow = document.querySelector("#categoryPageEyebrow");

    if (title) title.textContent = info.title;
    if (description) description.textContent = info.description;
    if (eyebrow) eyebrow.textContent = info.eyebrow;

    currentCategory = category;
    renderLocationList(category);

    window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ==========================================
   RENDER LOCATION LIST
========================================== */

function renderLocationList(category) {
    const list = document.querySelector("#locationList");
    const search = document.querySelector("#locationListSearch");
    const message = document.querySelector("#locationListMessage");

    if (!list || !message) return;

    const locations = monitoringLocations[category] || [];

    function displayLocations(query = "") {
        const filtered = locations.filter(function (location) {
            return (location.name + " " + location.region)
                .toLowerCase()
                .includes(query.toLowerCase());
        });

        list.replaceChildren();

        filtered.forEach(function (location) {
            const card = document.createElement("article");
            card.className = "location-card";

            const details = document.createElement("div");
            details.className = "location-card-details";

            const name = document.createElement("h3");
            appendHighlightedText(name, location.name, query);

            const region = document.createElement("p");
            region.textContent = location.region;

            const status = document.createElement("span");
            status.className = "location-data-status";
            status.textContent = "Analysis data not connected";

            const action = document.createElement("button");
            action.type = "button";
            action.className = "location-analysis-button";
            action.textContent = "View Analysis ↗";

            action.addEventListener("click", function () {
                openLocationAnalysis(category, location);
            });

            details.append(name, region, status);
            card.append(details, action);
            list.append(card);
        });

        message.textContent = filtered.length
            ? filtered.length + " location" +
                (filtered.length === 1 ? "" : "s") + " listed."
            : "No locations match your search.";
    }

    if (search) {
        search.value = "";
        search.oninput = function () {
            displayLocations(search.value.trim());
        };
    }

    displayLocations();
}

/* ==========================================
   OPEN LOCATION ANALYSIS
========================================== */

function openLocationAnalysis(category, location) {
    if (!categoryInfo[category] || !locationAnalysisPage || !location) {
        console.error("Location analysis page or location data is missing.");
        return;
    }

    currentCategory = category;

    document.querySelectorAll(".assessment-indicator").forEach(function (indicator) {
        indicator.hidden = indicator.dataset.assessment !== category;
    });

    const title = document.querySelector("#analysisLocationTitle");
    const region = document.querySelector("#analysisLocationRegion");
    const breadcrumbLocation = document.querySelector("#analysisBreadcrumbLocation");
    const categoryLabel = document.querySelector("#analysisCategoryLabel");
    const categoryLink = document.querySelector("#analysisCategoryLink");
    const dataStatus = document.querySelector("#analysisDataStatus");

    if (title) title.textContent = location.name;
    if (region) region.textContent = location.region;
    if (breadcrumbLocation) breadcrumbLocation.textContent = location.name;

    if (categoryLabel) {
        categoryLabel.textContent = categoryInfo[category].title.toUpperCase();
    }

    if (categoryLink) {
        categoryLink.textContent = categoryInfo[category].title;
    }

    if (dataStatus) dataStatus.textContent = "DATA NOT CONNECTED";

    updateSatelliteImage("before", location.beforeImageUrl, location.beforeImageDate);
    updateSatelliteImage("after", location.afterImageUrl, location.afterImageDate);

    hideAllMainViews();
    locationAnalysisPage.hidden = false;

    window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ==========================================
   RETURN NAVIGATION
========================================== */

function returnToCategoryPage() {
    if (!currentCategory) {
        returnToHomepage();
        return;
    }

    hideAllMainViews();

    if (categoryPage) categoryPage.hidden = false;

    window.scrollTo({ top: 0, behavior: "smooth" });
}

if (backToLocations) {
    backToLocations.addEventListener("click", returnToCategoryPage);
}

if (analysisCategoryLink) {
    analysisCategoryLink.addEventListener("click", function (event) {
        event.preventDefault();
        returnToCategoryPage();
    });
}

if (analysisHomeLink) {
    analysisHomeLink.addEventListener("click", function (event) {
        event.preventDefault();
        returnToHomepage();
    });
}

categoryButtons.forEach(function (button) {
    button.addEventListener("click", function () {
        openCategory(button.dataset.openCategory);
    });
});

if (backToHome) {
    backToHome.addEventListener("click", function (event) {
        event.preventDefault();
        returnToHomepage();
    });
}

/* ==========================================
   INITIALIZE
========================================== */

initializeMap();



/* ========================================
   FIX: GEOLENS SCROLL & NAVIGATION
======================================== */

(() => {
    function initGeoLensScrollEffects() {
        const homepage = document.querySelector("#home");
        const navLinks = document.querySelectorAll(
            ".home-nav .home-nav-link"
        );

        if (!homepage || !navLinks.length) return;

        /* Subtle section reveal animation */
        const revealTargets = homepage.querySelectorAll(
            ".hero-section, .platform-overview, #monitoring, #about"
        );

        const reducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        if (reducedMotion || !("IntersectionObserver" in window)) {
            revealTargets.forEach((section) => {
                section.classList.add("is-visible");
            });
        } else {
            const revealObserver = new IntersectionObserver(
                (entries, observer) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add("is-visible");
                            observer.unobserve(entry.target);
                        }
                    });
                },
                {
                    threshold: 0.05,
                    rootMargin: "0px 0px -30px 0px"
                }
            );

            revealTargets.forEach((section) => {
                section.classList.add("scroll-reveal");
                revealObserver.observe(section);
            });
        }

        
function updateActiveNavigation() {
    if (homepage.hidden) return;

    const monitoring = document.querySelector("#monitoring");
    const about = document.querySelector("#about");

    if (!monitoring || !about) return;

    const scrollPosition = window.scrollY;
    const activationLine = window.innerHeight * 0.35;

    const monitoringTop =
        monitoring.getBoundingClientRect().top + scrollPosition;

    const aboutTop =
        about.getBoundingClientRect().top + scrollPosition;

    const pageBottom =
        window.scrollY + window.innerHeight >=
        document.documentElement.scrollHeight - 5;

    let activeId = "home";

    if (pageBottom || scrollPosition + activationLine >= aboutTop) {
        activeId = "about";
    } else if (scrollPosition + activationLine >= monitoringTop) {
        activeId = "monitoring";
    }

    navLinks.forEach((link) => {
        const isActive = link.getAttribute("href") === "#" + activeId;

        link.classList.toggle("active", isActive);

        if (isActive) {
            link.setAttribute("aria-current", "location");
        } else {
            link.removeAttribute("aria-current");
        }
    });
}

        window.addEventListener(
            "scroll",
            updateActiveNavigation,
            { passive: true }
        );

        window.addEventListener("resize", updateActiveNavigation);

        navLinks.forEach((link) => {
            link.addEventListener("click", () => {
                window.setTimeout(updateActiveNavigation, 300);
            });
        });

        updateActiveNavigation();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initGeoLensScrollEffects,
            { once: true }
        );
    } else {
        initGeoLensScrollEffects();
    }
})();



/* =========================================
   GEO LENS — INTERACTIVE LOCATION MAP
========================================= */

(function initializeLocationExplorer() {
    const mapElement = document.getElementById("locationMap");

    if (!mapElement) return;

    const statusMessage = document.getElementById("locationMapMessage");
    const filterButtons = document.querySelectorAll("[data-map-filter]");

    if (typeof L === "undefined") {
        if (statusMessage) {
            statusMessage.textContent =
                "Map library unavailable. Check your internet connection.";
        }
        return;
    }

    const categoryColors = {
        flood: "#628ca1",
        drought: "#b39a67",
        vegetation: "#668b6a"
    };

    // One marker per unique location.
    // Some locations belong to more than one monitoring category.
    const mapLocations = [
        {
            name: "Kolkata",
            region: "South Bengal",
            coordinates: [22.5726, 88.3639],
            categories: ["flood"]
        },
        {
            name: "Sundarbans",
            region: "South Bengal",
            coordinates: [21.9497, 88.8958],
            categories: ["flood", "vegetation"]
        },
        {
            name: "Malda",
            region: "North Bengal",
            coordinates: [25.0108, 88.1411],
            categories: ["flood"]
        },
        {
            name: "Murshidabad",
            region: "South Bengal",
            coordinates: [24.1759, 88.2802],
            categories: ["flood"]
        },
        {
            name: "Howrah",
            region: "South Bengal",
            coordinates: [22.5958, 88.2636],
            categories: ["flood"]
        },
        {
            name: "Bankura",
            region: "South Bengal",
            coordinates: [23.2324, 87.0784],
            categories: ["drought"]
        },
        {
            name: "Purulia",
            region: "South Bengal",
            coordinates: [23.3322, 86.3652],
            categories: ["drought", "vegetation"]
        },
        {
            name: "Jhargram",
            region: "South Bengal",
            coordinates: [22.4530, 86.9977],
            categories: ["drought"]
        },
        {
            name: "Birbhum",
            region: "South Bengal",
            coordinates: [23.9080, 87.5270],
            categories: ["drought"]
        },
        {
            name: "Paschim Medinipur",
            region: "South Bengal",
            coordinates: [22.4257, 87.3199],
            categories: ["drought"]
        },
        {
            name: "Dooars",
            region: "North Bengal",
            coordinates: [26.8500, 88.8500],
            categories: ["vegetation"]
        },
        {
            name: "Darjeeling",
            region: "North Bengal",
            coordinates: [27.0360, 88.2627],
            categories: ["vegetation"]
        },
        {
            name: "Jalpaiguri",
            region: "North Bengal",
            coordinates: [26.5167, 88.7333],
            categories: ["vegetation"]
        }
    ];

    let activeFilter = "all";
    const markerRecords = [];

    const map = L.map("locationMap", {
        scrollWheelZoom: false,
        zoomControl: true
    });

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    const westBengalBounds = L.latLngBounds(
        [21.4, 85.7],
        [27.5, 89.9]
    );

    map.fitBounds(westBengalBounds, {
        padding: [18, 18]
    });

    function getMarkerColor(location) {
        const category =
            activeFilter !== "all" &&
            location.categories.includes(activeFilter)
                ? activeFilter
                : location.categories[0];

        return categoryColors[category];
    }

    function getPopupCategory(location) {
        if (
            activeFilter !== "all" &&
            location.categories.includes(activeFilter)
        ) {
            return activeFilter;
        }

        return location.categories[0];
    }

    function createPopupContent(location) {
        const categories = location.categories
            .map(category =>
                category.charAt(0).toUpperCase() + category.slice(1)
            )
            .join(" · ");

        return `
            <div class="map-popup-content">
                <strong>${location.name}</strong>
                <div>${location.region}</div>
                <div class="map-popup-categories">${categories}</div>
                <button
                    type="button"
                    class="map-popup-open"
                    data-map-location="${location.name}"
                    data-map-category="${getPopupCategory(location)}"
                >
                    Explore location →
                </button>
            </div>
        `;
    }

    mapLocations.forEach(location => {
        const marker = L.circleMarker(location.coordinates, {
            radius: 7,
            color: "#ffffff",
            weight: 2,
            fillColor: getMarkerColor(location),
            fillOpacity: 0.95
        });

        marker.bindPopup(createPopupContent(location), {
            maxWidth: 220
        });

        marker.addTo(map);

        markerRecords.push({
            location,
            marker
        });
    });

    function applyMapFilter(filter) {
        activeFilter = filter;

        filterButtons.forEach(button => {
            const isActive = button.dataset.mapFilter === filter;

            button.classList.toggle("active", isActive);
            button.setAttribute("aria-pressed", String(isActive));
        });

        const visibleLocations = [];

        markerRecords.forEach(({ location, marker }) => {
            const isVisible =
                filter === "all" ||
                location.categories.includes(filter);

            if (isVisible) {
                if (!map.hasLayer(marker)) {
                    marker.addTo(map);
                }

                marker.setStyle({
                    fillColor: getMarkerColor(location),
                    opacity: 1,
                    fillOpacity: 0.95
                });

                marker.setPopupContent(createPopupContent(location));
                visibleLocations.push(location);
            } else {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            }
        });

        if (visibleLocations.length === 1) {
            map.setView(visibleLocations[0].coordinates, 8);
        } else if (filter === "all") {
            map.fitBounds(westBengalBounds, {
                padding: [18, 18]
            });
        } else if (visibleLocations.length > 1) {
            const filteredBounds = L.latLngBounds(
                visibleLocations.map(location => location.coordinates)
            );

            map.fitBounds(filteredBounds, {
                padding: [24, 24],
                maxZoom: 8
            });
        }
    }

    filterButtons.forEach(button => {
        button.addEventListener("click", () => {
            applyMapFilter(button.dataset.mapFilter);
        });
    });

    // Open a location in the existing analysis view when supported.
    map.on("popupopen", event => {
        const popupElement = event.popup.getElement();

        if (!popupElement) return;

        const exploreButton = popupElement.querySelector(
            "[data-map-location]"
        );

        if (!exploreButton) return;

        exploreButton.addEventListener("click", () => {
            const locationName = exploreButton.dataset.mapLocation;
            const category = exploreButton.dataset.mapCategory;

            const location = mapLocations.find(
                item => item.name === locationName
            );

            if (!location) return;

            if (typeof openLocationAnalysis === "function") {
                openLocationAnalysis(category, {
                    name: location.name,
                    region: location.region
                });
            } else {
                // Keep the map usable even if the analysis function
                // has a different name in the existing project.
                console.info(
                    "Location selected:",
                    location.name,
                    "Category:",
                    category
                );
            }
        });
    });

    if (statusMessage) {
        statusMessage.hidden = true;
    }

    // Correct Leaflet sizing after the page layout is painted.
    requestAnimationFrame(() => {
        map.invalidateSize();
    });

    // Allow the map to respond to viewport changes.
    window.addEventListener("resize", () => {
        map.invalidateSize();
    });
})();
