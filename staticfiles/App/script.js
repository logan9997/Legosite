window.onload = function() {
    document.addEventListener("DOMContentLoaded", function(event) { 
        var scrollpos = localStorage.getItem('scrollpos');
        if (scrollpos) window.scrollTo(0, scrollpos);
    });

    window.onbeforeunload = function(e) {
        localStorage.setItem('scrollpos', window.scrollY);
    };
}

function display_item_delete_quantity() {
    form = document.getElementsByClassName("")
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


