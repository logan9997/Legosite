
function maintain_scroll_pos(elememt_id) {
    var elem = document.getElementById(elememt_id)
    window.onload = function() { 
        var elem_scroll_pos = localStorage.getItem('elem_scroll_pos');
        elem.scrollTo(0, elem_scroll_pos);
    }

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
                        <a href="/item/${item_ids[i]}" onclick="clear_search_suggestions()" 
                        class="item-id">${item_ids[i].replaceAll(input, `<span style="color:black">${input}</span>`)}</a>
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
    } else {
        button.innerHTML = "Add to Portfolio!"
    }
}

//https://www.scaler.com/topics/date-validation-in-javascript/
function isValidDate(date) {
 
    if (date.length > 10) {
        return false;
    }

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


function input_validation(input, add_new) {
    var form = input.parentElement.parentElement.parentElement
    var inputs = form.getElementsByTagName('input')

    var new_inputs = []
    for (let i = 0; i<inputs.length; i++) {
        if (inputs[i].type != "hidden") {
            new_inputs.push(inputs[i])
        }
    }
    inputs = new_inputs

    var submit_button = document.getElementById("submit")
    var error_msg_container = form.parentElement.getElementsByClassName("error-msg-container")[0]
    var error_msg = form.parentElement.getElementsByClassName("error-msg")[0]

    //check all inputs
    var msg = ''
    for (let i = 0; i < inputs.length; i ++) {
        let value = inputs[i].value
        if (i % 2 == 0 && value != '') {
            //dates
            if (! isValidDate(value)) {
                msg = 'Invalid date (YYYY-MM-DD)'
                break
            }
        }  
        if (i % 2 != 0 && value != 0) {
            //prices
            if (isNaN(value)) {
                msg = 'Invalid number format (0.00)'
                break
            } 
            if (parseFloat(value) < 0) {
                msg = 'Number must be > 0.00'
                break
            } 
        }
    }

    console.log('msg', msg)

    //update error message
    if (msg != '') {
        error_msg_container.style.display = 'block'
        error_msg.innerHTML = msg
        if (! window.location.href.includes('portfolio')) {
            document.getElementById('add-to-watchlist').style.marginTop = '1.5rem'
        }
    } else {
        error_msg_container.style.display = 'none'
        error_msg.innerHTML = ''
        if (! window.location.href.includes('portfolio')) {
            document.getElementById('add-to-watchlist').style.marginTop = '14.5rem'
        }
    }

    var valid = true
    if (msg != '') {
        valid = false
    }


    if (add_new) {
        if (! valid) {
            submit_button.disabled = true
        } else {
            submit_button.disabled = false
        }
    } else {
        if (valid) {
            input.addEventListener('blur', function() {form.submit()})
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