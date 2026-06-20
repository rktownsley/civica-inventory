/* inventory_page.js
 *
 * Page-level (non-item-specific) behavior for main.html.
 *
 * IMPORTANT: this file is a direct, behavior-preserving port of several
 * originally-separate <script> blocks from main.html. Each section below
 * (separated by a banner comment) corresponds to one of those original,
 * independent top-level scripts. They are kept independent here too
 * (not merged into a single DOMContentLoaded handler) because the
 * original relies on each <script> block being its own execution
 * context -- e.g. one block references a `#sort-option` element that
 * does not exist in this template and will throw, but that must not
 * prevent the *other*, unrelated blocks from running, exactly as in
 * the original markup.
 *
 * Depends on `window.APP_CONFIG`, set inline in main.html, for the
 * handful of values that originate server-side (current filter
 * selections, the main_page URL, total item count, etc).
 */

/* =====================================================================
 * Block: location-select -> navigate with ?location=
 * (originally the <script> immediately after the location <select>)
 * ===================================================================== */
document.getElementById("location-select").addEventListener("change", function() {
    const selectedLocation = this.value; // e.g., "Tepati"

    // Get current page URL
    const currentUrl = new URL(window.location.href);
    const currentLocation = currentUrl.searchParams.get('location') || "";

    // Only navigate if the value actually changed
    if (selectedLocation !== currentLocation) {
        currentUrl.searchParams.set('location', selectedLocation);
        window.location.href = currentUrl.toString();
    }
});

/* =====================================================================
 * Block: search input -> navigate with ?search= on blur
 * ===================================================================== */
(() => {
    const searchInput = document.getElementById("search");
    if (!searchInput) return;

    searchInput.addEventListener("blur", function () {
        const newSearch = this.value.trim();

        const currentUrl = new URL(window.location.href);
        const currentSearch = currentUrl.searchParams.get("search") || "";

        // Only navigate if the value actually changed
        if (newSearch !== currentSearch) {
            if (newSearch) {
                currentUrl.searchParams.set("search", newSearch);
            } else {
                currentUrl.searchParams.delete("search");
            }

            // Reset pagination when searching
            currentUrl.searchParams.set("page", "");

            window.location.href = currentUrl.toString();
        }
    });
})();

/* =====================================================================
 * Block: sortSelect -> navigate to URL stored in its value
 * ===================================================================== */
document.getElementById("sortSelect").addEventListener("change", function() {
    const url = this.value;
    if (url && url !== "Sort") {
        window.location = url;
    }
});

/* =====================================================================
 * Block: handleSearch / handleClear / handleSort (unused demo handlers,
 * kept verbatim for parity with the original inline <script>)
 * ===================================================================== */
function handleSearch() {
    const query = document.getElementById("searchInput").value;
    alert("Searching for: " + query);
}

function handleClear() {
    document.getElementById("searchInput").value = "";
    document.getElementById("sortSelect").selectedIndex = 0;
}

function handleSort() {
    const sortBy = document.getElementById("sortSelect").value;
    alert("Sorting by: " + sortBy);
}

/* =====================================================================
 * Block: filter modal checkboxes/date -> URL params + filter bubbles
 * ===================================================================== */
document.addEventListener('DOMContentLoaded', function () {
    const inputs = document.querySelectorAll('.category-checkbox');
    const bubblesContainer = document.getElementById('filter-bubbles');

    function updateURLForInput(input) {
        const name = input.name;
        const value = input.type === 'checkbox' ? input.value : input.value;
        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);

        if (input.type === 'checkbox') {
            if (input.checked) {
                params.append(name, value);
            } else {
                // Remove all entries of this name and re-add the others
                const newValues = [...params.getAll(name)].filter(v => v !== value);
                params.delete(name);
                newValues.forEach(v => params.append(name, v));
            }
        } else {
            // For non-checkbox inputs like <input type="date">
            if (value) {
                params.set(name, value);
            } else {
                params.delete(name);
            }
        }

        window.history.replaceState({}, '', `${url.pathname}?${params}`);
    }

    function updateBubbles() {
        bubblesContainer.innerHTML = ''; // clear old bubbles

        inputs.forEach(input => {
            const value = input.value;
            const name = input.name;
            if (
                (input.type === 'checkbox' && input.checked) ||
                (input.type !== 'checkbox' && value)
            ) {
                const label = input.dataset.label || value;

                const bubble = document.createElement('span');
                bubble.className = 'badge rounded-pill bg-light text-primary px-3 py-2 position-relative me-2 mb-2 d-inline-block';
                bubble.innerHTML = `
                    <span class="me-3">${label}</span>
                    <button type="button"
                        class="position-absolute top-50 end-0 translate-middle-y
                            btn btn-secondary btn-sm rounded-circle p-0
                            d-flex align-items-center justify-content-center"
                        style="width:16px;height:16px;"
                        aria-label="Remove">
                        ×
                    </button>
                `;

                bubble.querySelector('button').addEventListener('click', () => {
                    if (input.type === 'checkbox') {
                        input.checked = false;
                    } else {
                        input.value = '';
                    }
                    updateBubbles();
                    updateURLForInput(input);
                    window.location.reload();
                });

                bubblesContainer.appendChild(bubble);
            }
        });
    }

    inputs.forEach(input => {
        input.addEventListener('change', () => {
            updateBubbles();
            updateURLForInput(input);
            updateResultCount();
        });
    });

    updateBubbles(); // Initial render
    updateResultCount(); // Initial count

    // Function to update the result count display
    function updateResultCount() {
        // Get all checked filters
        const checkedInputs = Array.from(inputs).filter(input => {
            if (input.type === 'checkbox') {
                return input.checked;
            } else {
                return input.value && input.value.trim() !== '';
            }
        });

        // If no filters are selected, show total count
        if (checkedInputs.length === 0) {
            const totalCount = window.APP_CONFIG.itemsCount;
            updateCountDisplay(totalCount);
            return;
        }

        // Build URL with current filter parameters
        const url = new URL(window.location.href);
        const params = new URLSearchParams();

        // Add location and search from current URL
        const currentLocation = url.searchParams.get('location');
        const currentSearch = url.searchParams.get('search');
        const currentSort = url.searchParams.get('sort');

        if (currentLocation) params.set('location', currentLocation);
        if (currentSearch) params.set('search', currentSearch);
        if (currentSort) params.set('sort', currentSort);

        // Add all checked filters
        checkedInputs.forEach(input => {
            if (input.type === 'checkbox') {
                params.append(input.name, input.value);
            } else {
                params.set(input.name, input.value);
            }
        });

        // Fetch the filtered count from the server
        fetch(`${window.APP_CONFIG.mainPageUrl}?${params}&count_only=true`)
            .then(response => response.json())
            .then(data => {
                updateCountDisplay(data.count || 0);
            })
            .catch(error => {
                console.error('Error fetching count:', error);
                updateCountDisplay(window.APP_CONFIG.itemsCount);
            });
    }

    function updateCountDisplay(count) {
        const buttonCountEl = document.getElementById('button-result-count');
        if (buttonCountEl) buttonCountEl.textContent = count;
    }
});

/* =====================================================================
 * Block: locationExists flag (originally a standalone inline <script>
 * inside the <tbody>, used as a one-off boolean -- kept for parity)
 * ===================================================================== */
var locationExists = window.APP_CONFIG.locationExists;

/* =====================================================================
 * Block: sort-option dependent dropdown visibility (category/supplier/
 * last_edit/location1-4) + auto-submit-on-change wiring.
 *
 * NOTE: this template does not contain an element with id="sort-option".
 * As in the original inline script, this listener will throw a
 * TypeError as soon as it runs (`getElementById("sort-option")` is
 * null), so none of the code below actually executes in this template.
 * It is kept verbatim (unguarded) to preserve that exact behavior.
 * ===================================================================== */
document.addEventListener("DOMContentLoaded", function() {
    var sortOption = document.getElementById("sort-option").value; // Get the selected sort option
    var categoryDropdownContainer = document.getElementById("category-dropdown-container");
    var supplierDropdownContainer = document.getElementById("supplier-dropdown-container");
    var lastEditDropdownContainer = document.getElementById("last_edit-dropdown-container");
    var location1DropdownContainer = document.getElementById("location1-dropdown-container");
    var location2DropdownContainer = document.getElementById("location2-dropdown-container");
    var location3DropdownContainer = document.getElementById("location3-dropdown-container");
    var location4DropdownContainer = document.getElementById("location4-dropdown-container");

    var selectedCategory = window.APP_CONFIG.selectedCategory; // Get selected category from the URL
    var selectedSupplier = window.APP_CONFIG.selectedSupplier; // Get selected supplier from the URL
    var selectedLastEdit = window.APP_CONFIG.selectedLastEdit; // Get selected last edit from the URL
    var selectedLocation1 = window.APP_CONFIG.selectedLocation1;
    var selectedLocation2 = window.APP_CONFIG.selectedLocation2;
    var selectedLocation3 = window.APP_CONFIG.selectedLocation3;
    var selectedLocation4 = window.APP_CONFIG.selectedLocation4;

    // Show location1-4 dropdown if "Sort by location" is selected or a location is already selected
    location1DropdownContainer.style.display = (sortOption === "B" || (selectedLocation1 !== "" && selectedLocation1 !== "None") || (selectedLocation2 !== "" && selectedLocation2 !== "None") || (selectedLocation3 !== "" && selectedLocation3 !== "None") || (selectedLocation4 !== "" && selectedLocation4 !== "None")) ? "block" : "none";
    location2DropdownContainer.style.display = (sortOption === "B" || (selectedLocation1 !== "" && selectedLocation1 !== "None") || (selectedLocation2 !== "" && selectedLocation2 !== "None") || (selectedLocation3 !== "" && selectedLocation3 !== "None") || (selectedLocation4 !== "" && selectedLocation4 !== "None")) ? "block" : "none";
    location3DropdownContainer.style.display = (sortOption === "B" || (selectedLocation1 !== "" && selectedLocation1 !== "None") || (selectedLocation2 !== "" && selectedLocation2 !== "None") || (selectedLocation3 !== "" && selectedLocation3 !== "None") || (selectedLocation4 !== "" && selectedLocation4 !== "None")) ? "block" : "none";
    location4DropdownContainer.style.display = (sortOption === "B" || (selectedLocation1 !== "" && selectedLocation1 !== "None") || (selectedLocation2 !== "" && selectedLocation2 !== "None") || (selectedLocation3 !== "" && selectedLocation3 !== "None") || (selectedLocation4 !== "" && selectedLocation4 !== "None")) ? "block" : "none";

    // Show category dropdown if "Sort by category" is selected or a category is already selected
    categoryDropdownContainer.style.display = (sortOption === "C" || (selectedCategory !== "" && selectedCategory !== "None")) ? "block" : "none";

    // Show supplier dropdown if "Sort by supplier" is selected or a supplier is already selected
    supplierDropdownContainer.style.display = (sortOption === "D" || (selectedSupplier !== "" && selectedSupplier !== "None")) ? "block" : "none";

    // Show last_edit dropdown if "Sort by last_edit" is selected or a last_edit is already selected
    lastEditDropdownContainer.style.display = (sortOption === "A" || (selectedLastEdit !== "" && selectedLastEdit !== "None")) ? "block" : "none";
});

// Add an event listener to dynamically handle sorting option change
document.getElementById("sort-option").addEventListener("change", function() {
    var sortOption = this.value; // Get the selected sort option
    var categoryDropdownContainer = document.getElementById("category-dropdown-container");
    var supplierDropdownContainer = document.getElementById("supplier-dropdown-container");
    var lastEditDropdownContainer = document.getElementById("last_edit-dropdown-container");
    var location1DropdownContainer = document.getElementById("location1-dropdown-container");
    var location2DropdownContainer = document.getElementById("location2-dropdown-container");
    var location3DropdownContainer = document.getElementById("location3-dropdown-container");
    var location4DropdownContainer = document.getElementById("location4-dropdown-container");

    // Show location1-4 dropdown if "Sort by location" is selected or a location is selected
    location1DropdownContainer.style.display = (sortOption === "B" || (window.APP_CONFIG.selectedLocation1 !== "" && window.APP_CONFIG.selectedLocation1 !== "None")) ? "block" : "none";
    location2DropdownContainer.style.display = (sortOption === "B" || (window.APP_CONFIG.selectedLocation2 !== "" && window.APP_CONFIG.selectedLocation2 !== "None")) ? "block" : "none";
    location3DropdownContainer.style.display = (sortOption === "B" || (window.APP_CONFIG.selectedLocation3 !== "" && window.APP_CONFIG.selectedLocation3 !== "None")) ? "block" : "none";
    location4DropdownContainer.style.display = (sortOption === "B" || (window.APP_CONFIG.selectedLocation4 !== "" && window.APP_CONFIG.selectedLocation4 !== "None")) ? "block" : "none";

    // Show category dropdown if "Sort by category" is selected or a category is selected
    categoryDropdownContainer.style.display = (sortOption === "C" || (window.APP_CONFIG.selectedCategory !== "" && window.APP_CONFIG.selectedCategory !== "None")) ? "block" : "none";

    // Show supplier dropdown if "Sort by supplier" is selected or a supplier is selected
    supplierDropdownContainer.style.display = (sortOption === "D" || (window.APP_CONFIG.selectedSupplier !== "" && window.APP_CONFIG.selectedSupplier !== "None")) ? "block" : "none";

    // Show last edit dropdown if "Sort by last edit" is selected or a last edit is selected
    lastEditDropdownContainer.style.display = (sortOption === "A" || (window.APP_CONFIG.selectedLastEdit !== "" && window.APP_CONFIG.selectedLastEdit !== "None")) ? "block" : "none";
});

// Automatically submit the form when a category or supplier is selected
document.getElementById("category-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});
document.getElementById("supplier-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});
document.getElementById("last_edit-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});
document.getElementById("location1-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});
document.getElementById("location2-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});
document.getElementById("location3-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});
document.getElementById("location4-select").addEventListener("change", function() {
    this.form.submit();  // Automatically submit the form
});

/* =====================================================================
 * Block: getUrlParameter / isAnyLocationSelected / location -> location1-4
 * AJAX population / toggleLocationDropdowns + DOMContentLoaded bootstrap
 * ===================================================================== */

// Function to get a parameter from the URL
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);  // Returns the value of the specified parameter
}

// Function to check if any of the location fields are not null or empty
function isAnyLocationSelected() {
    const location1 = getUrlParameter('location1');
    const location2 = getUrlParameter('location2');
    const location3 = getUrlParameter('location3');
    const location4 = getUrlParameter('location4');
    return location1 || location2 || location3 || location4;
}

// Event listener for 'location' change
document.querySelector('[name="location"]').addEventListener('change', function() {
    var location = this.value;

    // Make AJAX request to fetch filtered locations based on the selected location
    fetch(`/get_locations?location=${location}`)
        .then(response => response.json())
        .then(data => {
            // Update the location1, location2, location3, location4 dropdowns with the fetched data
            updateLocationDropdown('location1', data.locations1);
            updateLocationDropdown('location2', data.locations2);
            updateLocationDropdown('location3', data.locations3);
            updateLocationDropdown('location4', data.locations4);
        })
        .catch(error => console.error('Error fetching locations:', error));
});

// Function to update a dropdown with new options
function updateLocationDropdown(locationName, options) {
    var select = document.querySelector(`[name="${locationName}"]`);

    // Extract the number part of the location name (e.g., "1", "2", "3", "4")
    var locationNumber = locationName.replace('location', '');

    // Set the appropriate placeholder text based on the location number
    var placeholder = `-- Select Location ${locationNumber} --`;

    // Clear existing options and set dynamic placeholder
    select.innerHTML = `<option value="">${placeholder}</option>`;

    // Add new options to the dropdown
    options.forEach(function(option) {
        var optionElement = document.createElement('option');
        optionElement.textContent = option;
        select.appendChild(optionElement);
    });

    // Ensure the previously selected value is reselected
    var selectedLocation = getUrlParameter(locationName); // Get the location value from the URL
    if (selectedLocation) {
        select.value = selectedLocation;
    }
}

// Function to show/hide location dropdowns based on conditions
function toggleLocationDropdowns() {
    const sortOption = getUrlParameter('filter'); // Get 'sort' from URL
    const location1Dropdown = document.querySelector('[name="location1"]');
    const location2Dropdown = document.querySelector('[name="location2"]');
    const location3Dropdown = document.querySelector('[name="location3"]');
    const location4Dropdown = document.querySelector('[name="location4"]');

    // Print each variable to the console

    // Show location dropdowns if 'Sort by Location' is selected or if any location field is not null
    const showLocationDropdowns1 = sortOption === 'B' || (window.APP_CONFIG.selectedLocation1 !== "" && window.APP_CONFIG.selectedLocation1 !== "None");
    const showLocationDropdowns2 = sortOption === 'B' || (window.APP_CONFIG.selectedLocation2 !== "" && window.APP_CONFIG.selectedLocation2 !== "None");
    const showLocationDropdowns3 = sortOption === 'B' || (window.APP_CONFIG.selectedLocation3 !== "" && window.APP_CONFIG.selectedLocation3 !== "None");
    const showLocationDropdowns4 = sortOption === 'B' || (window.APP_CONFIG.selectedLocation4 !== "" && window.APP_CONFIG.selectedLocation4 !== "None");


    // Toggle visibility of the location dropdowns based on the conditions
    location1Dropdown.closest('div').style.display = showLocationDropdowns1 ? 'block' : 'none';
    location2Dropdown.closest('div').style.display = showLocationDropdowns2 ? 'block' : 'none';
    location3Dropdown.closest('div').style.display = showLocationDropdowns3 ? 'block' : 'none';
    location4Dropdown.closest('div').style.display = showLocationDropdowns4 ? 'block' : 'none';
}

// Automatically trigger the location change logic when the page loads, based on the current URL
document.addEventListener('DOMContentLoaded', function() {
    var locationFromUrl = getUrlParameter('location'); // Get 'location' from URL

    // If a location is set in the URL, trigger the change event manually
    if (locationFromUrl) {
        // Set the location dropdown value
        var locationDropdown = document.querySelector('[name="location"]');
        locationDropdown.value = locationFromUrl;

        // Trigger the change event to fetch and update the location dropdowns
        var event = new Event('change');
        locationDropdown.dispatchEvent(event);
    }

    // Toggle the location dropdowns based on the sort and location fields
    toggleLocationDropdowns();
});

/* =====================================================================
 * Block: "Apply filter" / "clear all filters" default-option text,
 * and reset-all-filters-on-default-selected wiring.
 *
 * NOTE: also depends on the non-existent #sort-option element and will
 * throw, exactly as in the original inline script. Kept verbatim.
 * ===================================================================== */
window.addEventListener('load', function() {
    var sortOption = document.getElementById("sort-option").value; // Get the selected sort option from the server
    var defaultOption = document.getElementById("sort-option").options[0]; // Get the first option (the default one)

    // Change the default dropdown option text based on the selected value
    if (sortOption === "") {
        defaultOption.text = "Apply filter"; // No filter selected
    } else {
        defaultOption.text = "clear all filters"; // Filter applied
    }
});

document.getElementById("sort-option").addEventListener("change", function() {
    var sortOption = this.value; // Get the selected sort option
    var form = this.form; // Reference to the form
    var defaultOption = this.options[0]; // Get the first option (the default one)

    if (sortOption === "") {
        // Reset to the default text if no filter is selected
        defaultOption.text = "Apply filter";

        // Reset all filters if the default option is selected
        document.getElementById("category-select").value = "";
        document.getElementById("supplier-select").value = "";
        document.getElementById("last_edit-select").value = "";
        document.getElementById("location1-select").value = "";
        document.getElementById("location2-select").value = "";
        document.getElementById("location3-select").value = "";
        document.getElementById("location4-select").value = "";

        // Automatically submit the form to reset all filters
        form.submit();
    } else {
        // Change to "Clear Filters" when something else is selected
        defaultOption.text = "clear all filters";
    }
});

/* =====================================================================
 * Block: table header min-width sizing
 * ===================================================================== */

// Function to set the minimum width for the headers based on content
function adjustTableHeaders() {
    var headers = document.querySelectorAll('th');

    headers.forEach(function(header) {
        // Set a minimum width based on the header's text content
        var headerText = header.innerText || header.textContent;
        var minWidth = headerText.length * 10; // Rough estimate for width
        header.style.minWidth = minWidth + 'px';
    });
}

// Call the function on page load
window.onload = adjustTableHeaders;

/* =====================================================================
 * Block: scroll position persistence across navigations (URL hash)
 * ===================================================================== */

// Function to restore scroll position from the URL
function restoreScrollPosition() {
    const hash = window.location.hash;

    // Check if the hash contains 'scroll=' and extract the value
    if (hash && hash.startsWith('#scroll=')) {
        const scrollPos = parseInt(hash.split('scroll=')[1], 10);

        if (!isNaN(scrollPos)) {
            // Scroll to the position specified in the URL hash
            window.scrollTo(0, scrollPos);
        }
    }
}

// Function to update the scroll position in the URL as you scroll
function updateScrollPosition() {
    const scrollPosition = window.scrollY;

    // Update the URL with the current scroll position
    // We use pushState so that it doesn't reload the page
    history.replaceState(null, null, `#scroll=${scrollPosition}`);
}

// Update scroll position in URL when scrolling
window.addEventListener('scroll', updateScrollPosition);

// Call restoreScrollPosition when the page is loaded or hash is changed
window.addEventListener('load', restoreScrollPosition);
window.addEventListener('hashchange', restoreScrollPosition);

/* =====================================================================
 * Block: search autocomplete (jQuery + /autocomplete endpoint)
 * ===================================================================== */
$(document).ready(function() {
    // Bind to the input event on the search bar
    $('#search').on('input', function() {
        var query = $(this).val();  // Get the value entered by the user

        // If query is not empty, make an AJAX request for autocomplete suggestions
        if (query.length > 1) {
            $.get('/autocomplete', { query: query }, function(data) {
                var suggestions = data.suggestions;  // The returned suggestions
                $('#autocomplete-suggestions').empty();  // Clear previous suggestions

                // Remove duplicate suggestions by converting array to a Set and back to an array
                suggestions = [...new Set(suggestions)];

                // If there are suggestions, display them
                if (suggestions.length > 0) {
                    suggestions.forEach(function(suggestion) {
                        $('#autocomplete-suggestions').append('<div class="suggestion-item">' + suggestion + '</div>');
                    });
                } else {
                    $('#autocomplete-suggestions').append('<div>No suggestions found</div>');
                }
            }).fail(function() {
                // If the request fails
                console.error("Autocomplete request failed");
            });
        } else {
            $('#autocomplete-suggestions').empty();  // Clear suggestions if the input is empty
        }
    });

    // Highlight suggestion on hover
    $(document).on('mouseenter', '.suggestion-item', function() {
        $(this).addClass('highlighted');

        // Fill the search box with the hovered suggestion
        $('#search').val($(this).text());

    }).on('mouseleave', '.suggestion-item', function() {
        $(this).removeClass('highlighted');
    });

    // When a suggestion is clicked, set it in the input field and clear the suggestions
    $(document).on('click', '.suggestion-item', function() {
        var suggestion = $(this).text();
        $('#search').val(suggestion);
        $('#autocomplete-suggestions').empty();  // Clear suggestions

        // Trigger the form submission
        //$('form').submit();  // This submits the form
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search');
    const suggestionsBox = document.getElementById('autocomplete-suggestions');

    function updateBoxVisibility() {
        const isFocused = document.activeElement === searchInput;
        const hasText = searchInput.value.trim() !== '';

        if (isFocused && hasText) {
            suggestionsBox.style.display = 'block';
            suggestionsBox.style.width = `${searchInput.offsetWidth}px`;
            suggestionsBox.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.1)';
        } else {
            suggestionsBox.style.display = 'none';
        }
    }

    searchInput.addEventListener('input', updateBoxVisibility);
    searchInput.addEventListener('focus', updateBoxVisibility);
    searchInput.addEventListener('blur', function () {
        setTimeout(updateBoxVisibility, 150); // delay to allow suggestion click
    });
});

/* =====================================================================
 * Block: flash message auto-dismiss
 * ===================================================================== */
window.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll('[data-flash]');
    flashMessages.forEach((el) => {
        setTimeout(() => {
            el.classList.remove("show");
            el.classList.add("fade");
            setTimeout(() => el.remove(), 500); // optional cleanup
        }, 3000);
    });
});
