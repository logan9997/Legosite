
function maintain_scroll_pos(elememt_id) {
    var elem = document.getElementById(elememt_id)
    document.addEventListener("DOMContentLoaded", function(event) { 
        var elem_scroll_pos = localStorage.getItem('elem_scroll_pos');
        if (elem_scroll_pos) elem.scrollTo(0, elem_scroll_pos);
    });

    window.onbeforeunload = function(e) {
        localStorage.setItem('elem_scroll_pos', elem.scrollTop);
    };
}

function hide_unhide(elem_id) {
    var elem_style = document.getElementById(elem_id).style.display
    var button = document.getElementById('collapse-filters-button')

    if (elem_style == "block") {
        document.getElementById(elem_id).style.display = "none"
        button.innerHTML = "Show Filters"
    } else {
        document.getElementById(elem_id).style.display = "block"
        button.innerHTML = "Hide Filters"
    }
    localStorage.setItem('filters_display', document.getElementById(elem_id).style.display);
}


function dict_item_to_list(dict_key, list) {
    var items = []
    for (let i = 0; i < list.length; i ++) {
        items.push(list[i][dict_key])
    }
    return items
}


function search_suggestions(input) {
    var item_details = JSON.parse(document.getElementById("item_details").textContent);

    var item_names = dict_item_to_list("item_name", item_details)
    var item_ids = dict_item_to_list("item_id", item_details)
    var item_types = dict_item_to_list("item_type", item_details)

    var input = document.getElementById("item-id-input").value.toLowerCase();
    const max_search_suggestions = JSON.parse(document.getElementById("max_search_suggestions").textContent)
    const main_container = document.getElementById("search-logout-suggestions-container")
    
    var suggestion_boxes = document.getElementsByClassName("search-suggestion");

    for (let i = suggestion_boxes.length - 1; i >= 0; i --) {
        suggestion_boxes[i].remove()
    }

    //create container when search box is active
    if (document.getElementById("search-suggestions") == null) {
        main_suggestions = document.createElement("div")
        main_suggestions.setAttribute("id", "search-suggestions")
        main_suggestions.style.display = "flex"
        main_container.appendChild(main_suggestions)
    }

    var suggestion_boxes_container = document.getElementById("search-suggestions");

    var matches = 0;
    for (let i = 0; i < item_ids.length; i ++) {
        if ((item_ids[i].slice(0,input.length) == input || item_names[i].includes(input)) && input != "") {

            name_part1 = item_names[i].split(input)[0]
            name_part2 = item_names[i].split(input)[1]

            //create each box for every item
            html_block = document.createElement("a");
            html_block.setAttribute("href", `/item/${item_ids[i]}`)
            html_block.setAttribute("class", "search-suggestion")
            html_block.innerHTML = `
                    <div class="item-id-img-container">
                        <a href="/item/${item_ids[i]}" onclick="clear_search_suggestions()" class="item-id">${item_ids[i].replaceAll(input, `<span style="color:black">${input}</span>`)}</a>
                        <img class="item-img" src="/static/App/${item_types[i]}s/${item_ids[i]}.png">
                    </div>
                    <div class="item-name-contianer">
                        <p class="item-name">${item_names[i].replaceAll(input, `<span style="color:black">${input}</span>`)}</p>
                    </div>
            `
            suggestion_boxes_container.appendChild(html_block)
            matches += 1;
            if (matches == max_search_suggestions) {
                break;
            }
        }
    }
    const suggestion_box_height = 6.15;
    var container_height = matches * suggestion_box_height
    if (container_height > 6 * suggestion_box_height) {
        container_height = 6 * suggestion_box_height
    }
    suggestion_boxes_container.style.height = `${container_height}rem`
    
    //remove container
    if (matches == 0) {
        document.getElementById("search-suggestions").remove()
    }
}


function logout_popup(e) {
    if (confirm("Logging out? Are you sure?")) {
        window.location.reload()
    } else {
        e.preventDefault()
    }
}


function show_dropdown_content() {
    var element_style = document.getElementById("dropdown-content").style.display;
    console.log(element_style)
    if (element_style == "flex") {
        document.getElementById("dropdown-content").style.display = "none";
    } else {
        document.getElementById("dropdown-content").style.display = "flex";
    }
}


function reveal_sub_themes(theme_path) {
    if (theme_path.style.display == "none") {
        theme_path.style.display = "block";
    } else {
        theme_path.style.display = "none";  
    }
}

function update_add_portfolio_text() {
    var button = document.getElementById("portfolio-button")
    var value = document.getElementById("quantity-input").value

    if (value < 0) {
        button.innerHTML = "Remove from Portfolio!"
        console.log("less")
    } else {
        button.innerHTML = "Add to Portfolio!"
        console.log("more")
    }
}

//https://www.scaler.com/topics/date-validation-in-javascript/
function isValidDate(date) {
 
    // Date format: YYYY-MM-DD
    var datePattern = /^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))/;

    // Check if the date string format is a match
    var matchArray = date.match(datePattern);
    if (matchArray == null) {
        return false;
    }

    // Remove any non digit characters
    var dateString = date.replace(/\D/g, ''); 

    // Parse integer values from the date string
    var year = parseInt(dateString.substr(0, 4));
    var month = parseInt(dateString.substr(4, 2));
    var day = parseInt(dateString.substr(6, 2));
   
    // Define the number of days per month
    var daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    // Leap years
    if (year % 400 == 0 || (year % 100 != 0 && year % 4 == 0)) {
        daysInMonth[1] = 29;
    }

    if (month < 1 || month > 12 || day < 1 || day > daysInMonth[month - 1]) {
        return false;
    }
    return true;
}


function input_validation(input, type, add_new) {
    var form = input.parentElement.parentElement.parentElement

    var inputs = form.getElementsByTagName("input")
    var new_inputs = []
    for (let i = 0; i<inputs.length; i++) {
        if (inputs[i].type != "hidden") {
            new_inputs.push(inputs[i])
        }
    }
    inputs = new_inputs
    
    var msg = ""
    if (type == "date") {
        if (! isValidDate(input.value) || input.value.length != 10) {
            msg = "invalid date format. (YYYY-MM-DD)"
        }
    } else {
        if (isNaN(input.value)) {
            msg = "invalid number (0.00)"
        } 
        if (input.value < 0) {
            msg = "number must be >= 0"
        }
    }

    if (msg != "") {
        form.parentElement.getElementsByClassName("error-msg-container")[0].style.display = "block";
        form.parentElement.getElementsByClassName("error-msg")[0].innerHTML = msg;

        var watchlist_button = document.getElementById("add-to-watchlist")
        if (watchlist_button != null) {
            watchlist_button.style.marginTop = "1.5rem"
        }
        // form.parentElement.getElementsByClassName("entry-counter")[0].style.borderTop = "none";
    } else {
        form.parentElement.getElementsByClassName("error-msg-container")[0].style.display = "none"
        form.parentElement.getElementsByClassName("error-msg")[0].innerHTML = ""
    }

    var valid = true
    for (let i = 0; i<inputs.length; i++) {
        if (i % 2 == 0) {
            if (! isValidDate(inputs[i].value) && inputs[i].value != "" && inputs[i].value.length != 10) {
                valid = false
                console.log(inputs[i].value, "IN-VALID")
            }
        } else {            
            if (isNaN(inputs[i].value) || parseFloat(inputs[i].value) < 0) {
                valid = false
                console.log(inputs[i].value, "IN-VALID")
            } 
        }
    }

    for (let i = 0; i<inputs.length; i ++) {
        console.log(inputs[i].value)
    }

    var submit_button = document.getElementById("submit")

    console.log(add_new, valid)

    if (valid) {
        if (add_new) {
            submit_button.disabled = false
        } else {
            form.submit()
        } 
    } else {
        if (add_new) {
            input.value = ""
        }
    }
}

function condence_list(_list) {
    const max_graph_points = JSON.parse(document.getElementById("max_graph_points").textContent);
    if (_list.length > max_graph_points) {
        var first = _list[0]; 
        var last = _list[_list.length-1]

        var remove_gap = Math.ceil(_list.length / max_graph_points);

        var condenced_list = [];
        for (let i = 0; i <= _list.length; i += remove_gap) {
            if (i != _list.length) {
                condenced_list.push(_list[i])
            }
        }
        condenced_list[0] = first;
        condenced_list[condenced_list.length-1] = last;
        return condenced_list
    }
    return _list
    
}