// From https://www.w3schools.com/js/js_cookies.asp
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function performAjaxPOST(url, data, callback, failureCallback){
/*
    Function to abstract away AJAX calls, somewhat reducing the volume of code to be drudging through
*/
    $j.ajax({
        type:"POST",
        url: url,
        data: data,
        dataType: 'json',
        headers: { 'X-CSRFToken': $j('input[name="csrfmiddlewaretoken"]').val() }, 
        success: callback,
        error: failureCallback
    });
}

function performAjaxGET(url, callback, failureCallback){
/*
    Function to abstract away AJAX calls, somewhat reducing the volume of code to be drudging through
*/
    $j.ajax({
        type:"GET",
        url: url,
        // data: data,
        dataType: 'json',
        headers: { 'X-CSRFToken': $j('input[name="csrfmiddlewaretoken"]').val() }, 
        success: callback,
        error: failureCallback
    });
}


function escapeChars(inString){
/*
    Function to strip away single and double quotes. Without this, unfortunate things like everything
    after the single quote being added as an attribute of the rendered idea outside of intended 'value' attribute
*/
    inString = inString.replace(/'/g, "&apos;")
                            .replace(/"/g, "&quot;");
    return inString;
}
